"""
Created on May 21, 2020

@author: Parker Fagrelius

start server with the following command:

bokeh serve --show OS_Report

view at: http://localhost:5006/OS_Report
"""


#Imports
import os, glob
import numpy as np
import pandas as pd
from datetime import datetime

from bokeh.io import curdoc  # , output_file, save
from bokeh.plotting import figure, show, output_file
from bokeh.palettes import Magma256, Category10
from bokeh.models import (
    LinearColorMapper, ColorBar, AdaptiveTicker, TextInput, ColumnDataSource, Range1d,
    Title, Button, CheckboxButtonGroup, CategoricalColorMapper, Paragraph,DateFormatter,
    TextAreaInput, Select, PreText, Span, CheckboxGroup, RadioButtonGroup)
from bokeh.models.widgets.markups import Div
from bokeh.models.widgets.tables import (
    DataTable, TableColumn, SelectEditor, IntEditor, NumberEditor, StringEditor,PercentEditor)
from bokeh.layouts import column, layout
from bokeh.palettes import d3
from bokeh.client import push_session
from bokeh.models.widgets import Panel, Tabs
from bokeh.models import Span
from astropy.time import Time, TimezoneInfo
import astropy.units.si as u 

import nightlog as nl                                                                  

############################################

utc = TimezoneInfo() 
kp_zone = TimezoneInfo(utc_offset=-7*u.hour) 
zones = [utc, kp_zone]

# EXTRA FUNCTIONS
def clear_input(items):
    """
    After submitting something to the log, this will clear the form.
    """
    if isinstance(items, list):
      for item in items:
        item.value = None
    else:
      items.value = None

def get_time(time):
    """Returns strptime with utc. Takes time zone selection
    """  
    date = date_input.value
    zone = zones[time_select.active]
    try:
        t = datetime.strptime(date+":"+time,'%Y%m%d:%H%M')
    except:
        try:
            t = datetime.strptime(date+":"+time,'%Y%m%d:%I:%M%p')
        except:
            try:
                t = datetime.strptime(date+":"+time,'%Y%m%d:%H:%M')
            except:
                print("need format %H%M, %H:%M, %H:%M%p")
    try:
      tt = datetime(t.year, t.month, t.day, t.hour, t.minute, tzinfo = zone)
      return tt.strftime("%Y%m%dT%H:%M")   
    except:
      return time 

def short_time(str_time):
    """Returns %H%M in whichever time zone selected
    """
    try:
      t = datetime.strptime(str_time, "%Y%m%dT%H:%M")
      zone = zones[time_select.active]
      utc_time = datetime(t.year, t.month, t.day, t.hour, t.minute, tzinfo = utc)
      time = utc_time.astimezone(zone)
      return "{}:{}".format(time.hour, time.minute)
    except:
      return str_time




# TAB1: Initialize Night Log 
title = Div(text='''<font size="6">DESI Night Log - Operating Scientist</font> ''', width=800)
page_logo = Div(text="<img src='OS_Report/static/logo.png'>", width=350, height=300)
instructions = Div(text="The Operating Scientist (OS) is responsible for initializing the Night Log. Do so below or connect to an existing Night Log using the date. Throughout the night, enter information about the exposures, weather, and problems. Complete the OS Checklist once an hour. ",width=300)

subtitle_1 = Div(text='''<font size="4">Initialize Night Log</font> ''',width=500)
info_1 = Div(text='''<font size="2">Time Formats: 6:18pm = 18:18 = 1818. Use any format in either Local or UTC (select below). </font> ''',width=600)
time_select = RadioButtonGroup(labels=["Local", "UTC"], active=0)
date_input = TextInput(title ='DATE', value = datetime.now().strftime("%Y%m%d"))

your_firstname = TextInput(title ='Your Name', placeholder = 'John')
your_lastname = TextInput(value = 'Smith')
LO_firstname = TextInput(title ='Lead Observer Name', value = 'Molly')
LO_lastname = TextInput(value = 'Jackson')
OA_firstname = TextInput(title ='Observing Assistant Name', value = 'Paul')
OA_lastname = TextInput(value = 'Lawson')

time_sunset = TextInput(title ='Time of Sunset', value = '1838')
time_18_deg_twilight_ends = TextInput(title ='Time 18 deg Twilight Ends', value = '1956')
time_18_deg_twilight_starts = TextInput(title ='Time 18 deg Twilight Ends', value = '0513')
time_sunrise = TextInput(title ='Time of Sunrise', value = '0631')
time_moonrise = TextInput(title ='Time of Moonrise', value = '0127')
time_moonset = TextInput(title ='Time of Moonset', value = 'daytime')
illumination = TextInput(title ='Moon Illumination', value = '50')
sunset_weather = TextInput(title ='Weather conditions as sunset', value = 'clear skies')

