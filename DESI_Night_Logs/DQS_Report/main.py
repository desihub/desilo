"""
Created on May 21, 2020

@author: Parker Fagrelius

start server with the following command from folder above this.

bokeh serve --show DQS_Report

view at: http://localhost:5006/DQS_Report
"""


#Imports
import os, sys
from datetime import datetime
import numpy as np

from bokeh.io import curdoc  # , output_file, save
from bokeh.models import (TextInput, ColumnDataSource, Button, RadioGroup, TextAreaInput, Select,  Span, CheckboxGroup, RadioButtonGroup)
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
    date = date_init.value
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

# INITIALIZE NIGHT LOG
title = Div(text="DESI Night Intake - Data QA Scientist", width=600,style = {'font-family':'serif','font-size':'250%'})
page_logo = Div(text="<img src='DQS_Report/static/logo.png'>", width=350, height=300)
instructions = Div(text="The Data Quality Scientist (DQS) is responsible for analyzing all exposures for their quality. You can connect to an existing Night Log that was created by the Observing Scientist. ",width=500,style=inst_style)


subtitle_1 = Div(text="Connect to Night Log",width=500,style=subt_style)
info_1 = Div(text="Time Formats: 6:18pm = 18:18 = 1818. You can use any of these formats. <b>Input all times in Local Kitt Peak time.</b> When you input the date and your name, press the blue button. All relevant Night Log meta data will be displayed below.",width=800,style=inst_style)
#date_input = TextInput(title ='DATE', value = datetime.now().strftime("%Y%m%d"))

your_name = TextInput(title ='Your Name', placeholder = 'John Smith')

date_init = Select(title="Initialized Night Logs")
days = os.listdir('nightlogs')
init_nl_list = np.sort([day for day in days if 'nightlog_meta.json' in os.listdir('nightlogs/'+day)])[::-1][0:10]
date_init.options = list(init_nl_list)
date_init.value = init_nl_list[0]
init_bt = Button(label="Connect to Night Log", button_type='primary',width=300)
connect_txt = Div(text=' ', width=600, style={'font-family':'serif','font-size':'125%','color':'red'})

nl_info = Div(text="Night Log Info (this will populate when you've connected to an initialized NightLog)", width=500,style=inst_style)
os_name = TextInput(title ='OS Name')
LO_name = TextInput(title ='LO Name')
OA_name = TextInput(title ='OA Name')
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
        date = datetime.strptime(date_init.value, '%Y%m%d')
    except:
        date = datetime.now()
    global DESI_Log
    DESI_Log=nl.NightLog(str(date.year),str(date.month).zfill(2),str(date.day).zfill(2))
    exists = DESI_Log.check_exists()

    your_firstname, your_lastname = your_name.value.split(' ')[0], ' '.join(your_name.value.split(' ')[1:])
    if exists:
      connect_txt.text = 'Connected to Night Log for {}'.format(date_init.value)
      DESI_Log.add_dqs_observer(your_firstname, your_lastname)
      meta_dict = DESI_Log.get_meta_data()

      your_name.value = meta_dict['dqs_1']+' '+meta_dict['dqs_last']
      os_name.value = meta_dict['os_1']+' '+meta_dict['os_last']
      LO_name.value = meta_dict['os_lo_1']+' '+meta_dict['os_lo_last']
      OA_name.value = meta_dict['os_oa_1']+' '+meta_dict['os_oa_last']
      time_sunset.value = short_time(meta_dict['os_sunset'])
      time_18_deg_twilight_ends.value = short_time(meta_dict['os_end18'])
      time_18_deg_twilight_starts.value = short_time(meta_dict['os_start18'])
      time_sunrise.value = short_time(meta_dict['os_sunrise'])
      time_moonrise.value = short_time(meta_dict['os_moonrise'])
      time_moonset.value = short_time(meta_dict['os_moonset'])
      illumination.value = meta_dict['os_illumination']
      sunset_weather.value = meta_dict['os_weather_conditions']
    else:
      connect_txt.text = 'The Night Log for this {} is not yet initialized.'.format(date_init.value)


#EXPOSURES
subtitle_2 = Div(text="Exposures",width=500, style=subt_style)
exp_inst = Div(text="For each exposure, collect information about what you observe on Night Watch (quality) and observing conditions using other tools", width=800, style=inst_style)
info_2 = Div(text="Fill In Only Relevant Data",width=500, style=inst_style)

exp_time = TextInput(title ='Time', placeholder = '2007',value=None)

exp_exposure_start = TextInput(title ='Exposure Number: First', placeholder = '12345',value = None)
exp_exposure_finish = TextInput(title ='Exposure Number: Last', placeholder = '12345',value = None)

