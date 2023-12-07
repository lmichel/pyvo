********************
MIVOT (`pyvo.mivot`)
********************
This module contains the new feature of annotations in VOTable.
Astropy version >= 6.0 is required.

Introduction
============
.. pull-quote::

    Model Instances in VOTables (MIVOT) defines a syntax to map VOTable
    data to any model serizalized in VO-DML. The annotation operates as a
    bridge between the data and the model. It associates the column/param
    metadata from the VOTable to the data model elements (class, attributes,
    types, etc.) [...].
    The data model elements are grouped in an independent annotation block
    complying with the MIVOT XML syntax. This annotation block is added
    as an extra resource element at the top of the VOTable result resource. The
    MIVOT syntax allows to describe a data structure as a hierarchy of classes.
    It is also able to represent relations and composition between them. It can
    also build up data model objects by aggregating instances from different
    tables of the VOTable.

    -- `Model Instances in VOTables <https://ivoa.net/documents/MIVOT/20230620/REC-mivot-1.0.pdf>`_


Usage
-----
The API allows you to obtain different levels of model views on the last read data row. These levels are described below.
The lowest levels are model agnostic. 

They provide tools to browse model instances dynamically generated. The understanding of the model elements is the responsability of the final user. 

The highest level (4) is based on the MANGO draft model and especially to its . It has  been designed to solve the EpochPropagation use case risen at 2023 South Spring Interop.

>>>> Tu puex virer cet exemple que se retouvera plus bas dans la definition ds niveaux

.. doctest-remote-data::
    >>> import pyvo
    >>> from astropy.utils.data import get_pkg_data_filename
    >>> import astropy.units as u
    >>> from pyvo.mivot.viewer.model_viewer import ModelViewer
    >>> from pyvo.utils.prototype import activate_features
    >>> activate_features('MIVOT')
    >>> votable = get_pkg_data_filename("data/simple-annotation-votable.xml", package="pyvo.mivot.tests")
    >>> m_viewer = ModelViewer(votable) # doctest: +SKIP
    >>> row_view = m_viewer.get_next_row_view() # doctest: +SKIP
    >>> print(row_view.longitude.value) # doctest: +SKIP
    >>> print(row_view.Coordinate_coosys.PhysicalCoordSys_frame.spaceRefFrame.value) # doctest: +SKIP
    >>> print(row_view.sky_coordinate) # doctest: +SKIP
        10.0
        ICRS
        <SkyCoord (ICRS): (ra, dec, distance) in (deg, deg, pc)
           (10., 10., 200.)
        (pm_ra_cosdec, pm_dec, radial_velocity) in (mas / yr, mas / yr, km / s)
           (10., -20., 1234.)>


The model view is a dynamically generated Python object whose field names are derived from
the dmroles of the MIVOT elements. There is no checking against the model structure at this level.

Example for epoch propagation
-----------------------------
.. doctest-remote-data::
    >>> with ModelViewer(votable) as m_viewer: # doctest: +SKIP
    ...     row_view = m_viewer.get_next_row_view()
    ...     epoch_propagation = row_view.epoch_propagation
    ...     past_ra, past_dec = epoch_propagation.apply_space_motion(dt=-42 * u.year)
    ...     future_ra, future_dec = epoch_propagation.apply_space_motion(dt=2 * u.year)
    ...     print("past_ra, past_dec :", epoch_propagation.apply_space_motion(dt=-42 * u.year))
    ...     print("future_ra, future_dec :", epoch_propagation.apply_space_motion(dt=2 * u.year))
    past_ra, past_dec : (<Longitude 9.9998763 deg>, <Latitude 10.00024364 deg>)
    future_ra, future_dec : (<Longitude 10.00000563 deg>, <Latitude 9.99998891 deg>)

We implement the epoch propagation by using astropy functions and the data provided by the MIVOT block.

Implementation
==============
The implementation relies on the Astropy's write and read annotation modules (6.0+),
which allows to get and set Mivot blocks from/into VOTables.
We use this new Astropy feature, MIVOT, to retrieve the MIVOT block.

This implementation is built in 4 lavels, denoting the abstraction level in relation to the XML block.

Level 0: ModelViewer
--------------------
Provide the MIVOT block as it is in the VOTable: No references are resolved.
The Mivot block is provided as an xml tree. This feature is available in Astropy 6.0.

>>> tu peux mettre ici un snippet de code level0

Level 1: ModelViewerLayer1
--------------------------
Provide access to an xml tree whose structure matches the model view of the current row.
The internal references have been resolved. The attribute values have been set with the actual data values.
This XML element is intended to be used as a basis for building any objects.
The layer 1 output can be browsed using XPATH queries.

>>> tu peux mettre ici un snippet de code level 1

Level 2: ModelViewerLayer2
--------------------------
Just a few methods to make the browsing of the layer 1 output easier.
The layer 2 API allows users to retrieve MIVOT elements by their @dmrole or @dmtype.
At this level, the MIVOT block must still be handled as an xml element.
This module is not completely implemented.

>>> tu peux mettre ici un snippet de code level2

Level 3: ModelViewerLayer3
--------------------------
ModelViewerLayer3 generates, from the layer 1 output, a nested dictionary
representing the entire XML INSTANCE with its hierarchy.
From this dictionary, we build a :py:class:`pyvo.mivot.viewer.mivot_class.MivotClass`,
which is a dictionary containing only the essential information used to process data.
MivotClass basically stores all XML objects in its attribute dictionary :py:attr:`__dict__`.

>>> tu peux mettre ici un snippet de code level3

Level 4: Integrated to ModelViewerLayer3
----------------------------------------
This level is an extension of ModelViewerLayer3. It can generate SkypCoord instances from MANGO:EpochPosistion instances and aply to them an epch propagation.
>>> tu peux mettre ici un snippet de code level4


Reference/API
=============

.. automodapi:: pyvo.mivot.viewer
.. automodapi:: pyvo.mivot.seekers
.. automodapi:: pyvo.mivot.features
.. automodapi:: pyvo.mivot.utils


