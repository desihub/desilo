"""
Created on May 21, 2020

@author: Parker Fagrelius

Other Observer to see Ongoing Night Log

start server with the following command:

bokeh serve --show bk_other.py

view at: http://localhost:5006/bk_other
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
    TextAreaInput, Select, PreText, Span)
from bokeh.models.widgets.markups import Div
from bokeh.models.widgets.tables import (
    DataTable, TableColumn, SelectEditor, IntEditor, NumberEditor, StringEditor,PercentEditor)
from bokeh.layouts import column, layout
from bokeh.palettes import d3
from bokeh.client import push_session
from bokeh.models.widgets import Panel, Tabs


import nightlog as nl

title = Div(text='''
<font size="4">DESI Night Log - Other</font> ''',
            width=500)

#Initialize Night Log Info
subtitle_1 = Div(text='''<font size="3">Connect to Night Log</font> ''',width=500)
info_1 = Div(text='''<font size="2">Time Formats: 6:18pm = 18:18 = 1818. All times in Local Time </font> ''',width=500)
date_input = TextInput(title ='DATE', value = datetime.now().strftime("%Y%m%d"))

your_firstname = TextInput(title ='Your Name', placeholder = 'John')
your_lastname = TextInput(placeholder = 'Smith')

init_bt = Button(label="Connect to Night Log", button_type='primary',width=300)

nl_info = Paragraph(text="""Night Log Info""", width=500,height=200)

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


subtitle_2 = Div(text='''<font size="3">Comments</font> ''',width=500)
info_2 = Div(text='''<font size="2">Fill In Only Information Relevant</font> ''',width=500)
exp_time = TextInput(title ='Time', placeholder = '2007',value=None)
exp_comment = TextAreaInput(title ='Data Quality Comment/Remark', placeholder = 'Data Quality good',value=None)
exp_btn = Button(label='Add', button_type='primary')


#Problems
subtitle_3 = Div(text='''<font size="3">Problems</font> ''', width=500)
prob_time = TextInput(title ='Time', placeholder = '2007', value=None)
prob_input = TextAreaInput(placeholder="NightWatch not plotting raw data", rows=6, title="Problem Description:")
prob_btn = Button(label='Add', button_type='primary')

#Display Current Night Log
subtitle_5 = Div(text='''<font size="3">Current Night Log</font> ''', width=500)
nl_btn = Button(label='Get Current Night Log', button_type='primary')
nl_text = Div(text='''Current Night Log''',width=500)



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
    nl_info.text = DESI_Log.check_exists()

    DESI_Log.add_dqs_observer(your_firstname.value, your_lastname.value)
    meta_dict = DESI_Log.get_meta_data()
    os_firstname.value = meta_dict['os_1']
    os_lastname.value = meta_dict['os_last']
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




def exp_add():
    """
    Function to add line about an exposure sequence in the Night Log
    
    Note, I really don't like how this is currently implemented on my end, but I also don't really l
    ike that there are different functions for different types of inputs. I think we should have one kind of input, 
    and if the value is None or Nan then it's not included. So, I'll clean up my side if we can have fewer functions
    for DESI_Log
    """
    pass

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
exp_btn.on_click(exp_add)
prob_btn.on_click(prob_add)
nl_btn.on_click(current_nl)

layout1 = layout([[title],
                 [subtitle_1],
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
                 [exp_comment],
                 [exp_btn]
                 ])
tab2 = Panel(child=layout2, title="Comments")


layout4 = layout([[title],
                 [subtitle_3],
                 [prob_time, prob_input],
                 [prob_btn]
                 ])
tab4 = Panel(child=layout4, title="Problems")

layout5 = layout([[title],
                [subtitle_5],
                [nl_btn],
                [nl_text]])
tab5 = Panel(child=layout5, title="Current Night Log")

tabs = Tabs(tabs=[ tab1, tab5, tab2 , tab4])

curdoc().title = 'DESI Night Log - Operations Scientist'
curdoc().add_root(tabs)
