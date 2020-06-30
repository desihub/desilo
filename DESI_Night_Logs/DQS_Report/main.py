"""
Created on May 21, 2020

@author: Parker Fagrelius

start server with the following command:

bokeh serve --show bk_nl_dqs_input.py

view at: http://localhost:5006/bk_nl_dqs_input
"""


#Imports
import os, glob, sys
import numpy as np
import pandas as pd
from datetime import datetime

from bokeh.io import curdoc  # , output_file, save
from bokeh.plotting import figure, show, output_file
from bokeh.palettes import Magma256, Category10
from bokeh.models import (
    LinearColorMapper, ColorBar, AdaptiveTicker, TextInput, ColumnDataSource, Range1d,
    Title, Button, CheckboxButtonGroup, CategoricalColorMapper, Paragraph,DateFormatter,
    TextAreaInput, Select, PreText, Span, CheckboxGroup, RadioButtonGroup, RadioGroup)
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

sys.path.append(os.getcwd())

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
        print(item)
        item.value = None
    else:
      items.value = None

def get_time(time):
    """Returns strptime with utc. Takes time zone selection
    """  
    date = date_input.value
    zone = kp_zone #zones[time_select.active]
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
      zone = kp_zone #zones[time_select.active]
      time = datetime(t.year, t.month, t.day, t.hour, t.minute, tzinfo = zone)
      return "{}:{}".format(str(time.hour).zfill(2), str(time.minute).zfill(2))
    except:
      return str_time

# INITIALIZE NIGHT LOG
title = Div(text='''<font size="6">DESI Night Log - Data QA Scientist</font> ''',width=800)
page_logo = Div(text="<img src='OS_Report/static/logo.png'>", width=350, height=300)
instructions = Div(text="The Data Quality Scientist (DQS) is responsible for analyzing all exposures for their quality. You can connect to an existing Night Log that was created by the Observing Scientist. ",width=500)


subtitle_1 = Div(text='''<font size="3">Connect to Night Log</font> ''',width=500)
info_1 = Div(text='''<font size="2">Time Formats: 6:18pm = 18:18 = 1818. All times in Local Kitt Peak Time </font> ''',width=500)
date_input = TextInput(title ='DATE', value = datetime.now().strftime("%Y%m%d"))

your_firstname = TextInput(title ='Your Name', placeholder = 'John')
your_lastname = TextInput(placeholder = 'Smith')

init_bt = Button(label="Connect to Night Log", button_type='primary',width=300)

nl_info = Div(text="""Night Log Info""", width=300)
os_firstname = TextInput(title ='OS Name')
os_lastname = TextInput()
LO_firstname = TextInput(title ='LO Name')
LO_lastname = TextInput()
OA_firstname = TextInput(title ='OA Name')
OA_lastname = TextInput()
time_sunset = TextInput(title ='Time of Sunset')
time_18_deg_twilight_ends = TextInput(title ='Time 18 deg Twilight Ends')
time_18_deg_twilight_starts = TextInput(title ='Time 18 deg Twilight Ends')
time_sunrise = TextInput(title ='Time of Sunrise')
time_moonrise = TextInput(title ='Time of Moonrise')
time_moonset = TextInput(title ='Time of Moonset')
illumination = TextInput(title ='Moon Illumination')
sunset_weather = TextInput(title ='Weather conditions as sunset')

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

    DESI_Log.add_dqs_observer(your_firstname.value, your_lastname.value)
    
    meta_dict = DESI_Log.get_meta_data()

    your_firstname.value = meta_dict['dqs_1']
    your_lastname.value = meta_dict['dqs_last']
    os_firstname.value = meta_dict['os_1']
    os_lastname.value = meta_dict['os_last']
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



#EXPOSURES
subtitle_2 = Div(text='''<font size="4">Exposures</font> ''',width=500)
info_2 = Div(text='''<font size="2">Fill In Only Information Relevant</font> ''',width=500)

exp_time = TextInput(title ='Time', placeholder = '2007',value=None)

exp_exposure_start = TextInput(title ='Exposure Number: First', placeholder = '12345',value = None)
exp_exposure_finish = TextInput(title ='Exposure Number: Last', placeholder = '12345',value = None)

