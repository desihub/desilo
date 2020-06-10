"""
Created on May 21, 2020

@author: Parker Fagrelius

start server with the following command:

bokeh serve --show bk_nl_input.py

view at: http://localhost:5006/bk_nl_input
"""


#Imports
import os, glob
import numpy as np
import pandas as pd
from datetime import datetime

from bokeh.io import curdoc  # , output_file, save
from bokeh.plotting import figure
from bokeh.palettes import Magma256, Category10
from bokeh.models import (
    LinearColorMapper, ColorBar, AdaptiveTicker, TextInput, ColumnDataSource,
    Title, Button, CheckboxButtonGroup, CategoricalColorMapper, Paragraph,DateFormatter,
    TextAreaInput, Select, PreText, Span, CheckboxGroup)
from bokeh.models.widgets.markups import Div
from bokeh.models.widgets.tables import (
    DataTable, TableColumn, SelectEditor, IntEditor, NumberEditor, StringEditor,PercentEditor)
from bokeh.layouts import column, layout
from bokeh.palettes import d3
from bokeh.client import push_session
from bokeh.models.widgets import Panel, Tabs


import nightlog as nl

title = Div(text='''
<font size="4">DESI Night Log - Operating Scientist</font> ''',
            width=500)

#Initialize Night Log Info
subtitle_1 = Div(text='''<font size="3">Initialize Night Log</font> ''',width=500)
info_1 = Div(text='''<font size="2">Time Formats: 6:18pm = 18:18 = 1818. All times in Local Time </font> ''',width=500)
date_input = TextInput(title ='DATE', value = datetime.now().strftime("%Y%m%d"))

your_firstname = TextInput(title ='Your Name', placeholder = 'John')
your_lastname = TextInput(placeholder = 'Smith')

LO_firstname = TextInput(title ='LO Name', placeholder = 'Molly')
LO_lastname = TextInput(placeholder = 'Jackson')

OA_firstname = TextInput(title ='OA Name', placeholder = 'Paul')
OA_lastname = TextInput(placeholder = 'Lawson')

time_sunset = TextInput(title ='Time of Sunset', placeholder = '1838')
time_18_deg_twilight_ends = TextInput(title ='Time 18 deg Twilight Ends', placeholder = '1956')
time_18_deg_twilight_starts = TextInput(title ='Time 18 deg Twilight Ends', placeholder = '0513')
time_sunrise = TextInput(title ='Time of Sunrise', placeholder = '0631')
time_moonrise = TextInput(title ='Time of Moonrise', placeholder = '0127')
time_moonset = TextInput(title ='Time of Moonset', placeholder = 'daytime')
illumination = TextInput(title ='Moon Illumination', placeholder = '50')
sunset_weather = TextInput(title ='Weather conditions as sunset', placeholder = 'clear skies')

init_bt = Button(label="Initialize Night Log", button_type='primary',width=300)
connect_bt = Button(label="Connect to Existing Night Log (enter date)", button_type='primary',width=300)
info_connect = Div(text='''Not connected to Night Log''')

#Inputs for Exposures (combined Startup and Observations)
global header_options
header_options = ['Startup','Calibrations','Focus','Observation']
subtitle_2 = Div(text='''<font size="3">Nightly Progress</font> ''',width=500)
info_2 = Div(text='''<font size="2">Fill In Only Information Relevant</font> ''',width=500)
seq_type = Select(title="Description Header - Use one already created", value = 'Observation', options=header_options)
header_new = TextInput(value=None)
hdr_btn = Button(label='OR Create new Header', button_type='primary')
exp_time = TextInput(title ='Time', placeholder = '2007',value=None)
exp_comment = TextAreaInput(title ='Comment/Remark', placeholder = 'Humidity high for calibration lamps',value=None,rows=6)
add_image = TextInput(title="Add Image",placeholder = 'Pictures/image.png',value=None)

info_3 = Div(text='''<font size="2">Other Meta Data to Save with Comments</font> ''',width=500)
exp_exposure_start = TextInput(title ='Exposure Number: First', placeholder = '12345',value = None)
exp_exposure_finish = TextInput(title ='Exposure Number: Last', placeholder = '12345',value = None)

