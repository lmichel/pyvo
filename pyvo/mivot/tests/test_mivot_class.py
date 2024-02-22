'''
Created on 19 févr. 2024

@author: michel
'''
import os
import pytest
from urllib.request import urlretrieve
from pyvo.mivot.viewer.model_viewer_level1 import ModelViewerLevel1
from pyvo.mivot.viewer.mivot_class import MivotClass
from pyvo.mivot.utils.exceptions import ResolveException


faze_dict = {
  "dmtype": "EpochPosition",
  "longitude": {
    "dmtype": "RealQuantity",
    "value": 52.2340018,
    "unit": "deg",
    "astropy_unit": {},
    "ref": "RAICRS"
  },
  "latitude": {
    "dmtype": "RealQuantity",
    "value": 59.8937333,
    "unit": "deg",
    "astropy_unit": {},
    "ref": "DEICRS"
  },
  }


mivot_object = MivotClass(**faze_dict)
print(mivot_object.longitude.value)
print(mivot_object.longitude.unit)
print(mivot_object.longitude.dmtype)
print(mivot_object.dmtype)

