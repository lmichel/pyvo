# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
MivotAnnotations: A utility module to build and manage MIVOT annotations.
"""
import os
import logging

try:
    import xmlschema
except ImportError:
    xmlschema = None
# Use defusedxml only if already present in order to avoid a new depency.
try:
    from defusedxml import ElementTree as etree
except ImportError:
    from xml.etree import ElementTree as etree
from astropy.io.votable.tree import VOTableFile, Resource
try:
    from astropy.io.votable.tree import MivotBlock
except ImportError:
    pass
from astropy.io.votable import parse
from astropy import version
from pyvo.utils.prototype import prototype_feature
from pyvo.mivot.utils.xml_utils import XmlUtils
from pyvo.mivot.utils.exceptions import MappingError, AstropyVersionException
from pyvo.mivot.writer.instance import MivotInstance
from pyvo.mivot.version_checker import check_astropy_version

__all__ = ["MivotAnnotations"]


@prototype_feature("MIVOT")
class MivotAnnotations:
    """
    This module provides a class to construct, validate, and insert MIVOT
    blocks into VOTable files.
    The MIVOT block, represented as an XML structure, is used for
    data model annotations in the IVOA ecosystem.

    The main features are:

    - Construct the MIVOT block step-by-step with various components.
    - Validate the MIVOT block against the MIVOT XML schema (if ``xmlschema`` is installed).
    - Embed the MIVOT block into an existing VOTable file.

    The MIVOT block is constructed as a string to maintain compatibility with the Astropy API.

    Attributes
    ----------
    _models : dict
        A dictionary containing models with their names as keys and URLs as values.
    _report_status : bool
        Indicates the success status of the annotation process.
    _report_message : str
        A message associated with the report, used in the REPORT block.
    _globals : list
        A list of GLOBALS blocks to be included in the MIVOT block.
    _templates : list
        A list of TEMPLATES blocks to be included in the MIVOT block.
    _templates_id : str
        An optional ID for the TEMPLATES block.
    _mivot_block : str
        The complete MIVOT block as a string.
    """

    def __init__(self):
        """
        """
        self._models = {}
        self._report_status = True
        self._report_message = "Generated by pyvo.mivot.writer"
        self._globals = []
        self._templates = []
        self._templates_id = ""
        self._mivot_block = ""

    @property
    def mivot_block(self):
        """
        Getter for the MIVOT block.

        Returns
        -------
        str
            Complete MIVOT block as a string.
        """
        return self._mivot_block

    def _get_report(self):
        """
        Generates the REPORT component of the MIVOT block.

        Returns
        -------
        str
            The REPORT block as a string, indicating the success or failure of the process.
        """
        if self._report_status:
            return f'<REPORT status="OK">{self._report_message}</REPORT>'
        else:
            return f'<REPORT status="FAILED">{self._report_message}</REPORT>'

    def _get_models(self):
        """
        Generates the MODEL components of the MIVOT block.

        Returns
        -------
        str
            The MODEL components as a formatted string.
        """
        models_block = ""
        for key, value in self._models.items():
            if value:
                models_block += f'<MODEL name="{key}" url="{value}" />\n'
            else:
                models_block += f'<MODEL name="{key}" />\n'

        return models_block

    def _get_globals(self):
        """
        Generates the GLOBALS component of the MIVOT block.

        Returns
        -------
        str
            The GLOBALS block as a formatted string.
        """
        globals_block = "<GLOBALS>\n"
        for glob in self._globals:
            globals_block += f"{glob}\n"
        globals_block += "</GLOBALS>\n"

        return globals_block

    def _get_templates(self):
        """
        Generates the TEMPLATES component of the MIVOT block.

        Returns
        -------
        str
            The TEMPLATES block as a formatted string, or an empty string if no templates are defined.
        """
        if not self._templates:
            return ""
        if not self._templates_id:
            templates_block = "<TEMPLATES>\n"
        else:
            templates_block = f'<TEMPLATES tableref="{self._templates_id}">\n'

        for templates in self._templates:
            templates_block += f"{templates}\n"
        templates_block += "</TEMPLATES>\n"
        return templates_block

    def build_mivot_block(self, *, templates_id=None):
        """
        Builds a complete MIVOT block from the declared components and validates it
        against the MIVOT XML schema.

        Parameters
        ----------
        templates_id : str, optional
            The ID to associate with the TEMPLATES block. Defaults to None.

        Raises
        ------
        Any exceptions raised during XML validation are not caught and must
        be handled by the caller.
        """
        if templates_id:
            self._templates_id = templates_id
        self._mivot_block = '<VODML xmlns="http://www.ivoa.net/xml/mivot">\n'
        self._mivot_block += self._get_report()
        self._mivot_block += "\n"
        self._mivot_block += self._get_models()
        self._mivot_block += "\n"
        self._mivot_block += self._get_globals()
        self._mivot_block += "\n"
        self._mivot_block += self._get_templates()
        self._mivot_block += "\n"
        self._mivot_block += "</VODML>\n"
        self._mivot_block = self.mivot_block.replace("\n\n", "\n")
        self.check_xml()

    def add_templates(self, templates_instance):
        """
        Adds an <INSTANCE> block to the <TEMPLATES> block.

        Parameters
        ----------
        templates_instance : str or MivotInstance
            The <INSTANCE> block to be added.

        Raises
        ------
        MappingError
            If ``templates_instance`` is neither a string nor an instance of `MivotInstance`.
        """
        if isinstance(templates_instance, MivotInstance):
            self._templates.append(templates_instance.xml_string())
        elif isinstance(templates_instance, str):
            self._templates.append(templates_instance)
        else:
            raise MappingError(
                "Instance added to templates must be a string or MivotInstance."
            )

    def add_globals(self, globals_instance):
        """
        Adds an <INSTANCE> block to the <GLOBALS> block.

        Parameters
        ----------
        globals_instance : str or MivotInstance
            The <INSTANCE> block to be added.

        Raises
        ------
        MappingError
            If ``globals_instance`` is neither a string nor an instance of `MivotInstance`.
        """
        if isinstance(globals_instance, MivotInstance):
            self._globals.append(globals_instance.xml_string())
        elif isinstance(globals_instance, str):
            self._globals.append(globals_instance)
        else:
            raise MappingError(
                "Instance added to globals must be a string or MivotInstance."
            )

    def add_model(self, model_name, model_url):
        """
        Adds a MODEL element to the MIVOT block.

        Parameters
        ----------
        model_name : str
            The short name of the model.
        model_url : str
            The URL of the VO-DML file associated with the model.
        """
        self._models[model_name] = model_url

    def set_report(self, status, message):
        """
        Sets the REPORT element of the MIVOT block.

        Parameters
        ----------
        status : bool
            The status of the annotation process. True for success, False for failure.
        message : str
            The message associated with the REPORT.

        Notes
        -----
        If ``status`` is False, all components of the MIVOT block except MODEL and REPORT
        are cleared.
        """
        self._report_status = status
        self._report_message = message
        if not status:
            self._globals = []
            self._templates = []

    def check_xml(self):
        """
        Validates the MIVOT block against the MIVOT XML schema v1.0.

        Raises
        ------
        MappingError
            If the validation fails.

        Notes
        -----
        The schema is loaded from a local file to avoid dependency on a remote service.
        """
        # put here just to improve the test coverage
        root = etree.fromstring(self._mivot_block)
        mivot_block = XmlUtils.pretty_string(root, clean_namespace=False)
        if not xmlschema:
            logging.error(
                "XML validation skipped: no XML schema found. "
                + "Please install it (e.g., pip install xmlschema)."
            )
            return

        schema = xmlschema.XMLSchema11(os.path.dirname(__file__) + "/mivot-v1.xsd")

        try:
            schema.validate(mivot_block)
        except Exception as excep:
            raise MappingError(f"Validation failed: {excep}") from excep

    def insert_into_votable(self, votable_file, override=False):
        """
        Inserts the MIVOT block into a VOTable.

        Parameters
        ----------
        votable_file : str or VOTableFile
            The VOTable to be annotated, either as a file path or a ``VOTableFile`` instance.
        override : bool
            If True, overrides any existing annotations in the VOTable.

        Raises
        ------
        MappingError
            If a mapping block already exists and ``override`` is False.
        """
        if not check_astropy_version():
            raise AstropyVersionException(f"Astropy version {version.version} "
                                          f"is below the required version 6.0 for the use of MIVOT.")
        if isinstance(votable_file, str):
            votable = parse(votable_file)
        elif isinstance(votable_file, VOTableFile):
            votable = votable_file
        else:
            raise MappingError(
                "votable_file must be a file path string or a VOTableFile instance."
            )

        for resource in votable.resources:
            if resource.type == "results":
                for subresource in resource.resources:
                    if subresource.type == "meta":
                        if not override:
                            raise MappingError(
                                "A type='meta' resource already exists in the first 'result' resource."
                            )
                        else:
                            logging.info("Overriding existing type='meta' resource.")
                        break
                mivot_resource = Resource()
                mivot_resource.type = "meta"
                mivot_resource.mivot_block = MivotBlock(self._mivot_block)
                resource.resources.append(mivot_resource)
