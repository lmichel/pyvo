"""
Created on Jan 6, 2022

@author: laurentmichel
"""
import unittest
import os
import io
from astropy.io.votable import parse
from astropy.io.votable import tree 
from astropy.io.votable.tree import VOTableFile, Resource, ModelMapping

from pyvo.mivot.utils.xml_utils import XmlUtils
from pyvo.mivot.utils.dict_utils import DictUtils
from pyvo.mivot.xml_interpreter.model_viewer import ModelViewer
from pyvo.mivot.class_wrappers.mango.mango_parameter import MangoObject
from pyvo.mivot.class_wrappers.photdm.photfilter import PhotometryFilter


data_path = os.path.dirname(os.path.realpath(__file__))
raw_votable_path = os.path.join(data_path, "data/xtapdb.flux.raw.xml")

def annotate_votable(annotation_block):
    """
    Place the annotation block at the right place in the raw VOTable
    and return the annotated VOTable as a bytes stream
    """
    # get the annotation block as a string
    with open(annotation_block) as mivot_file:
        mivot_block = mivot_file.read()
        # And build an Astropy MIVOT instance
        model_mapping = ModelMapping(mivot_block)
        # parse the raw votable
        raw_votable = parse(raw_votable_path)
        # let's assume that the first resource will be annotated (usually true) 
        for resource in raw_votable.resources:
            # build the resources
            meta_resource = Resource()
            meta_resource.type = "meta"
            # Put the MIVOT block in that resource
            meta_resource.model_mapping = model_mapping
            # and put that stuff in the resource to be annotated
            resource.resources.append(meta_resource)
            # release the annotated VOTable as a Bytes stream 
            votable_data_stream = io.BytesIO()
            raw_votable.to_xml(votable_data_stream)
            votable_data_stream.seek(0)
            return votable_data_stream
        
def search_photometric_points(votable_data_stream):
    """
    Print out the photometric points found in the Mango instances
    """
    # Get the modelviewer that provides a DM view on the VOTable data
    votable = parse(votable_data_stream)
    mviewer = ModelViewer(None, parsed_votable=votable)  
      
    while mviewer.get_next_row()  is not None:   
        # Get the MANGO instance mapped on the row data  
        for mango_type in mviewer.get_model_component_by_type("mango:MangoObject"):
            mango_object = MangoObject(mango_type)                
            print(f"== Source {mango_object.identifier}")
            print("    Photometric data")
            # Search the photometric points embedded in the mango instance
            for mango_parameter in mango_object._parameters:
                if mango_parameter.isPhotometry():
                    filter_instance = mango_parameter.measure.coord.coordSys.frame.photCal.photometryFilter
                    print(f"      {mango_parameter.measure.coord.cval} +/- {mango_parameter.measure.error.radius}"
                          f"\tfilter {filter_instance.name} {filter_instance.bandwidth.start} "
                          f"to {filter_instance.bandwidth.stop} {filter_instance.bandwidth.unitexpression} ")       
            print("=============================")

def search_filters_in_votable(votable_data_stream):
    """
    Print out all the photometric filters found in GLOBALS
    Not caring about the connection with data columns
    """
    # Get the modelviewer that provides a DM view on the VOTable data
    votable = parse(votable_data_stream)
    mviewer = ModelViewer(None, parsed_votable=votable)
    
    print("\nFilters found in GLOBALS")
    # Search all photometric filters located in GLOBALS
    for xml_filter in mviewer._annotation_seeker.get_instance_by_dmtype("photdm:PhotometryFilter")["GLOBALS"]:
        photometryFilter = PhotometryFilter(xml_filter)
        print(f" {photometryFilter.name} {photometryFilter.bandwidth.start} "
                          f"to {photometryFilter.bandwidth.stop} {photometryFilter.bandwidth.unitexpression} ")       

# Process a VOTable just containing the filters in the GLOBALS
data_stream = annotate_votable(
    os.path.join(data_path, "data/xtapdb.flux.mivot.photdm.xml")
    )
search_filters_in_votable(data_stream)


# Process a VOTable with data mapped on Mango
data_stream = annotate_votable(
    os.path.join(data_path, "data/xtapdb.flux.mivot.mango.xml")
    )

search_photometric_points(data_stream)

