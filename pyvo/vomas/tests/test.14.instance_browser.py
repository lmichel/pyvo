"""
Created on jan  2022

@author: laurentmichel
"""
import unittest
import os

from pyvo.vomas.utils.xml_utils import XmlUtils

from pyvo.vomas.xml_interpreter.instance_browser import Instance
from pyvo.vomas.xml_interpreter.exceptions import ParsingException

class TestInstanceBrowser(unittest.TestCase):

    def test_MJDInstance(self):      
        self.maxDiff = None
        vpath = os.path.join(self.data_path, "data/input/test.14.1.xml")
        xmltree = XmlUtils.xmltree_from_file(vpath)
        instance = Instance(xmltree)
        
        self.assertEqual(instance.dmrole, 'meas:Time.coord')
        self.assertEqual(instance.dmtype, 'coords:MJD')
        
        attributes = instance.get_attributes()
            
        self.assertListEqual(list(attributes.keys()), ['coords:MJD.date'])

        attribute = attributes['coords:MJD.date']
        self.assertEqual(attribute.dmrole, 'coords:MJD.date')
        self.assertEqual(attribute.dmtype, 'ivoa:real')
        self.assertEqual(attribute.value, '1705.9437360200984')
        self.assertIsNone(attribute.unit)
        
        instances = instance.get_instances()
            
        self.assertListEqual(list(instances.keys()), ['coords:Coordinate.coordSys'])
        coord_sys = instances['coords:Coordinate.coordSys']

        self.assertEqual(coord_sys.dmrole, 'coords:Coordinate.coordSys')
        self.assertEqual(coord_sys.dmtype, 'coords:TimeSys')

        sys_inst = coord_sys.get_instances()
            
        self.assertListEqual(list(sys_inst.keys()), ['coords:PhysicalCoordSys.frame'])
        
        frame = sys_inst['coords:PhysicalCoordSys.frame']

        attributes = frame.get_attributes()
            
        self.assertListEqual(list(attributes.keys()), ['coords:TimeFrame.timescale'])
        attribute = attributes['coords:TimeFrame.timescale']
        self.assertEqual(attribute.dmrole, 'coords:TimeFrame.timescale')
        self.assertEqual(attribute.dmtype, 'ivoa:string')
        self.assertEqual(attribute.value, 'TCB')
        self.assertIsNone(attribute.unit)
        
        instances = frame.get_instances()
            
        self.assertListEqual(list(instances.keys()), ['coords:TimeFrame.refPosition'])
         
        attributes = instances['coords:TimeFrame.refPosition'].get_attributes()
            
        self.assertListEqual(list(attributes.keys()), ['coords:StdRefLocation.position'])
        attribute = attributes['coords:StdRefLocation.position']
        self.assertEqual(attribute.dmrole, 'coords:StdRefLocation.position')
        self.assertEqual(attribute.dmtype, 'ivoa:string')
        self.assertEqual(attribute.value, 'BARYCENTER')
        self.assertIsNone(attribute.unit)
        
        self.assertEqual(instance.get_attribute('coords:Coordinate.coordSys', 
                                                'coords:PhysicalCoordSys.frame', 
                                                'coords:TimeFrame.timescale').value, 'TCB')
        
        try:
            instance.get_attribute('coords:Coordinate.coordSys', 
                                   'coords:PhysicalCoordSys.frame', 
                                   'coords:TimeFrame.timescaleWRONG').value
        except ParsingException as e:
            self.assertEqual(e.__str__(), 
                             "INSTANCE[@dmrole=coords:PhysicalCoordSys.frame] has no ATTRIBUTE[@dmrole=coords:TimeFrame.timescaleWRONG]")

        try:
            instance.get_attribute('coords:Coordinate.coordSys', 
                                   'coords:PhysicalCoordSys.frameWRONG', 
                                   'coords:TimeFrame.timescale').value
        except ParsingException as e:
            self.assertEqual(e.__str__(), 
                             "INSTANCE[@dmrole=coords:Coordinate.coordSys] contains no INSTANCE[@dmrole=coords:PhysicalCoordSys.frameWRONG]")

        
    def setUp(self):
        self.data_path = os.path.dirname(os.path.realpath(__file__))

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()