exp_type = Select(title="Exposure Type", value = None, options=['None','Zero','Focus','Dark','Arc','FVC','DESI'])
exp_script = TextInput(title ='Script Name', placeholder = 'dithering.json', value=None)
exp_time_end = TextInput(title ='Time End', placeholder = '2007',value=None)
exp_focus_trim = TextInput(title ='Trim from Focus', placeholder = '54',value=None)
exp_tile = TextInput(title ='Tile Number', placeholder = '68001',value=None)
exp_tile_type = Select(title="Tile Type", value = None, options=['QSO','LRG','ELG','BGS','MW'])
exp_btn = Button(label='Add', button_type='primary')



# Weather
subtitle_3 = Div(text='''<font size="3">Weather</font> ''', width=500)
def init_weather_source_data():
    """
    Creates a table with pre-identified Times for weather input
    """
    data = pd.DataFrame(columns = ['time','desc','temp','wind','humidity'])
    hours = [17,18,19,20,21,22,23,24,1,2,3,4,5,6,7]
    data['time'] = [("%s:00" % str(hour).zfill(2)) for hour in hours]
    return ColumnDataSource(data)

weather_source = init_weather_source_data()
columns = [TableColumn(field='time', title='Time UTC', width=100),
           TableColumn(field='desc', title='Description', width=200, editor=StringEditor()),
           TableColumn(field='temp', title='Temperature', width=100, editor=NumberEditor()),
           TableColumn(field='wind', title='Wind Speed', width=100, editor=NumberEditor()),
           TableColumn(field='humidity', title='Humidity', width=100, editor=PercentEditor())]

weather_table = DataTable(source=weather_source, columns=columns, editable=True,
              sortable=False, reorderable=False, fit_columns=False,
              min_width=1300, sizing_mode='stretch_width')
weather_btn = Button(label='Update NightLog', button_type='primary')

#Problems
subtitle_4 = Div(text='''<font size="3">Problems</font> ''', width=500)
prob_time = TextInput(title ='Time', placeholder = '2007', value=None)
prob_input = TextAreaInput(placeholder="description", rows=6, title="Problem Description:")
prob_btn = Button(label='Add', button_type='primary')

subtitle_5 = Div(text='''<font size="3">Current Night Log</font> ''', width=500)
nl_btn = Button(label='Get Current Night Log', button_type='primary')
nl_text = Div(text='''Current Night Log''',width=1000)

subtitle_6 = Div(text='''<font size="3">OS Checklist</font> ''', width=500)
os_checklist = CheckboxGroup(
        labels=["Did you check the weather?", "Did you check the guiding?", "Did you check the focal plane?","Did you check the spectrographs?"])
check_time = TextInput(title ='Time', placeholder = '2007', value=None)
check_btn = Button(label='Submit', button_type='primary')

def update_weather_source_data():
    """
    Adds initial input to weather table
    """
    new_data = pd.DataFrame(weather_source.data.copy())
    sunset_hour = datetime.strptime(get_time(time_sunset.value),'%H%M').hour
    idx = new_data[new_data.time == "%s:00"%(str(sunset_hour).zfill(2))].index[0]
    new_data.at[idx,'desc'] = sunset_weather.value
    del new_data['index']

    weather_source.data = new_data


def initialize_log():
    """
    Initialize Night Log with Input Date
    """
    try:
        date = datetime.strptime(date_input.value, '%Y%m%d')
    except:
        date = datetime.now()
    global DESI_Log
    DESI_Log=nl.NightLog(str(date.year),str(date.month).zfill(2),str(date.day).zfill(2))
    DESI_Log.initializing()
    DESI_Log.get_started_os(your_firstname.value,your_lastname.value,LO_firstname.value,LO_lastname.value,
        OA_firstname.value,OA_lastname.value,get_time(time_sunset.value),get_time(time_18_deg_twilight_ends.value),get_time(time_18_deg_twilight_starts.value),
        get_time(time_sunrise.value),time_moonrise.value,time_moonset.value,illumination.value,sunset_weather.value)

    update_weather_source_data()
    info_connect.text = 'Night Log is Initialized'