exp_type = Select(title="Exposure Type", value = None, options=['None','Zero','Focus','Dark','Arc','FVC','DESI'])
quality_title = Div(text='Data Quality: ', style=inst_style)
quality_btns = RadioGroup(labels=['Bad','OK','Good','Great'],active=2)
exp_comment = TextInput(title ='Data Quality Comment/Remark', placeholder = 'Data Quality good',value=None)
obs_cond_comment = TextInput(title ='Observing Conditions Comment/Remark', placeholder = 'Seeing stable at 0.8arcsec',value=None)
inst_perf_comment = TextInput(title ='Instrument Performance Comment/Remark', placeholder = 'Positioner Accuracy less than 10um',value=None)
exp_btn = Button(label='Add', button_type='primary')
exp_alert = Div(text=' ', width=600, style=inst_style)


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
    exp_alert.text = 'Last Exposure input {} at {}'.format(exp_exposure_start.value, exp_time.value)
    clear_input([exp_time, exp_exposure_start, exp_type, exp_comment, obs_cond_comment, inst_perf_comment, exp_exposure_finish])


#Problems
subtitle_3 = Div(text="Problems", width=500, style=subt_style)
prob_inst = Div(text="Describe problems as they come up and at what time they occur. If possible, include a description of the remedy.", width=800, style=inst_style)
prob_time = TextInput(title ='Time', placeholder = '2007', value=None)
prob_input = TextAreaInput(placeholder="NightWatch not plotting raw data", rows=6, title="Problem Description:")
prob_alarm = TextInput(title='Alarm ID', placeholder='12', value=None)
prob_action = TextAreaInput(title='Resolution/Action',placeholder='description',rows=6)
prob_btn = Button(label='Add', button_type='primary')
prob_alert = Div(text=' ', width=600,style=inst_style)

def prob_add():
    """Adds problem to nightlog
    """
    DESI_Log.add_problem(get_time(prob_time.value),prob_input.value,prob_alarm.value, prob_action.value,'DQS')
    prob_alert.text = "Last Problem Input: '{}' at {}".format(prob_input.value, prob_time.value)
    clear_input([prob_time, prob_input, prob_alarm, prob_action])


# CHECKLISTS
subtitle_6 = Div(text="DQS Checklist", width=500, style=subt_style)
checklist_inst = Div(text="Every hour, the OS is expected to monitor several things. After completing these tasks, record at what time they were completed. Be honest please!", width=800, style=inst_style )
os_checklist = CheckboxGroup(
        labels=["Are all images being transferred to Night Watch?","Did you check the observing conditions?", "Did you check the guiding?"])
check_time = TextInput(title ='Time', placeholder = '2007', value=None)
check_txt = Div(text=" ", width=800, style=inst_style)
check_btn = Button(label='Submit', button_type='primary')

def check_add():
    """add checklist time to Night Log
    """
    complete = os_checklist.active
    if len(complete) == 3:
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
subtitle_5 = Div(text="Current DESI Night Log", width=500, style=subt_style)
nl_btn = Button(label='Get Current DESI Night Log', button_type='primary')
nl_text = Div(text="Current DESI Night Log",width=500, style=inst_style)
nl_alert = Div(text=' ',width=600, style=inst_style)

def current_nl():
    now = datetime.now()
    DESI_Log.finish_the_night()
    path = "nightlogs/"+DESI_Log.obsday+"/nightlog.html"
    nl_file = open(path,'r')
    nl_txt = ''
    for line in nl_file:
        nl_txt =  nl_txt + line + '\n'
    nl_text.text = nl_txt
    nl_file.closed
    nl_alert.text = 'Last Updated on this page: {}'.format(now)




# Layouts and Actions on Bokeh Page

init_bt.on_click(initialize_log)
exp_btn.on_click(exp_add)
prob_btn.on_click(prob_add)
check_btn.on_click(check_add)
nl_btn.on_click(current_nl)

layout1 = layout([[title],
                 [page_logo, instructions],
                 [subtitle_1],
                 [info_1],
                 [date_init, your_name],
                 [init_bt],
                 [connect_txt],
                 [nl_info],
                 [[os_name], [LO_name],[OA_name]],
                 [[time_sunset,time_sunrise],[time_18_deg_twilight_ends,time_18_deg_twilight_starts],[time_moonrise,time_moonset],
                 [illumination,sunset_weather]]
                 ])
tab1 = Panel(child=layout1, title="Initialization")

layout2 = layout([[title],
                 [subtitle_2],
                 [exp_inst],
                 [info_2],
                 [exp_time],
                 [exp_exposure_start, exp_exposure_finish],
                 [exp_type],
                 [quality_title,quality_btns],
                 [exp_comment],
                 [obs_cond_comment],
                 [inst_perf_comment],
                 [exp_btn],
                 [exp_alert]
                 ])
tab2 = Panel(child=layout2, title="Exposures")


layout3 = layout([[title],
                 [subtitle_3],
                 [prob_inst],
                 [prob_time, prob_input],
                 [prob_alarm, prob_action],
                 [prob_btn],
                 [prob_alert]
                 ])
tab3 = Panel(child=layout3, title="Problems")

layout6 = layout([[title],
                [subtitle_6],
                [checklist_inst],
                [os_checklist],
                [check_time, check_btn],
                [check_txt]])
tab6 = Panel(child=layout6, title="DQS Checklist")

layout5 = layout([[title],
                [subtitle_5],
                [nl_btn, nl_alert],
                [nl_text]])
tab5 = Panel(child=layout5, title="Current DESI Night Log")

tabs = Tabs(tabs=[tab1, tab2, tab3, tab6, tab5])

curdoc().title = 'DESI Night Log - Data QA Scientist'
curdoc().add_root(tabs)
