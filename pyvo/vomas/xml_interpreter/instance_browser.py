'''
Created on 31 Mar 2022

@author: laurentmichel
'''
from pyvo.vomas.xml_interpreter.exceptions import NotImplementedException,\
    ParsingException, MappingException
from pyvo.vomas.utils.xml_utils import XmlUtils
from copy import deepcopy
from pyvo.vomas.utils.dict_utils import DictUtils

class Instance(object):
    '''
    classdocs
    '''

    def __init__(self, xmltree):
        '''
        Constructor
        '''
        self._xmltree = deepcopy(xmltree)
        self._dmtype = None
        self._dmrole = None
        cpt = 0
        for root in self._xmltree.xpath('/INSTANCE'):
            self._dmtype = root.get("dmtype")
            self._dmrole = root.get("dmrole")
            cpt += 1
        if cpt == 0:
            raise MappingException("Attempt build build an instance from a block without INSTANCE element")
        elif cpt > 1:
            raise MappingException("Attempt build build an instance from a block with more than one INSTANCE element")

    
    def get_attributes(self):
        retour = {}
        for att in self._xmltree.xpath('/INSTANCE/ATTRIBUTE'):
            retour[att.get("dmrole")] = Attribute(att)
        return retour
    
    def get_instances(self):
        retour = {}
        for inst in self._xmltree.xpath('/INSTANCE/INSTANCE'):
            retour[inst.get("dmrole")] = Instance(inst)
        return retour
    
    def get_collections(self):
        retour = {}
        for inst in self._xmltree.xpath('/INSTANCE/COLLECTION'):
            retour[inst.get("dmrole")] = Collection(inst)
        return retour
        
    def get_attribute(self, *dmrole_path):
        path_len = len(dmrole_path)
        
        if path_len == 0 :
            raise ParsingException("No attribute role given")
        
        instance = self
        for cpt in range(path_len - 1):
            inst_map = instance.get_instances()
            if dmrole_path[cpt] not in inst_map.keys():
                raise ParsingException(f"INSTANCE[@dmrole={instance.dmrole}] contains no INSTANCE[@dmrole={dmrole_path[cpt]}]")
            instance = inst_map[dmrole_path[cpt]]
                        
        last_role = dmrole_path[path_len - 1]
        att_map = instance.get_attributes()
        if last_role not in att_map.keys():
            raise ParsingException(f"INSTANCE[@dmrole={instance.dmrole}] has no ATTRIBUTE[@dmrole={dmrole_path[path_len - 1]}]")
        attribute = att_map[last_role]
        return attribute

        
    @property
    def dmtype(self):
        return self._dmtype
    
    @property
    def dmrole(self):
        return self._dmrole

class Attribute(object):
    '''
    classdocs
    '''

    def __init__(self, xmltree):
        '''
        Constructor
        '''
        self._xmltree = deepcopy(xmltree)
        if self._xmltree.tag != "ATTRIBUTE":
            raise MappingException("Attempt build build an attribute from a block without ATTRIBUTE element")
        
        self._dmtype = self._xmltree.get("dmtype")
        self._dmrole = self._xmltree.get("dmrole")
        self._value = self._xmltree.get("value")
        self._unit = self._xmltree.get("unit")

    @property
    def dmtype(self):
        return self._dmtype
    
    @property
    def dmrole(self):
        return self._dmrole

    @property
    def value(self):
        return self._value
    
    @property
    def unit(self):
        return self._unit

class Collection(object):
    '''
    classdocs
    '''

    def __init__(self, xmltree):
        '''
        Constructor
        '''
        self._xmltree = deepcopy(xmltree)
        if self._xmltree.tag != "COLLECTION":
            raise MappingException("Attempt build build an attribute from a block without COLLECTION element")
        self._dmrole = self._xmltree.get("dmrole")
    
    @property
    def dmrole(self):
        return self._dmrole
    
    def get_items(self):
        retour = {"type": None, "items": []}
        for ele in self._xmltree.xpath('/COLLECTION/*'):
            tag = ele.tag
            if tag not in ['ATTRIBUTE', 'INSTANCE', 'COLLECTION']:
                continue
            if retour["type"] is None:
                retour["type"] = tag
            elif retour["type"] != tag:
                raise MappingException("A collection can contain ATTRIBUTES, COLLECTION or INSTANCES but nor a mix")
            if tag == 'ATTRIBUTE':
                retour['items'].append(Attribute(ele))
            elif tag == 'INSTANCE':
                retour['items'].append(Instance(ele))
            else:
                retour['items'].append(Collection(ele))
        return retour


        
