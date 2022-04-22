'''
Created on 24 Mar 2022

https://docs.astropy.org/en/latest/development/workflow/get_devel_version.html
pip3 uninstall astropy
git clone astropyfork
cd astropy
pip install cython

python setup.py develop
pip3 show astropy

@author: laurentmichel
'''
import os
from pyvo.dal.tap import TAPResults
from pyvo.vomas.xml_interpreter.model_viewer import ModelViewer
from pyvo.vomas.utils.dict_utils import DictUtils
from pyvo.vomas.utils.xml_utils import XmlUtils
from astropy.io.votable import parse
from pyvo.vomas.xml_interpreter.instance_browser import Instance
   
data_path = os.path.dirname(os.path.realpath(__file__))
resultset = TAPResults(parse(os.path.join(data_path, "data/input/test.1.xml")))

mviewer = None    
for resource in resultset.votable.resources:
    mviewer = ModelViewer(resource)

print(DictUtils.print_pretty_json(mviewer.get_templates_models()))

mviewer.connect_table("Results")

#while True:
row = None
while mviewer.get_next_row() is not None:
    row = mviewer.current_data_row
    for mjd in mviewer.get_model_component_by_type("coords:MJD"):
        XmlUtils.pretty_print(mjd)
    break

while mviewer.get_next_row() is not None:
    model_view = mviewer.get_model_view()
    XmlUtils.pretty_print(model_view)
    for root in model_view.xpath('/TEMPLATES/INSTANCE'):
        instance = Instance(root)
        collection = instance.get_collections()['cube:NDPoint.observable']
        obs_items = collection.get_items()["items"]
        for obs_item in obs_items:
            measure = obs_item.get_instances()["cube:MeasurementAxis.measure"]
            print(f"====== {measure.dmrole} {measure.dmtype}")
            for meas_role , coord in measure.get_instances().items():
                print(f"{coord.dmrole} {coord.dmtype}")
        break
    break

