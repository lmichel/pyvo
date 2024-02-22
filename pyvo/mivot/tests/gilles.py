'''
Created on 20 févr. 2024

@author: michel
'''
from astropy.io.votable import parse
from xml.etree import ElementTree as etree
from pyvo.mivot.utils.xml_utils import XmlUtils
from pyvo.mivot.viewer.model_viewer_level1 import ModelViewerLevel1, ModelViewerLevel2
m_viewer = ModelViewerLevel1("t.vot")
m_viewer.get_next_row()
XmlUtils.pretty_print(m_viewer._get_model_view()) 