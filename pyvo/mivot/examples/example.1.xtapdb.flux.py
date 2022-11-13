"""
Created on Jan 6, 2022

@author: laurentmichel
"""
import unittest
import os
from astropy.io.votable import parse

from pyvo.mivot.utils.xml_utils import XmlUtils
from pyvo.mivot.utils.dict_utils import DictUtils
from pyvo.mivot.xml_interpreter.model_viewer import ModelViewer
from pyvo.mivot.class_wrappers.mango.mango_parameter import MangoObject

class TestLonLatPoint(unittest.TestCase):
    votable = None
    mviewer = None
    def test_global_getters(self):      
        self.maxDiff = None
        
        while self.mviewer.get_next_row()  is not None:     

            for mango_type in self.mviewer.get_model_component_by_type("mango:MangoObject"):
                mango_object = MangoObject(mango_type)                
                print(f"== Source {mango_object.identifier}")
                print("    Photometric data")
                for mango_parameter in mango_object._parameters:
                    if mango_parameter.isPhotometry():
                        filter = mango_parameter.measure.coord.coordSys.frame.photCal.photometryFilter
                        print(f"    {mango_parameter.measure.coord.cval} +/- {mango_parameter.measure.error.radius}"
                              f"\tfilter {filter.name} {filter.bandwidth.start} "
                              f"to {filter.bandwidth.stop} {filter.bandwidth.unitexpression} ")       
                print("=============================")

    @classmethod
    def setUpClass(cls):
        cls.data_path = os.path.dirname(os.path.realpath(__file__))
        cls.votable = parse(os.path.join(cls.data_path, "data/xtapdb.flux.xml"))
        cls.mviewer = ModelViewer(None, parsed_votable=cls.votable)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()