init_bt = Button(label="Initialize Night Log", button_type='primary',width=300)
connect_bt = Button(label="Connect to Existing Night Log (enter date)", button_type='primary',width=300)
info_connect = Div(text='''Not connected to Night Log''')

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
        get_time(time_sunrise.value),get_time(time_moonrise.value),get_time(time_moonset.value),illumination.value,sunset_weather.value)

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
    your_firstname.value = short_time(meta_dict['os_1'])
    your_lastname.value = short_time(meta_dict['os_last'])
    LO_firstname.value = short_time(meta_dict['os_lo_1'])
    LO_lastname.value = short_time(meta_dict['os_lo_last'])
    OA_firstname.value = short_time(meta_dict['os_oa_1'])
    OA_lastname.value = short_time(meta_dict['os_oa_last'])
    time_sunset.value = short_time(meta_dict['os_sunset'])
    time_18_deg_twilight_ends.value = short_time(meta_dict['os_end18'])
    time_18_deg_twilight_starts.value = short_time(meta_dict['os_start18'])
    time_sunrise.value = short_time(meta_dict['os_sunrise'])
    time_moonrise.value = short_time(meta_dict['os_moonrise'])
    time_moonset.value = short_time(meta_dict['os_moonset'])
    illumination.value = meta_dict['os_illumination']
    sunset_weather.value = meta_dict['os_weather_conditions']

    try:
      new_data = pd.read_csv(DESI_Log.weather_file)
      new_data = new_data[['time','desc','temp','wind','humidity']]
      weather_source.data = new_data
    except:
      pass


# TAB2: Nightly Progress 
global header_options
header_options = ['Startup','Calibrations','Focus','Observation']
subtitle_2 = Div(text='''<font size="3">Nightly Progress</font> ''',width=500)
info_2 = Div(text='''<font size="2">Fill In Only Information Relevant</font> ''',width=500)
hdr_type = Select(title="Description Header - Use one already created", value = 'Observation', options=header_options)
hdr_btn = Button(label='Select Header', button_type='primary')

exp_time = TextInput(title ='Time', placeholder = '2007',value=None)
exp_comment = TextAreaInput(title ='Comment/Remark', placeholder = 'Humidity high for calibration lamps',value=None,rows=6)
add_image = TextInput(title="Add Image",placeholder = 'Pictures/image.png',value=None)

exp_exposure_start = TextInput(title ='Exposure Number: First', placeholder = '12345',value = None)
exp_exposure_finish = TextInput(title ='Exposure Number: Last', placeholder = '12345',value = None)

exp_type = Select(title="Exposure Type", value = None, options=['None','Zero','Focus','Dark','Arc','FVC','DESI'])
exp_script = TextInput(title ='Script Name', placeholder = 'dithering.json', value=None)
exp_time_end = TextInput(title ='Time End', placeholder = '2007',value=None)
exp_focus_trim = TextInput(title ='Trim from Focus', placeholder = '54',value=None)
exp_tile = TextInput(title ='Tile Number', placeholder = '68001',value=None)
exp_tile_type = Select(title="Tile Type", value = None, options=['QSO','LRG','ELG','BGS','MW'])
exp_btn = Button(label='Add', button_type='primary')
global input_layout
input_layout = layout([])

def choose_exposure():
    if hdr_type.value == 'Focus':
        input_layout = layout([
                 [exp_time],
                 [exp_exposure_start, exp_exposure_finish],
                 [exp_comment],
                 [exp_script],
                 [exp_focus_trim],
                 [exp_btn]])
    elif hdr_type.value == 'Startup':
        input_layout = layout([
                 [exp_time],
                 [exp_comment],
                 [exp_btn]])
    elif hdr_type.value == 'Calibrations':
        input_layout = layout([
                 [exp_time],
                 [exp_exposure_start, exp_exposure_finish],
                 [exp_comment],
                 [exp_type],
                 [exp_script],
                 [exp_btn]])
    elif hdr_type.value == 'Observation':
        input_layout = layout([
                 [exp_time],
                 [exp_exposure_start, exp_exposure_finish],
                 [exp_comment],
                 [exp_tile_type],
                 [exp_tile],
                 [exp_btn]])       

    layout2.children[4] = input_layout

def progress_add():
    data = [hdr_type.value, get_time(exp_time.value), exp_comment.value, exp_exposure_start.value, exp_exposure_finish.value, 
            exp_type.value, exp_script.value, get_time(exp_time_end.value), exp_focus_trim.value, exp_tile.value, exp_tile_type.value]
    DESI_Log.add_exposure(data)


    clear_input([exp_time, exp_comment, add_image, exp_exposure_start, exp_exposure_finish, exp_type, exp_script,
                exp_time_end, exp_focus_trim, exp_tile, exp_tile_type])


# TAB3: Weather
subtitle_3 = Div(text='''<font size="3">Weather</font> ''', width=500)

