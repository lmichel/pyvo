"""
Created on 5 Jan 2022

@author: laurentmichel
"""
from copy import deepcopy

from astropy.io.votable import parse
from lxml import etree

from pyvo.mivot import logger
from pyvo.mivot.utils.vocabulary import Ele, Att
from pyvo.mivot.utils.constant import Constant
from pyvo.mivot.utils.exceptions import *
from pyvo.mivot.utils.xml_utils import XmlUtils
from pyvo.mivot.seekers.annotation_seeker import AnnotationSeeker
from pyvo.mivot.seekers.resource_seeker import ResourceSeeker
from pyvo.mivot.seekers.table_iterator import TableIterator
from pyvo.mivot.features.static_reference_resolver import StaticReferenceResolver
from pyvo.mivot.viewer.model_viewer_layer1 import ModelViewerLayer1
from pyvo.mivot.viewer.model_viewer_layer3 import ModelViewerLayer3
from pyvo.utils.prototype import prototype_feature


@prototype_feature('MIVOT')
class ModelViewer(object):
    """
    ModelViewer is a PyVO table wrapper aiming at providing a model view on VOTable data read with usual tools.

    Standard usage applied to data rows:
    .. code-block:: python
        data_path = os.path.dirname(os.path.realpath(__file__))
        votable = os.path.join(data_path,"any_votable.xml")
        m_viewer = ModelViewer(votable)
        row_view = m_viewer.get_next_row_view()
    """

    def __init__(self, votable_path, tableref=None, resource_number=None):
        """
        Constructor
        :param votable_path: VOTable that we will parse with the parser of Astropy, which extract the annotation block.
        :param tableref: Used to identify the table to process, if not specified, the first table is taken by default.
        :param resource_number: The number corresponding to the resource containing the MIVOT block (first by default).
        """
        self._parsed_votable = parse(votable_path)
        self._table_iterator = None
        self._connected_table = None
        self._connected_tableref = None
        self._current_data_row = None
        # when the search object is in GLOBALS
        self._globals_instance = None
        self._last_row = None
        self._templates = None
        self._resource = None

        self._annotation_seeker = None
        self._mapping_block = None
        self._mapped_tables = None

        self._set_resource(resource_number)
        self._set_mapping_block()
        self._resource_seeker = ResourceSeeker(self._resource)
        self._set_mapped_tables()
        self.connect_table(tableref)

    """
    Properties
    """

    @property
    def annotation_seeker(self):
        """
        Returns an API to search various components in the XML mapping block.
        """
        return self._annotation_seeker

    @property
    def resource_seeker(self):
        """
        Returns an API to search various components in the VOTabel resource.
        """
        return self._resource_seeker

    @property
    def connected_table(self):
        return self._connected_table

    @property
    def connected_table_ref(self):
        return self._connected_tableref

    @property
    def current_data_row(self):
        self._assert_table_is_connected()
        return self._current_data_row

    """
    Global accessors
    """

    def get_table_ids(self):
        """
        Returns a list of the table located just below self._resource.
        """
        return self.resource_seeker.get_table_ids()

    def get_globals_models(self):
        """
        Collection types are GLOBALS/COLLECTION/INSTANCE@dmtype: used for collections of static objects.
        :return : The dmtypes of all the top level INSTANCE/COLLECTION of GLOBALS.
        :rtype:  {'COLLECTION': [dmtypes], 'INSTANCE': [dmtypes]}
        """
        retour = {}
        retour[Ele.COLLECTION] = self._annotation_seeker.get_globals_collection_dmtypes()
        retour[Ele.INSTANCE] = self._annotation_seeker.get_globals_instance_dmtypes()

        return retour

    def get_models(self):
        """
        :return: dictionary of the models and theirs urls
        :rtype: {'model': [url], ...}
        """
        retour = self._annotation_seeker.models
        return retour

    def get_templates_models(self):
        """
        COLLECTION not implemented yet
        :return : The dmtypes (except ivoa:*) of all INSTANCE/COLLECTION of all TEMPLATES
        :rtype:  {'tableref: {'COLLECTIONS': [dmtypes], 'INSTANCE': [dmtypes]}, ...}
        """
        retour = {}
        gni = self._annotation_seeker.get_instance_dmtypes()[Ele.TEMPLATES]
        for tid, tmplids in gni.items():
            retour[tid] = {Ele.COLLECTION: [], Ele.INSTANCE: tmplids}

        return retour

    """
    Data browsing
    """

    def connect_table(self, tableref=None):
        """
        Iterate over the table identified by tableref
        Required to browse table data.
        Connect to the first table if tableref is None.
        :param tableref: Identifier of the table.
        """
        if tableref is None:
            self._connected_tableref = Constant.FIRST_TABLE
            logger.debug("Since "+Ele.TEMPLATES+" table_ref '%s' is None, it will be set as 'first_table' by default",
                         tableref)

        elif tableref not in self._mapped_tables:
            raise MappingException(f"The table {self._connected_tableref} doesn't match with any "
                                   f"mapped_table ({self._mapped_tables}) encountered in "+Ele.TEMPLATES)
        else:
            self._connected_tableref = tableref

        self._connected_table = self._resource_seeker.get_table(tableref)
        if self.connected_table is None:
            raise ResourceNotFound("Cannot find table {} in VOTable".format(tableref))
        logger.debug("table %s found in VOTable", tableref)

        self._templates = deepcopy(self.annotation_seeker.get_templates_block(tableref))
        if self._templates is None:
            raise MivotElementNotFound("Cannot find "+Ele.TEMPLATES+f" {tableref} ")
        logger.debug(Ele.TEMPLATES+" %s found ", tableref)

        self._table_iterator = TableIterator(self._connected_tableref, self.connected_table.to_table())
        self._squash_join_and_references()
        self._set_column_indices()
        self._set_column_units()

    def get_next_row(self):
        """
        Returns the next data row of the connected table.
        :return: Next data row
        :rtype: ~`astropy.table.row.Row`
        """
        self._assert_table_is_connected()
        self._current_data_row = self._table_iterator._get_next_row()
        return self._current_data_row

    def rewind(self):
        """
        Rewinds the table iterator of the connected table
        """
        self._assert_table_is_connected()
        self._table_iterator._rewind()

    """
    Private methods
    """
    def _get_model_view(self, resolve_ref=True):
        """
        Returns an XML model view of the last read row.
        This function resolves references by default. It is called in the ModelViewerLayer1.
        :param resolve_ref: Boolean, if True, resolves the references.
        """
        templates_copy = deepcopy(self._templates)
        if resolve_ref is True:
            while StaticReferenceResolver.resolve(self._annotation_seeker, self._connected_tableref,
                                                  templates_copy) > 0:
                pass
            # Make sure the instances of the resolved references have both indexes and unit attribute
            XmlUtils.set_column_indices(templates_copy,
                                        self._resource_seeker.get_id_index_mapping(self._connected_tableref))
            XmlUtils.set_column_units(templates_copy,
                                      self._resource_seeker.get_id_unit_mapping(self._connected_tableref))

        for ele in templates_copy.xpath("//ATTRIBUTE"):
            ref = ele.get(Att.ref)
            if ref is not None and ref != Constant.NOT_SET:
                index = ele.attrib[Constant.COL_INDEX]
                ele.attrib[Att.value] = str(self._current_data_row[int(index)])

        return templates_copy

    def get_first_instance(self, tableref=None):
        """
        Returns the head of INSTANCE, the first child of TEMPLATES.
        If no INSTANCE is found, take the first COLLECTION.
        :param tableref: Identifier of the table.
        :return: The first child of TEMPLATES
        :rtype: `~lxml.etree._Element`
        """
        child = self._annotation_seeker.get_templates_block(tableref).getchildren()
        collection = self._annotation_seeker.get_templates_block(tableref).xpath(Ele.COLLECTION)
        instance = self._annotation_seeker.get_templates_block(tableref).xpath(Ele.INSTANCE)

        if len(collection) >= 1:
            collection[0].set(Att.dmtype, Constant.ROOT_COLLECTION)
            (self._annotation_seeker.get_templates_block(tableref).find(Ele.COLLECTION)
             .set(Att.dmtype, Constant.ROOT_COLLECTION))

        if len(child) > 1:
            if len(instance) >= 1:
                for inst in instance:
                    if inst in child:
                        return inst.get(Att.dmtype)
            elif len(collection) >= 1:
                for coll in collection:
                    if coll in child:
                        return coll.get(Att.dmtype)
        elif len(child) == 1:
            if child[0] in instance:
                return child[0].get(Att.dmtype)
            elif child[0] in collection:
                return collection[0].get(Att.dmtype)
        else:
            raise MivotElementNotFound("Can't find the first "+Ele.INSTANCE+"/"+Ele.COLLECTION+" in "+Ele.TEMPLATES)

    def get_model_view_layer1(self):
        """
        Private methods that builds and returns a new layer on our model viewer which contains various XML getters.
        """
        return ModelViewerLayer1(self)

    def get_next_row_view(self):
        """
        Private methods that builds and returns a new layer on our model viewer which consists in creating
        an object that contains all INSTANCEs and ATTRIBUTEs as a dictionary.
        :return: `~pyvo.mivot.viewer.mivot_class.MivotClass` object of the next data row
        :rtype: `~pyvo.mivot.viewer.mivot_class.MivotClass`
        """
        self.get_next_row()
        if self._current_data_row is None:
            return None
        else:
            mv_niv1 = self.get_model_view_layer1()
            instance = mv_niv1.get_instance_by_type(self.get_first_instance())
            m_viewer3 = ModelViewerLayer3(instance)

            m_viewer3.show_class_dict()
            return m_viewer3.mivot_class

    def _assert_table_is_connected(self):
        assert self._connected_table is not None, "Operation failed: no connected data table"

    def _set_mapped_tables(self):
        """
        Set the mapped tables with a list of the TEMPLATES tablerefs
        """
        self._mapped_tables = self._annotation_seeker.templates

    def _set_resource(self, resource_number):
        """
        Take the resource_number in entry and then set the resource concerned,
        if the resource_number if None, the resource set by default is the first one.
        """
        nb_resources = len(self._parsed_votable.resources)
        if resource_number is None:
            rnb = 0
        else:
            rnb = resource_number

        if rnb < 0 or rnb >= nb_resources:
            raise ResourceNotFound(f"Resource #{rnb} is not found")
        else:
            logger.info("Resource %s selected", rnb)
            self._resource = self._parsed_votable.resources[rnb]

    def _set_mapping_block(self):
        """
        Set the mapping block found in the resource and set the annotation_seeker
        """
        if self._resource.mivot_block.content == ('<VODML xmlns="http://www.ivoa.net/xml/mivot">\n  '
                                                  '<REPORT status="KO">No Mivot block</REPORT>\n</VODML>\n'):
            raise MivotNotFound("Mivot block is not found")

        # The namespace should be removed
        self._mapping_block = etree.fromstring(self._resource.mivot_block.content
                                               .replace('xmlns="http://www.ivoa.net/xml/mivot"', '')
                                               .replace("xmlns='http://www.ivoa.net/xml/mivot'", ''))

        self._annotation_seeker = AnnotationSeeker(self._mapping_block)
        logger.info("Mapping block found")

    def _squash_join_and_references(self):
        """
        Remove both JOINs and REFERENCEs from the templates and store them in to be resolved later on
        This prevents the model view of being polluted with elements that are not in the model
        """
        for ele in self._templates.xpath("//*[starts-with(name(), 'REFERENCE_')]"):
            if ele.get("sourceref") is not None:
                self._dyn_references = {ele.tag: deepcopy(ele)}
                for child in list(ele):
                    ele.remove(child)

        for ele in self._templates.xpath("//*[starts-with(name(), 'JOIN')]"):
            self._joins = {ele.tag: deepcopy(ele)}
            for child in list(ele):
                ele.remove(child)

    def _set_column_indices(self):
        """
        Add column ranks to attribute having a ref.
        Using ranks allow identifying columns even numpy raw have been serialised as []
        """
        index_map = self._resource_seeker.get_id_index_mapping(self._connected_tableref)
        XmlUtils.set_column_indices(self._templates, index_map)

    def _set_column_units(self):
        """
        Add field unit to attribute having a ref.
        Used for performing unit conversions
        """
        unit_map = self._resource_seeker.get_id_unit_mapping(self._connected_tableref)
        XmlUtils.set_column_units(self._templates, unit_map)
