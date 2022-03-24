'''
Created on 24 Mar 2022

https://docs.astropy.org/en/latest/development/workflow/get_devel_version.html
pip3 uninstall astropy
git clone astropyfork
cd astropy
python setup.py develop
pip3 show astropy

@author: laurentmichel
'''
import os
import pyvo as vo
import astropy 
from pyvo.dal.tap import TAPResults
from pyvo.vomas.xml_interpreter.model_viewer import ModelViewer
from pyvo.vomas.utils.dict_utils import DictUtils
from pyvo.vomas.utils.xml_utils import XmlUtils
from astropy.io.votable import parse


print(astropy.__version__)
   
data_path = os.path.dirname(os.path.realpath(__file__))
resultset = TAPResults(parse(os.path.join(data_path, "data/input/test.1.xml")))

mviewer = None    
for resource in resultset.votable.resources:
    print(f"Resource type: {resource.type}  Mapping block: {resource.model_mapping}")
    mviewer = ModelViewer(resource)

print(DictUtils.print_pretty_json(mviewer.get_templates_models()))

mviewer.connect_table("Results")

while True:
    row = mviewer.get_next_row()
    if row is None:
        break;
    XmlUtils.pretty_print(mviewer.get_model_view())
    for mjd in mviewer.get_model_component_by_type("coords:MJD"):
        XmlUtils.pretty_print(mjd)
    break