def init_weather_source_data():
    """Creates a table with pre-identified Times for weather input
    """
    data = pd.DataFrame(columns = ['time','desc','temp','wind','humidity'])
    hours = [17,18,19,20,21,22,23,24,1,2,3,4,5,6,7]
    data['time'] = [("%s:00" % str(hour).zfill(2)) for hour in hours]
    return ColumnDataSource(data)

weather_source = init_weather_source_data()
columns = [TableColumn(field='time', title='Time UTC', width=100),
           TableColumn(field='desc', title='Description', width=200, editor=StringEditor()),
           TableColumn(field='temp', title='Temperature (C)', width=100, editor=NumberEditor()),
           TableColumn(field='wind', title='Wind Speed (mph)', width=100, editor=NumberEditor()),
           TableColumn(field='humidity', title='Humidity (%)', width=100, editor=PercentEditor())]

weather_table = DataTable(source=weather_source, columns=columns, editable=True,
              sortable=False, reorderable=False, fit_columns=False,
              min_width=1300, sizing_mode='stretch_width')
weather_btn = Button(label='Update NightLog', button_type='primary')

def update_weather_source_data():
    """Adds initial input to weather table
    """
    new_data = pd.DataFrame(weather_source.data.copy())
    sunset_time = datetime.strptime(get_time(time_sunset.value),"%Y%m%dT%H:%M")   
    sunset_hour = sunset_time.hour 
    idx = new_data[new_data.time == "%s:00"%(str(sunset_hour).zfill(2))].index[0]
    new_data.at[idx,'desc'] = sunset_weather.value
    del new_data['index']

    weather_source.data = new_data

def weather_add():
    """Adds table to Night Log
    """
    data = pd.DataFrame(weather_source.data)
    DESI_Log.add_weather_os(data)

# TAB4: Problems
subtitle_4 = Div(text='''<font size="3">Problems</font> ''', width=500)
prob_time = TextInput(title ='Time', placeholder = '2007', value=None)
prob_input = TextAreaInput(placeholder="description", rows=6, title="Problem Description:")
prob_btn = Button(label='Add', button_type='primary')

def prob_add():
    """Adds problem to nightlog
    """
    DESI_Log.add_problem(get_time(prob_time.value),prob_input.value,'OS')
    clear_input([prob_time, prob_input])


# TAB5: Checklists
subtitle_6 = Div(text='''<font size="3">OS Checklist</font> ''', width=500)
os_checklist = CheckboxGroup(
        labels=["Did you check the weather?", "Did you check the guiding?", "Did you check the focal plane?","Did you check the spectrographs?"])
check_time = TextInput(title ='Time', placeholder = '2007', value=None)
check_txt = Div(text=" ")
check_btn = Button(label='Submit', button_type='primary')

def check_add():
    """add checklist time to Night Log
    """
    complete = os_checklist.active 
    if len(complete) == 4:
      if check_time.value is not None:
        DESI_Log.add_to_checklist(get_time(check_time.value), 'OS')
        check_txt.text = "Checklist last submitted at {}".format(check_time.value)
      else:
        check_txt.text = "Must input a valid time to submit checklist"
    else:
      check_txt.text = "Must complete all tasks before submitting checklist"
    clear_input(check_time)
    os_checklist.active = []

# TAB6: Current Night Log
subtitle_5 = Div(text='''<font size="3">Current Night Log</font> ''', width=500)
nl_btn = Button(label='Get Current Night Log', button_type='primary')
nl_text = Div(text='''Current Night Log''',width=1000)

def current_nl():
    """Return the current Night Log
    """
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
exp_btn.on_click(progress_add)
hdr_btn.on_click(choose_exposure)
weather_btn.on_click(weather_add)
prob_btn.on_click(prob_add)
nl_btn.on_click(current_nl)
check_btn.on_click(check_add)

layout1 = layout([[title],
                 [page_logo, instructions],
                 [subtitle_1],
                 [info_1],
                 [time_select],
                 [date_input,connect_bt],
                 [[your_firstname, your_lastname], [LO_firstname, LO_lastname],[OA_firstname, OA_lastname]],
                 [[time_sunset,time_sunrise],[time_18_deg_twilight_ends,time_18_deg_twilight_starts],[time_moonrise,time_moonset],
                 [illumination,sunset_weather]],
                 [init_bt],
                 [info_connect]
                 ])
tab1 = Panel(child=layout1, title="Initialization")

layout2 = layout(children = [[title],
                 [subtitle_2],
                 [info_2],
                 [hdr_type, hdr_btn],
                 [input_layout]
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
                [check_time, check_btn],
                [check_txt]])
tab6 = Panel(child=layout6, title="OS Checklist")

tabs = Tabs(tabs=[ tab1, tab2 , tab3, tab4, tab6, tab5])

curdoc().title = 'DESI Night Log - Operations Scientist'
curdoc().add_root(tabs)