exp_type = Select(title="Exposure Type", value = None, options=['None','Zero','Focus','Dark','Arc','FVC','DESI'])
quality_title = Div(text='Data Quality: ')
quality_btns = RadioGroup(labels=['Bad','OK','Good','Great'],active=2)
exp_comment = TextInput(title ='Data Quality Comment/Remark', placeholder = 'Data Quality good',value=None)
obs_cond_comment = TextInput(title ='Observing Conditions Comment/Remark', placeholder = 'Seeing stable at 0.8arcsec',value=None)
inst_perf_comment = TextInput(title ='Instrument Performance Comment/Remark', placeholder = 'Positioner Accuracy less than 10um',value=None)
exp_btn = Button(label='Add', button_type='primary')


def exp_add():
    """
    Function to add line about an exposure sequence in the Night Log

    Note, I really don't like how this is currently implemented on my end, but I also don't really l
    ike that there are different functions for different types of inputs. I think we should have one kind of input,
    and if the value is None or Nan then it's not included. So, I'll clean up my side if we can have fewer functions
    for DESI_Log
    """
    q_list = ['Bad','OK','Good','Great']
    quality = q_list[quality_btns.active]
    DESI_Log.dqs_add_exp([get_time(exp_time.value), exp_exposure_start.value, exp_type.value, quality, exp_comment.value, obs_cond_comment.value, inst_perf_comment.value, exp_exposure_finish.value])
    clear_input([exp_time, exp_exposure_start, exp_type, exp_comment, obs_cond_comment, inst_perf_comment, exp_exposure_finish])


#Problems
subtitle_3 = Div(text='''<font size="3">Problems</font> ''', width=500)
prob_time = TextInput(title ='Time', placeholder = '2007', value=None)
prob_input = TextAreaInput(placeholder="NightWatch not plotting raw data", rows=6, title="Problem Description:")
prob_btn = Button(label='Add', button_type='primary')

def prob_add():
    """Adds problem to nightlog
    """
    DESI_Log.add_problem(get_time(prob_time.value),prob_input.value,'DQS')
    clear_input([prob_time, prob_input])

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

# CHECKLISTS
subtitle_6 = Div(text='''<font size="3">DQS Checklist</font> ''', width=500)
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
        DESI_Log.add_to_checklist(get_time(check_time.value), 'DQS')
        check_txt.text = "Checklist last submitted at {}".format(check_time.value)
      else:
        check_txt.text = "Must input a valid time to submit checklist"
    else:
      check_txt.text = "Must complete all tasks before submitting checklist"
    clear_input(check_time)
    os_checklist.active = []

# CURRENT NIGHT LOG
subtitle_5 = Div(text='''<font size="3">Current Night Log</font> ''', width=500)
nl_btn = Button(label='Get Current Night Log', button_type='primary')
nl_text = Div(text='''Current Night Log''',width=500)

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
exp_btn.on_click(exp_add)
prob_btn.on_click(prob_add)
check_btn.on_click(check_add)
nl_btn.on_click(current_nl)

layout1 = layout([[title],
                 [subtitle_1],
                 [page_logo, instructions],
                 [info_1],
                 [date_input, [your_firstname, your_lastname]],
                 [init_bt],
                 [nl_info],
                 [[os_firstname, os_lastname], [LO_firstname, LO_lastname],[OA_firstname, OA_lastname]],
                 [[time_sunset,time_sunrise],[time_18_deg_twilight_ends,time_18_deg_twilight_starts],[time_moonrise,time_moonset],
                 [illumination,sunset_weather]]
                 ])
tab1 = Panel(child=layout1, title="Initialization")

layout2 = layout([[title],
                 [subtitle_2],
                 [info_2],
                 [exp_time],
                 [exp_exposure_start, exp_exposure_finish],
                 [exp_type],
                 [quality_title,quality_btns],
                 [exp_comment],
                 [obs_cond_comment],
                 [inst_perf_comment],
                 [exp_btn]

                 ])
tab2 = Panel(child=layout2, title="Exposures")


layout3 = layout([[title],
                 [subtitle_3],
                 [prob_time, prob_input],
                 [prob_btn]
                 ])
tab3 = Panel(child=layout3, title="Problems")

layout6 = layout([[title],
                [subtitle_6],
                [os_checklist],
                [check_time, check_btn],
                [check_txt]])
tab6 = Panel(child=layout6, title="DQS Checklist")

layout5 = layout([[title],
                [subtitle_5],
                [nl_btn],
                [nl_text]])
tab5 = Panel(child=layout5, title="Current Night Log")

tabs = Tabs(tabs=[ tab1, tab2 , tab3, tab6, tab5])

curdoc().title = 'DESI Night Log - Data QA Scientist'
curdoc().add_root(tabs)
