"""
Created on Feb 26, 2021

@author: laurentmichel
"""
import unittest
import os
from pyvo.vomas.utils.xml_utils import XmlUtils
from astropy.io.votable import parse
from pyvo.vomas.xml_interpreter.model_viewer import ModelViewer
from pyvo.vomas.xml_interpreter.dynamic_reference import DynamicReference

class TestMapppingBuilder(unittest.TestCase):

    def test_PKTable(self):      
        self.maxDiff = None
        
        data_path = os.path.dirname(os.path.realpath(__file__))
        votable = parse(os.path.join(data_path, "data/input/test.1.xml"))
        
        mviewer = None
        for resource in votable.resources:
            mviewer = ModelViewer(resource, votable_path=os.path.join(data_path, "data/input/test.1.xml"))
            break;

        mviewer.connect_table('_PKTable')

        dynamic_ref = DynamicReference(mviewer, "REFERENCE_2", '_PKTable', mviewer._dyn_references["REFERENCE_2"])
        dynamic_ref._set_mode()
        
        self.assertEqual(dynamic_ref.target_id, '_Datasets')
        self.assertEqual(dynamic_ref.fk_ref, '_pksrcid')
        self.assertEqual(dynamic_ref.fk_col, 0)
        
        row = mviewer.get_next_row()    
 
        XmlUtils.assertXmltreeEqualsFile(dynamic_ref.get_target_instance(row),
                                         os.path.join(self.data_path, "data/output/test.3.1.xml"))
 

    def setUp(self):
        self.data_path = os.path.dirname(os.path.realpath(__file__))

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()