def connect_log():
    try:
        date = datetime.strptime(date_input.value, '%Y%m%d')
    except:
        date = datetime.now()
    global DESI_Log
    DESI_Log=nl.NightLog(str(date.year),str(date.month).zfill(2),str(date.day).zfill(2))
    DESI_Log.check_exists()
    info_connect.text = 'Connected to Existing Night Log'

    meta_dict = DESI_Log.get_meta_data()
    your_firstname.value = meta_dict['os_1']
    your_lastname.value = meta_dict['os_last']
    LO_firstname.value = meta_dict['os_lo_1']
    LO_lastname.value = meta_dict['os_lo_last']
    OA_firstname.value = meta_dict['os_oa_1']
    OA_lastname.value = meta_dict['os_oa_last']
    time_sunset.value = meta_dict['os_sunset']
    time_18_deg_twilight_ends.value = meta_dict['os_end18']
    time_18_deg_twilight_starts.value = meta_dict['os_start18']
    time_sunrise.value = meta_dict['os_sunrise']
    time_moonrise.value = meta_dict['os_moonrise']
    time_moonset.value = meta_dict['os_moonset']
    illumination.value = meta_dict['os_illumination']
    sunset_weather.value = meta_dict['os_weather_conditions']

    try:
      new_data = pd.read_csv(DESI_Log.weather_file)
      new_data = new_data[['time','desc','temp','wind','humidity']]
      weather_source.data = new_data
    except:
      pass


def exp_add():
    if exp_type == 'Startup&Calibrations':
        suc_add()
    elif exp_type == 'Observations':
        obs_add()

    # Reset everything
    exp_time.value = None 
    exp_comment.value = None 
    add_image.value = None 

    exp_exposure_start.value = None 
    exp_exposure_finish.value = None 

    exp_type.value = None 
    exp_script.value = None 
    exp_time_end.value = None 
    exp_focus_trim.value = None 
    exp_tile.value = None 
    exp_tile_type.value = None 

def suc_add():
    """
    Function to add line about a Startup&Calibrations sequence in the Night Log

    Note, I really don't like how this is currently implemented on my end, but I also don't really l
    ike that there are different functions for different types of inputs. I think we should have one kind of input,
    and if the value is None or Nan then it's not included. So, I'll clean up my side if we can have fewer functions
    for DESI_Log
    """

    inputs = [exp_time.value, exp_comment.value,exp_exposure_start.value, exp_exposure_finish.value,
              exp_type.value, exp_script.value, exp_time_end.value, exp_focus_trim.value]
    idx = np.where(np.array(inputs) == None)[0]
    if (np.array([0,1]) == idx).all():
        DESI_Log.supcal_add_com_os(get_time(exp_time.value),exp_comment.value)
    elif (np.array([0,1,2,4]) == idx).all():
        DESI_Log.supcal_add_seq_os(get_time(exp_time.value),exp_exposure_start.value, exp_type.value, exp_comment.value)
    elif (np.array([0,1,2,5,6]) == idx).all():
        DESI_Log.supcal_add_spec_script_os(get_time(exp_time.value),exp_exposure_start.value, exp_script.value,get_time(exp_time_end.value), exp_comment.value)
    elif (np.array([0,1,2,3,5,6,7]) == idx).all():
        DESI_Log.supcal_add_spec_script_os(get_time(exp_time.value),exp_exposure_start.value, exp_script.value,get_time(exp_time_end.value), exp_exposure_start.value, exp_comment.value)
    else:
        print("missing information")

def obs_add():
    """
    Function to add line about an exposure sequence in the Night Log

    Note, I really don't like how this is currently implemented on my end, but I also don't really l
    ike that there are different functions for different types of inputs. I think we should have one kind of input,
    and if the value is None or Nan then it's not included. So, I'll clean up my side if we can have fewer functions
    for DESI_Log
    """
    inputs = [exp_time.value, exp_comment.value,exp_exposure_start.value, exp_exposure_finish.value,
              exp_type.value, exp_script.value, exp_time_end.value, exp_focus_trim.value,exp_tile.value, exp_tile_type.value]
    idx = np.where(np.array(inputs) == None)[0]
    if (np.array([0,1,2,4,8,9]) == idx).all():
        DESI_Log.obs_add_seq_os(get_time(exp_time.value),exp_exposure_start.value,exp_type.value,exp_tile.value,exp_tile_type.value,exp_comment.value)
    elif (np.array([0,1]) == idx).all():
        DESI_Log.obs_add_com_os(time,remark)
    elif (np.array([0,1,2,6]) == idx).all():
        DESI_Log.obs_add_script_os(get_time(exp_time.value), exp_exposure_start.value, get_time(ex_time_end.value), exp_comment.value)
    else:
        print("missing information")

