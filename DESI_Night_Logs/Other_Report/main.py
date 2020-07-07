"""
Created on May 21, 2020

@author: Parker Fagrelius

Other Observer to see Ongoing Night Log

start server with the following command:

bokeh serve --show bk_other.py

view at: http://localhost:5006/bk_other
"""


#Imports
import os, sys
from datetime import datetime

from bokeh.io import curdoc  # , output_file, save
from bokeh.models import (TextInput, ColumnDataSource, Paragraph, Button, TextAreaInput, Select)
from bokeh.models.widgets.markups import Div
from bokeh.layouts import layout
from bokeh.models.widgets import Panel, Tabs
from astropy.time import TimezoneInfo
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

inst_style = {'font-family':'serif','font-size':'150%'}
subt_style = {'font-family':'serif','font-size':'200%'}

title = Div(text="DESI Night Log - Non Observer", width=800,style = {'font-family':'serif','font-size':'250%'})
page_logo = Div(text="<img src='Other_Report/static/logo.png'>", width=450, height=400)
instructions = Div(text="This Night Log is for Non-Observers. It should mainly be used for observing the ongoing Night Log. In special circumstances, if a non-observer has an important comment about an exposure or problem, it can be added here. Before doing so, make sure to communicate with the Observing Scientist. ",width=500, style=inst_style)
#Initialize Night Log Info
subtitle_1 = Div(text="Connect to Night Log",width=500,style=subt_style)
info_1 = Div(text="Time Formats: 6:18pm = 18:18 = 1818. You can use any of these formats. <b>Input all times in Local Kitt Peak time.</b>\n",width=800, style=inst_style)
date_input = TextInput(title ='DATE', value = datetime.now().strftime("%Y%m%d"))

your_name = TextInput(title ='Your Name', placeholder = 'John Doe')

init_bt = Button(label="Connect to Night Log", button_type='primary',width=300)

nl_info = Paragraph(text="""Night Log Info""", width=500)

os_firstname = TextInput(title ='Observing Scientist Name')
os_lastname = TextInput()
LO_firstname = TextInput(title ='Lead Observer Name')
LO_lastname = TextInput()
OA_firstname = TextInput(title ='Observing Assistant Name')
OA_lastname = TextInput()
DQS_firstname = TextInput(title= 'Data QA Scientist')
DQS_lastname = TextInput()
time_sunset = TextInput(title ='Time of Sunset')
time_18_deg_twilight_ends = TextInput(title ='Time 18 deg Twilight Ends')
time_18_deg_twilight_starts = TextInput(title ='Time 18 deg Twilight Ends')
time_sunrise = TextInput(title ='Time of Sunrise')
time_moonrise = TextInput(title ='Time of Moonrise')
time_moonset = TextInput(title ='Time of Moonset')
illumination = TextInput(title ='Moon Illumination')
sunset_weather = TextInput(title ='Weather conditions as sunset')

#TAB2
subtitle_2 = Div(text="Comments",width=500, style=subt_style)
comment_txt = Div(text=" ",width=500,style=inst_style)
exp_time = TextInput(title ='Time', placeholder = '2007',value=None)
exp_comment = TextAreaInput(title ='Data Quality Comment/Remark', placeholder = 'Data Quality good',value=None)
exp_btn = Button(label='Add', button_type='primary')


#TAB3 - Problems
subtitle_3 = Div(text="Problems", width=500, style=subt_style)
problem_txt = Div(text=" ", width=500, style=inst_style)
prob_time = TextInput(title ='Time', placeholder = '2007', value=None)
prob_input = TextAreaInput(placeholder="NightWatch not plotting raw data", rows=6, title="Problem Description:")
prob_btn = Button(label='Add', button_type='primary')

#TAB4 - Display Current Night Log
subtitle_5 = Div(text="Current Night Log", width=500, style=subt_style)
nl_btn = Button(label='Get Current Night Log', button_type='primary')
nl_text = Div(text="Current Night Log",width=500,style = inst_style)



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
    exists = DESI_Log.check_exists()
    if exists:
        nl_info.text = "Connected to Night Log for {}".format(date_input.value)
        meta_dict = DESI_Log.get_meta_data()
        os_firstname.value = meta_dict['os_1']
        os_lastname.value = meta_dict['os_last']
        LO_firstname.value = meta_dict['os_lo_1']
        LO_lastname.value = meta_dict['os_lo_last']
        OA_firstname.value = meta_dict['os_oa_1']
        OA_lastname.value = meta_dict['os_oa_last']
        DQS_firstname.value = meta_dict['dqs_1']
        DQS_lastname.value = meta_dict['dqs_last']
        time_sunset.value = short_time(meta_dict['os_sunset'])
        time_18_deg_twilight_ends.value = short_time(meta_dict['os_end18'])
        time_18_deg_twilight_starts.value = short_time(meta_dict['os_start18'])
        time_sunrise.value = short_time(meta_dict['os_sunrise'])
        time_moonrise.value = short_time(meta_dict['os_moonrise'])
        time_moonset.value = short_time(meta_dict['os_moonset'])
        illumination.value = meta_dict['os_illumination']
        sunset_weather.value = meta_dict['os_weather_conditions']
    else:
        nl_info.text = "No Night Log exists for {} at this time".format(date_input.value)

def exp_add():
    """
    Function to add line about an exposure sequence in the Night Log
    """
    if your_name.value in [None,' ','']:
        comment_txt.text = 'You need to enter your name on first page before submitting a comment'
    else:
        DESI_Log.add_comment_other(get_time(exp_time.value), exp_comment.value, your_name.value)
        clear_input([exp_time, exp_comment])
        comment_txt.text = "Currently this is not being published to the Night Log."

def prob_add():
    # Currently no code in jupyter notebook
    if your_name.value == [None,' ','']:
        problem_txt.text = 'You need to enter your name on first page before submitting a comment'
    else:
        DESI_Log.add_problem(get_time(prob_time.value), prob_input.value, "Other")
        clear_input([prob_time, prob_input])
        problem_txt.text = "Currently this is not being published to the Night Log."

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
                 [instructions,page_logo],                 
                 [subtitle_1],
                 [info_1],
                 [date_input, your_name],
                 [init_bt],
                 [nl_info],
                 [[os_firstname, os_lastname], [LO_firstname, LO_lastname],[OA_firstname, OA_lastname], [DQS_firstname,DQS_lastname]],
                 [[time_sunset,time_sunrise],[time_18_deg_twilight_ends,time_18_deg_twilight_starts],[time_moonrise,time_moonset],
                 [illumination,sunset_weather]]
                 ])
tab1 = Panel(child=layout1, title="Initialization")

layout2 = layout([[title],
                 [subtitle_2],
                 [comment_txt],
                 [exp_time],
                 [exp_comment],
                 [exp_btn]
                 ])
tab2 = Panel(child=layout2, title="Comments")


layout4 = layout([[title],
                 [subtitle_3],
                 [problem_txt],
                 [prob_time, prob_input],
                 [prob_btn]
                 ])
tab4 = Panel(child=layout4, title="Problems")

layout5 = layout([[title],
                [subtitle_5],
                [nl_btn],
                [nl_text]])
tab5 = Panel(child=layout5, title="Current Night Log")

tabs = Tabs(tabs=[tab1, tab5, tab2, tab4])

curdoc().title = 'DESI Night Log - Non Observer'
curdoc().add_root(tabs)
