# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Class that provides multiple getters on resource tables.
"""
from pyvo.mivot.utils.constant import Constant
from pyvo.utils.prototype import prototype_feature


@prototype_feature('MIVOT')
class ResourceSeeker(object):
    """
    This class provides multiple getters on resource tables.
    """

    def __init__(self, resource):
        """
        Constructor

        Parameters
        ----------
        resource : ~pyvo.dal.query.Resource
            The resource object to be queried.
        """
        self._resource = resource

    def get_table_ids(self):
        """
        Returns the list of table ids.
        Only child resources are considered.
        The id is first looked up in ID then in name, and finally 'AnonymousTable' is taken.

        Returns
        -------
        list of str
            List of table ids.
        """
        retour = []
        for table in self._resource.tables:
            if table.ID is not None:
                retour.append(table.ID)
            elif table.name is not None:
                retour.append(table.name)
            else:
                retour.append('AnonymousTable')
        return retour

    def get_table(self, table_name):
        """
        Returns the table matching table_name first by ID and then by name.

        Parameters
        ----------
        table_name : str
            Name of the table to get.

        Returns
        -------
        ~pyvo.dal.query.DALResults
            The table matching the given name.
        """
        if table_name == Constant.FIRST_TABLE:
            return self._resource.tables[0]
        for table in self._resource.tables:
            if (table_name is None or table.name == table_name
                    or table.ID == table_name):
                return table
        return None

    def get_params(self):
        """
        Returns the VOTable PARAMS.

        Returns
        -------
        ~pyvo.dal.query.DALResults
            The VOTable PARAMS.
        """
        return self._resource.params

    def get_id_index_mapping(self, table_name):
        """
        Build an index binding column number with field id.

        Parameters
        ----------
        table_name : str
            Name of the table.

        Returns
        -------
        dict
            A dictionary mapping field id to column number.
        """
        retour = {}
        table = self.get_table(table_name)
        indx = 0
        for field in table.fields:
            if field.ID is not None:
                retour[field.ID] = indx
            elif field.name is not None:
                retour[field.name] = indx
            elif field.ref is not None:
                retour[field.ref] = indx
            indx += 1
        return retour

    def get_id_unit_mapping(self, table_name):
        """
        Build an index binding field unit with field id.

        Parameters
        ----------
        table_name : str
            Name of the table.

        Returns
        -------
        dict
            A dictionary mapping field id to field unit.
        """
        retour = {}
        table = self.get_table(table_name)
        for field in table.fields:
            unit = field.unit
            if field.ID is not None:
                retour[field.ID] = unit
            elif field.name is not None:
                retour[field.name] = unit
            elif field.ref is not None:
                retour[field.ref] = unit
        return retour