def weather_add():
    """
    We need to create a function in DESI_Log for adding a row of weather information
    """
    data = pd.DataFrame(weather_source.data)
    DESI_Log.obs_add_weather(data)

def add_header():
    header_options.append(header_new.value)
    print(header_options)
    seq_type.options = header_options

def check_add():
    """add checklist
    """
    os_checklist.active = []


def prob_add():
    # Currently no code in jupyter notebook
    pass

def get_time(time):
    try:
        t = datetime.strptime(time,'%H%M')
        return t.strftime('%H%M')
    except:
        try:
            t = datetime.strptime(time,'%I:%M%p')
            return t.strftime('%H%M')
        except:
            try:
                t = datetime.strptime(time,'%H:%M')
                return t.strftime('%H%M')
            except:
                print("need format %H%M, %H:%M, %H:%M%p")
                return None


def current_nl():
    DESI_Log.finish_the_night()
    path = "nightlogs/"+DESI_Log.obsday+"/nightlog.html"
    nl_file = open(path,'r')
    nl_txt = ''
    for line in nl_file:
        nl_txt =  nl_txt + line + '\n'
    nl_text.text = nl_txt
    nl_file.closed
    



# Layouts and Actions on Bokeh Page

init_bt.on_click(initialize_log)
connect_bt.on_click(connect_log)
exp_btn.on_click(exp_add)
hdr_btn.on_click(add_header)
weather_btn.on_click(weather_add)
prob_btn.on_click(prob_add)
nl_btn.on_click(current_nl)
check_btn.on_click(check_add)

layout1 = layout([[title],
                 [subtitle_1],
                 [info_1],
                 [date_input, [your_firstname, your_lastname], [LO_firstname, LO_lastname],[OA_firstname, OA_lastname]],
                 [[time_sunset,time_sunrise],[time_18_deg_twilight_ends,time_18_deg_twilight_starts],[time_moonrise,time_moonset],
                 [illumination,sunset_weather]],
                 [init_bt],
                 [connect_bt],
                 [info_connect]
                 ])
tab1 = Panel(child=layout1, title="Initialization")

layout2 = layout([[title],
                 [subtitle_2],
                 [info_2],
                 [seq_type],
                 [header_new,hdr_btn],
                 [exp_time, exp_comment],
                 [info_3],
                 [add_image],
                 [exp_exposure_start, exp_exposure_finish],
                 [exp_type],
                 [exp_script],
                 [exp_time_end],
                 [exp_focus_trim],
                 [exp_tile, exp_tile_type],
                 [exp_btn]
                 ])
tab2 = Panel(child=layout2, title="Nightly Progress")


layout3 = layout([[title],
                 [subtitle_3],
                 [weather_table],
                 [weather_btn]
                 ])
tab3 = Panel(child=layout3, title="Weather")

layout4 = layout([[title],
                 [subtitle_4],
                 [prob_time, prob_input],
                 [prob_btn]
                 ])
tab4 = Panel(child=layout4, title="Problems")

layout5 = layout([[title],
                [subtitle_5],
                [nl_btn],
                [nl_text]])
tab5 = Panel(child=layout5, title="Current Night Log")

layout6 = layout([[title],
                [subtitle_6],
                [os_checklist],
                [check_time, check_btn]])
tab6 = Panel(child=layout6, title="OS Checklist")

tabs = Tabs(tabs=[ tab1, tab2 , tab3, tab4, tab5, tab6])

curdoc().title = 'DESI Night Log - Operations Scientist'
curdoc().add_root(tabs)
