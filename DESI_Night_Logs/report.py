#Imports
import os, sys
import glob
import time, sched
import datetime 
from collections import OrderedDict
import numpy as np
import pandas as pd
import socket
import psycopg2
import subprocess
import pytz
import json

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from bokeh.io import curdoc  # , output_file, save
from bokeh.models import (TextInput, ColumnDataSource, DateFormatter, RadioGroup,Paragraph, Button, TextAreaInput, Select,CheckboxGroup, RadioButtonGroup, DateFormatter)
from bokeh.models.widgets.markups import Div
from bokeh.layouts import layout, column, row
from bokeh.models.widgets import Panel, Tabs, FileInput
from bokeh.models.widgets.tables import DataTable, TableColumn
from bokeh.plotting import figure
from astropy.time import TimezoneInfo
import astropy.units.si as u

from util import sky_calendar

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

sys.path.append(os.getcwd())
sys.path.append('./ECLAPI-8.0.12/lib')
import nightlog as nl

os.environ['NL_DIR'] = '/software/www2/html/nightlogs'
os.environ['NW_DIR'] = '/exposures/nightwatch/'

#os.environ['NL_DIR'] = '/n/home/desiobserver/parkerf/desilo/nightlogs'
#os.environ['NW_DIR'] = '/exposures/nightwatch/'

class Report():
    def __init__(self, type):

        self.test = False 

        self.report_type = type
        self.kp_zone = TimezoneInfo(utc_offset=-7*u.hour)

        self.datefmt = DateFormatter(format="%m/%d/%Y %H:%M:%S")
        self.timefmt = DateFormatter(format="%m/%d %H:%M")

        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        if 'desi' in hostname:
            self.location = 'kpno'
            self.conn = psycopg2.connect(host="desi-db", port="5442", database="desi_dev", user="desi_reader", password="reader")
        elif 'app' in hostname: #this is not true. Needs to change.
            self.location = 'nersc'
            self.conn = psycopg2.connect(host="db.replicator.dev-cattle.stable.spin.nersc.org", port="60042", database="desi_dev", user="desi_reader", password="reader")
        else:
            self.location = 'nersc'

        nw_dirs = {'nersc':'/global/cfs/cdirs/desi/spectro/nightwatch/nersc/', 'kpno':'/exposures/nightwatch/', 'other':None}
        self.nw_dir = os.environ['NW_DIR'] #nw_dirs[self.location]
        self.nl_dir = os.environ['NL_DIR']     

        self.intro_subtitle = Div(text="Connect to Night Log", css_classes=['subt-style'])
        self.time_note = Div(text="<b> Note: </b> Enter all times as HH:MM (18:18 = 1818 = 6:18pm) in Kitt Peak local time. Either enter the time or hit the <b> Now </b> button if it just occured.", css_classes=['inst-style'])
        self.exp_info = Div(text="Mandatory fields have an asterisk*.", css_classes=['inst-style'],width=500)
        
        self.img_upinst = Div(text="Include images in the Night Log by uploading a png image from your local computer. Select file, write a comment and click Add", css_classes=['inst-style'], width=1000)
        self.img_upinst2 = Div(text="           Choose image to include with comment:  ", css_classes=['inst-style'])
        self.img_upload = FileInput(accept=".png")
        self.img_upload.on_change('value', self.upload_image)

        self.img_upload_comments_os = FileInput(accept=".png")
        self.img_upload_comments_os.on_change('value', self.upload_image_comments_os)
        self.img_upload_comments_dqs = FileInput(accept=".png")
        self.img_upload_comments_dqs.on_change('value', self.upload_image_comments_dqs)
        self.img_upload_problems = FileInput(accept=".png")
        self.img_upload_problems.on_change('value', self.upload_image_problems)

        self.nl_file = None
        self.milestone_time = None
        self.plan_time = None
        self.full_time = None

        self.DESI_Log = None
        self.save_telem_plots =True 
        self.buffer = Div(text=' ')


    def clear_input(self, items):
        """ After submitting something to the log, this will clear the form.
        """
        if isinstance(items, list):
            for item in items:
                item.value = ' '
        else:
            items.value = ' '

    def get_exposure_list(self):
        
        try:
            current_exp = self.exp_select.value
            dir_ = os.path.join(self.nw_dir,self.night)
            exposures = []
            for path, subdirs, files in os.walk(dir_): 
                for s in subdirs: 
                    exposures.append(s)  
            x = list([str(int(e)) for e in list(exposures)])
            x = np.sort(x)[::-1]
            self.exp_select.options = list(x) 
            self.exp_select.value = current_exp 
        except:
            self.exp_select.options = []

    def update_nl_list(self):
        days = [f for f in os.listdir(self.nl_dir) if os.path.isdir(os.path.join(self.nl_dir,f))]
        init_nl_list = np.sort([day for day in days if 'OperationsScientist' in os.listdir(os.path.join(self.nl_dir,day))])[::-1][0:10]
        init_nl_list = [x for x in init_nl_list if x > '20210326']
        self.date_init.options = list(init_nl_list)
        self.date_init.value = init_nl_list[0]

    def get_intro_layout(self):

        self.connect_txt = Div(text=' ', css_classes=['alert-style'])
        self.intro_txt = Div(text=' ')
        self.comment_txt = Div(text=" ", css_classes=['inst-style'], width=1000)

        self.connect_bt = Button(label="Connect to Existing Night Log", css_classes=['connect_button'])
        self.nl_info = Div(text="Night Log Info:", css_classes=['inst-style'], width=500) 

        self.your_name = TextInput(title ='Your Name', placeholder = 'John Smith')

        self.date_init = Select(title="Existing Night Logs")
        self.time_title = Paragraph(text='Time* (Kitt Peak local time)', align='center')
        self.now_btn = Button(label='Now', css_classes=['now_button'], width=75)

        self.full_time_text = Div(text='Total time between 18 deg. twilights (hrs): ', width=100) #Not on intro slide, but needed across reports

        self.update_nl_list()

        self.line = Div(text='-----------------------------------------------------------------------------------------------------------------------------', width=1000)
        self.line2 = Div(text='-----------------------------------------------------------------------------------------------------------------------------', width=1000)

        intro_layout = layout([self.buffer,
                            self.title,
                            [self.page_logo, self.instructions],
                            self.intro_subtitle,
                            [self.date_init, self.your_name],
                            [self.connect_bt],
                            self.connect_txt,
                            self.nl_info,
                            self.intro_txt], width=1000)
        self.intro_tab = Panel(child=intro_layout, title="Initialization")

    def get_plan_layout(self):
        self.plan_subtitle = Div(text="Night Plan", css_classes=['subt-style'])
        inst = """<ul>
        <li>Add the major elements of the night plan found at the link below in the order expected for their completion using the <b>Add/New</b> button. Do NOT enter an index for new items - they will be generated.</li>
        <li>You can recall submitted plans using their index, as found on the Current DESI Night Log tab.</li>
        <li>If you'd like to modify a submitted plan item, <b>Load</b> the index (these can be found on the Current NL), make your modifications, and then press <b>Update</b>.</li>
        </ul>
        """
        self.plan_inst = Div(text=inst, css_classes=['inst-style'], width=1000)
        self.plan_txt = Div(text='<a href="https://desi.lbl.gov/trac/wiki/DESIOperations/ObservingPlans/">Tonights Plan Here</a>', css_classes=['inst-style'], width=500)
        self.plan_order = TextInput(title ='Plan Index (see Current NL):', placeholder='0', width=75)
        self.plan_input = TextAreaInput(placeholder="description", rows=5, cols=3, title="Enter item of the night plan:",max_length=5000, width=800)
        self.plan_btn = Button(label='Update', css_classes=['add_button'], width=75)
        self.plan_new_btn = Button(label='Add New', css_classes=['add_button'])
        self.plan_load_btn = Button(label='Load', css_classes=['connect_button'], width=75)
        self.plan_alert = Div(text=' ', css_classes=['alert-style'])

        plan_layout = layout([self.buffer,
                    self.title,
                    self.plan_subtitle,
                    self.plan_inst,
                    self.plan_txt,
                    [self.plan_input, [self.plan_order, self.plan_load_btn, self.plan_btn]],
                    [self.plan_new_btn],
                    self.plan_alert], width=1000)
        self.plan_tab = Panel(child=plan_layout, title="Night Plan")



    def get_milestone_layout(self):
        self.milestone_subtitle = Div(text="Milestones & Major Accomplishments", css_classes=['subt-style'])
        inst = """<ul>
        <li>Record any major milestones or accomplishments that occur throughout a night. These should correspond with the major elements input on the 
        <b>Plan</b> tab. Include exposure numbers that correspond with the accomplishment, and if applicable, indicate any exposures to ignore in a series.
        Do NOT enter an index for new items - they will be generated.</li>
        <li>If you'd like to modify a submitted milestone, <b>Load</b> the index (these can be found on the Current NL), make your modifications, and then press <b>Update</b>.</li>
        <li>At the end of your shift - either at the end of the night or half way through - summarize the activities of the night in the <b>End of Night Summary</b>.
        There is space for a night summary for the first half and the second half of the night. DO NOT delete what already exists.</li>
        <li>At the end of the night, record how many hours of the night were spent observing <b>(ObsTime)</b>, lost to testing <b>(TestTime)</b>, lost to issues with the
        instrument <b>(InstTime)</b>, lost due to weather <b>(WeathTime)</b> or lost due to issues with the telescope <b>(TelTime)</b>. The times entered should sum to the time spent 
        "observing" during the night (i.e., if you started at 15 deg twi and ended and 12 deg twi, it should add up to that), but no less than the time between 18 deg twilights.</li>
        </ul>
        """
        self.milestone_inst = Div(text=inst, css_classes=['inst-style'],width=1000)
        self.milestone_input = TextAreaInput(placeholder="Description", title="Enter a Milestone:", rows=5, cols=3, max_length=5000, width=800)
        self.milestone_exp_start = TextInput(title ='Exposure Start', placeholder='12345',  width=200)
        self.milestone_exp_end = TextInput(title='Exposure End', placeholder='12345', width=200)
        self.milestone_exp_excl = TextInput(title='Excluded Exposures', placeholder='12346', width=200)
        self.milestone_btn = Button(label='Update', css_classes=['add_button'],width=75)
        self.milestone_new_btn = Button(label='Add New Milestone', css_classes=['add_button'], width=300)
        self.milestone_load_num = TextInput(title='Milestone Index', placeholder='0',  width=75)
        self.milestone_load_btn = Button(label='Load', css_classes=['connect_button'], width=75)
        self.milestone_alert = Div(text=' ', css_classes=['alert-style'])
        self.summary_1 = TextAreaInput(rows=10, placeholder='End of Night Summary for first half', title='End of Night Summary',max_length=5000)
        self.summary_2 = TextAreaInput(rows=10, placeholder='End of Night Summary for second half', max_length=5000)
        self.obs_time = TextInput(title ='ObsTime', placeholder='10', width=100)
        self.test_time = TextInput(title ='TestTime', placeholder='0', width=100)
        self.inst_loss_time = TextInput(title ='InstLoss', placeholder='0', width=100)
        self.weather_loss_time = TextInput(title ='WeathLoss', placeholder='0', width=100)
        self.tel_loss_time = TextInput(title ='TelLoss', placeholder='0', width=100)
        self.total_time = Div(text='Time Documented (hrs): ', width=100) #add all times together
        self.summary_btn = Button(label='Add Summary', css_classes=['add_button'], width=300)

        milestone_layout = layout([self.buffer,
                        self.title,
                        self.milestone_subtitle,
                        self.milestone_inst,
                        [self.milestone_input,[self.milestone_load_num, self.milestone_load_btn, self.milestone_btn]] ,
                        [self.milestone_exp_start,self.milestone_exp_end, self.milestone_exp_excl],
                        [self.milestone_new_btn],
                        self.milestone_alert,
                        self.line,
                        self.summary_1,
                        self.summary_2,
                        [self.obs_time, self.test_time, self.inst_loss_time, self.weather_loss_time, self.tel_loss_time, [self.total_time, self.full_time_text]],
                        self.summary_btn,
                        ], width=1000)
        self.milestone_tab = Panel(child=milestone_layout, title='Milestones')

    def exp_layout(self):
        self.exp_comment = TextAreaInput(title ='Comment/Remark', placeholder = 'Humidity high for calibration lamps',rows=10, cols=5,width=800,max_length=10000)
        self.exp_time = TextInput(placeholder = '20:07', width=100) #title ='Time in Kitt Peak local time*', 
        self.exp_btn = Button(label='Add/Update', css_classes=['add_button'])
        self.exp_load_btn = Button(label='Load', css_classes=['connect_button'], width=75)
        self.exp_alert = Div(text=' ', css_classes=['alert-style'])
        self.dqs_load_btn = Button(label='Load', css_classes=['connect_button'], width=75)

        self.exp_select = Select(title='(1) Select Exposure',options=['None'],width=150)
        self.exp_enter = TextInput(title='(2) Enter Exposure', placeholder='12345', width=150)
        self.exp_update = Button(label='Update Selection List', css_classes=['connect_button'], width=200)
        self.exp_option = RadioButtonGroup(labels=['(1) Select','(2) Enter'], active=0, width=200)
        self.os_exp_option = RadioButtonGroup(labels=['Time','Exposure'], active=0, width=200)

    def get_os_exp_layout(self):
        self.exp_layout()
        exp_subtitle = Div(text="Nightly Progress", css_classes=['subt-style'])
        inst="""<ul>
        <li>Throughout the night record the progress, including comments on calibrations and exposures. 
        All exposures are recorded in the eLog, so only enter information that can provide additional information.</li>
        <li> You can make a comment that is either associated with a <b>Time</b> or <b>Exposure</b>. Select which you will use.
        <ul class="square">
         <li> If you want to comment on a specific Exposure Number, the Night Log will include data from the eLog and combine it with any inputs
        from the Data Quality Scientist for that exposure.</li>
         <li> You can either select an exposure from the drop down (<b>(1) Select</b>) or enter it yourself (<b>(2) Enter</b>). Make sure to identify which you will use.</li> 
         </ul>
        </li>
        <li>If you'd like to modify a submitted comment, enter the Time of the submission and hit the <b>Load</b> button. 
        If you forget when a comment was submitted, check the Current NL. This will be the case for submissions made by Exposure number as well.
        After making your modifications, resubmit using the <b>Add/Update</b>.</li>
        </ul>
        """
        exp_inst = Div(text=inst, css_classes=['inst-style'], width=1000)
        
        self.exp_exposure_start = TextInput(title='Exposure Number: First', placeholder='12345', width=200)
        self.exp_exposure_finish = TextInput(title='Exposure Number: Last', placeholder='12346', width=200)

        self.exp_layout = layout(children=[self.buffer, self.title,
                        exp_subtitle,
                        exp_inst,
                        self.time_note,
                        self.os_exp_option,
                        [self.time_title, self.exp_time, self.now_btn, self.exp_load_btn],
                        [self.exp_option],
                        [self.exp_select, self.exp_enter],
                        [self.exp_comment],
                        [self.img_upinst2, self.img_upload_comments_os],
                        [self.exp_btn],
                        self.exp_alert], width=1000)
        self.exp_tab = Panel(child=self.exp_layout, title="Nightly Progress")

    def get_dqs_exp_layout(self):
        self.exp_layout()
        exp_subtitle = Div(text="Exposures", css_classes=['subt-style'])
        inst = """
        <ul>
        <li>For each exposure, collect information about what you observe on Night Watch (quality).
        <li>You can either select an exposure from the drop down (<b>(1) Select</b>) or enter it yourself (<b>(2) Enter</b>). Make sure to identify which you will use.</li> 
        <li>The exposure list is updated every 30 seconds. It might take some time for the exposure to transfer to Night Watch.</li> 
        <li>If you'd like to modify a submitted comment or quality assingment, you can recall a submission by selecting or entering the exposure number and using the <b>Load</b> button. 
        After making your modifications, resubmit using the <b>Add/Update</b> button.</li>
        </ul>
        """
        exp_inst = Div(text=inst, css_classes=['inst-style'], width=1000)

        self.exp_comment.placeholder = 'CCD4 has some bright columns'
        self.quality_title = Div(text='Data Quality: ', css_classes=['inst-style'])
        
        
        self.exp_layout = layout(self.buffer,self.title,
                            exp_subtitle,
                            exp_inst,
                            [self.exp_option, self.dqs_load_btn],
                            [self.exp_select, self.exp_enter],
                            [self.quality_title, self.quality_btns],
                            self.exp_comment,
                            [self.img_upinst2, self.img_upload_comments_dqs],
                            [self.exp_btn],
                            [self.exp_alert], width=1000)
        self.exp_tab = Panel(child=self.exp_layout, title="Exposures") 

    def get_prob_layout(self):
        self.prob_subtitle = Div(text="Problems", css_classes=['subt-style'])
        inst = """<ul>
        <li>Describe problems as they come up, the time at which they occur, the resolution, and how much time was lost as a result. If there is an Alarm ID associated with the problem, 
        include it, but leave blank if not. </li>
        <li>Please enter the time when the problem began, or use the “Now” button if it just occurred.</li>
        <li>If you'd like to modify or add to a submission, you can <b>Load</b> it using its timestamp. 
        If you forget when a comment was submitted, check the Current NL. After making the modifications 
        or additions, press the <b>Add/Update</b> button.</li>
        </ul>
        """
        self.prob_inst = Div(text=inst, css_classes=['inst-style'], width=1000)
        self.prob_time = TextInput(placeholder = '20:07', width=100) #title ='Time in Kitt Peak local time*', 
        self.prob_input = TextAreaInput(placeholder="NightWatch not plotting raw data", rows=10, cols=5, title="Problem Description*:",width=400,max_length=10000)
        self.prob_alarm = TextInput(title='Alarm ID', placeholder='12', width=100)
        self.prob_action = TextAreaInput(title='Resolution/Action',placeholder='description',rows=10, cols=5,width=400,max_length=10000)
        self.prob_btn = Button(label='Add/Update', css_classes=['add_button'])
        self.prob_load_btn = Button(label='Load', css_classes=['connect_button'], width=75)
        self.prob_alert = Div(text=' ', css_classes=['alert-style'])

        prob_layout = layout([self.buffer,self.title,
                            self.prob_subtitle,
                            self.prob_inst,
                            self.time_note,
                            self.exp_info,
                            [self.time_title, self.prob_time, self.now_btn, self.prob_load_btn], 
                            self.prob_alarm,
                            [self.prob_input, self.prob_action],
                            [self.img_upinst2, self.img_upload_problems],
                            [self.prob_btn],
                            self.prob_alert], width=1000)

        self.prob_tab = Panel(child=prob_layout, title="Problems")

    def get_weather_layout(self):
    
        self.weather_subtitle = Div(text="Observing Conditions", css_classes=['subt-style'])
        inst = """<ul>
        <li>Every hour, as part of the OS checklist, include a description of the weather and observing conditions.</li>
        <li>The most recent weather and observing condition information will be added to the table below and the Night Log when you <b>Add Weather Description</b>.
        Please note that the additional information may not correlate exactly with the time stamp but are just the most recent recorded values</li>
        <li>If you are not the OS, you can only see their inputs.</li>
        <li>SCROLL DOWN! There are plots of the ongoing telemetry for the observing conditions. These will be added to the Night Log when submitted at the end of the night.</li> 
        </ul>
        """
        self.weather_inst = Div(text=inst, width=1000, css_classes=['inst-style'])

        data = pd.DataFrame(columns = ['Time','desc','temp','wind','humidity','seeing','tput','skylevel'])
        self.weather_source = ColumnDataSource(data)
        obs_columns = [TableColumn(field='Time', title='Time (Local)', width=50, formatter=self.timefmt),
                   TableColumn(field='desc', title='Description', width=150),
                   TableColumn(field='temp', title='Temperature (C)', width=75),
                   TableColumn(field='wind', title='Wind Speed (mph)', width=75),
                   TableColumn(field='humidity', title='Humidity (%)', width=50),
                   TableColumn(field='seeing', title='Seeing (arcsec)', width=50),
                   TableColumn(field='tput', title='Throughput', width=50),
                   TableColumn(field='skylevel', title='Sky Level', width=50)] #, 

        self.weather_table = DataTable(source=self.weather_source, columns=obs_columns, width=1000, height=500)

        telem_data = pd.DataFrame(columns =
        ['time','exp','mirror_temp','truss_temp','air_temp','humidity','wind_speed','airmass','exptime','seeing','tput','skylevel'])
        self.telem_source = ColumnDataSource(telem_data)

        plot_tools = 'pan,wheel_zoom,lasso_select,reset,undo,save'
        p1 = figure(plot_width=800, plot_height=300, x_axis_label='UTC Time', y_axis_label='Temp (C)',x_axis_type="datetime", tools=plot_tools)
        p2 = figure(plot_width=800, plot_height=300, x_axis_label='UTC Time', x_range=p1.x_range, y_axis_label='Humidity (%)', x_axis_type="datetime",tools=plot_tools)
        p3 = figure(plot_width=800, plot_height=300, x_axis_label='UTC Time', x_range=p1.x_range, y_axis_label='Wind Speed (mph)', x_axis_type="datetime",tools=plot_tools)
        p4 = figure(plot_width=800, plot_height=300, x_axis_label='UTC Time', x_range=p1.x_range, y_axis_label='Airmass', x_axis_type="datetime",tools=plot_tools)
        p5 = figure(plot_width=800, plot_height=300, x_axis_label='UTC Time', x_range=p1.x_range, y_axis_label='Exptime (sec)', x_axis_type="datetime",tools=plot_tools)
        p6 = figure(plot_width=800, plot_height=300, x_axis_label='Exposure', y_axis_label='Seeing (arcsec)', tools=plot_tools)
        p7 = figure(plot_width=800, plot_height=300, x_axis_label='Exposure', y_axis_label='Transparency', tools=plot_tools, x_range = p6.x_range)
        p8 = figure(plot_width=800, plot_height=300, x_axis_label='Exposure', y_axis_label='Sky Level', tools=plot_tools, x_range=p6.x_range)

        p1.circle(x = 'time',y='mirror_temp',source=self.telem_source,color='orange', size=10, alpha=0.5) #
        p1.circle(x = 'time',y='truss_temp',source=self.telem_source, size=10, alpha=0.5, ) #legend_label = 'Truss'
        p1.circle(x = 'time',y='air_temp',source=self.telem_source, color='green', size=10, alpha=0.5) #, legend_label = 'Air'
        p1.legend.location = "top_right"

        p2.circle(x = 'time',y='humidity',source=self.telem_source, size=10, alpha=0.5)
        p3.circle(x = 'time',y='wind_speed',source=self.telem_source, size=10, alpha=0.5)
        p4.circle(x = 'time',y='airmass',source=self.telem_source, size=10, alpha=0.5)
        p5.circle(x = 'time',y='exptime',source=self.telem_source, size=10, alpha=0.5)
        p6.circle(x = 'exp',y='seeing',source=self.telem_source, size=10, alpha=0.5)
        p7.circle(x = 'exp',y='tput',source=self.telem_source, size=10, alpha=0.5)
        p8.circle(x = 'exp',y='skylevel',source=self.telem_source, size=10, alpha=0.5)

        self.weather_desc = TextInput(title='Weather Description', placeholder='description', width=500)
        self.weather_btn = Button(label='Add Weather Description', css_classes=['add_button'], width=100)
        self.weather_alert = Div(text=' ', css_classes=['alert-style'])
        self.plots_subtitle = Div(text='Telemetry Plots', css_classes=['subt-style'],width=800)

        if self.report_type == 'OS':
            weather_layout = layout([self.buffer,self.title,
                            self.weather_subtitle,
                            self.weather_inst,
                            [self.weather_desc, self.weather_btn],
                            self.weather_alert,
                            self.weather_table,
                            self.plots_subtitle,
                            p1,p2,p3,p4,p5,p6,p7,p8], width=1000)
        else:
            weather_layout = layout([self.buffer,self.title,
                self.weather_subtitle,
                self.weather_inst,
                self.weather_table,
                self.plots_subtitle,
                p1,p2,p3,p4,p5,p6,p7,p8], width=1000)
        self.weather_tab = Panel(child=weather_layout, title="Observing Conditions")

    def get_checklist_layout(self):
        
        self.checklist = CheckboxGroup(labels=[])
        inst="""
        <ul>
        <li>Once an hour, complete the checklist below.</li>
        <li>In order to <b>Submit</b>, you must check each task. You do not need to include a comment.</li>
        <li>Often, completing these tasks requires communication with the LO.</li> 
        </ul>
        """
        self.checklist_inst = Div(text=inst, css_classes=['inst-style'], width=1000)

        self.check_time = TextInput(placeholder = '20:07') #title ='Time in Kitt Peak local time*', 
        self.check_alert = Div(text=" ", css_classes=['alert-style'])
        self.check_btn = Button(label='Submit', css_classes=['add_button'])
        self.check_comment = TextAreaInput(title='Comment', placeholder='comment if necessary', rows=3, cols=3)
        
        if self.report_type == 'OS':
            self.checklist.labels = self.os_checklist
            self.check_subtitle = Div(text="OS Checklist", css_classes=['subt-style'])
        elif self.report_type == 'DQS':
            self.checklist.labels = self.dqs_checklist
            self.check_subtitle = Div(text="DQS Checklist", css_classes=['subt-style'])
        checklist_layout = layout(self.buffer,self.title,
                                self.check_subtitle,
                                self.checklist_inst,
                                self.checklist,
                                self.check_comment,
                                [self.check_btn],
                                self.check_alert, width=1000)
        self.check_tab = Panel(child=checklist_layout, title="DQS Checklist")


    def get_nl_layout(self):
        self.nl_subtitle = Div(text="Current DESI Night Log: {}".format(self.nl_file), css_classes=['subt-style'])
        self.nl_btn = Button(label='Get Current DESI Night Log', css_classes=['connect_button'])
        self.nl_text = Div(text=" ", width=800)
        self.nl_alert = Div(text='You must be connected to a Night Log', css_classes=['alert-style'], width=500)
        self.nl_submit_btn = Button(label='Submit NightLog & Publish Nightsum', width=300, css_classes=['add_button'])
        
        self.exptable_alert = Div(text=" ", css_classes=['alert-style'], width=500)

        exp_data = pd.DataFrame(columns = ['date_obs','id','program','sequence','flavor','exptime','airmass','seeing'])
        self.explist_source = ColumnDataSource(exp_data)

        exp_columns = [TableColumn(field='date_obs', title='Time (UTC)', width=50, formatter=self.datefmt),
                   TableColumn(field='id', title='Exposure', width=50),
                   TableColumn(field='sequence', title='Sequence', width=100),
                   TableColumn(field='flavor', title='Flavor', width=50),
                   TableColumn(field='exptime', title='Exptime', width=50),
                   TableColumn(field='program', title='Program', width=300),
                   TableColumn(field='airmass', title='Airmass', width=50),
                   TableColumn(field='seeing', title='Seeing', width=50)]

        self.exp_table = DataTable(source=self.explist_source, columns=exp_columns, width=1000)

        if (self.report_type == 'OS') & (self.location == 'kpno'):
            nl_layout = layout([self.buffer,self.title,
                        self.nl_subtitle,
                        self.nl_alert,
                        self.nl_text,
                        self.exptable_alert,
                        self.exp_table,
                        self.nl_submit_btn], width=1000)
        else:
            nl_layout = layout([self.buffer, self.title,
                        self.nl_subtitle,
                        self.nl_alert,
                        self.nl_text,
                        self.exptable_alert,
                        self.exp_table], width=1000)
        self.nl_tab = Panel(child=nl_layout, title="Current DESI Night Log")


    def get_time(self, time):
        """Returns strptime with utc. Takes time zone selection
        """
        date = datetime.datetime.strptime(self.night,'%Y%m%d')
        try:
            b = datetime.datetime.strptime(time, '%H:%M')
        except:
            try:
                b = datetime.datetime.strptime(time, '%H%M')
            except:
                try:
                    b = datetime.datetime.strptime(time, '%I%M%p')
                except:
                    print(time)
                    print('need format %H%M, %H:%M, %H:%M%p')
        t = datetime.time(hour=b.hour, minute=b.minute)
        if t > datetime.datetime.min.time():
            d = date + datetime.timedelta(days=1)
        else:
            d = date
        tt = datetime.datetime.combine(d, t)
        try:
            return tt.strftime("%Y%m%dT%H:%M")
        except:
            return time

    def get_strftime(self, time):
        date = self.night
        d = datetime.datetime.strptime(date, "%Y%m%d")
        dt = datetime.datetime.combine(d,time)
        return dt.strftime("%Y%m%dT%H:%M")

    def get_night(self, mode='connect'):
        if mode == 'connect':
            try:
                date = datetime.datetime.strptime(self.date_init.value, '%Y%m%d')
            except:
                date = datetime.datetime.now().date()
        elif mode == 'init':
            date = datetime.datetime.now().date()
        self.night = date.strftime("%Y%m%d")
        self.DESI_Log = nl.NightLog(self.night, self.location)

    def connect_log(self):
        """Connect to Existing Night Log with Input Date
        """
        self.get_night('connect')
        exists = self.DESI_Log.check_exists()

        your_firstname, your_lastname = self.your_name.value.split(' ')[0], ' '.join(self.your_name.value.split(' ')[1:])
        if exists:
            self.connect_txt.text = 'Connected to Night Log for {}'.format(self.date_init.value)

            if self.report_type == 'DQS':
                self.DESI_Log.add_dqs_observer(your_firstname, your_lastname)
                
            meta_dict_file = self.DESI_Log._open_kpno_file_first(self.DESI_Log.meta_json)
            meta_dict = json.load(open(meta_dict_file,'r'))
                
            if self.report_type == 'DQS':
                self.your_name.value = meta_dict['dqs_1']+' '+meta_dict['dqs_last']

            self.full_time = (datetime.datetime.strptime(meta_dict['dawn_18_deg'], '%Y%m%dT%H:%M') - datetime.datetime.strptime(meta_dict['dusk_18_deg'], '%Y%m%dT%H:%M')).seconds/3600
            self.full_time_text.text = 'Total time between 18 deg. twilights (hrs): {:.2f}'.format(self.full_time)
            self.display_current_header()
            self.nl_file = self.DESI_Log.nightlog_file
            self.nl_subtitle.text = "Current DESI Night Log: {}".format(self.nl_file)

            if self.report_type == 'OS':
                plan_txt_text="https://desi.lbl.gov/trac/wiki/DESIOperations/ObservingPlans/OpsPlan{}".format(self.night)
                self.plan_txt.text = '<a href={}>Tonights Plan Here</a>'.format(plan_txt_text)
                self.os_name_1.value = meta_dict['{}_1_firstname'.format(self.report_type.lower())]+' '+meta_dict['{}_1_lastname'.format(self.report_type.lower())]
                self.os_name_2.value = meta_dict['{}_2_firstname'.format(self.report_type.lower())]+' '+meta_dict['{}_2_lastname'.format(self.report_type.lower())]
                self.LO.value = meta_dict['LO_firstname']+' '+meta_dict['LO_lastname']
                self.OA.value = meta_dict['OA_firstname']+' '+meta_dict['OA_lastname']
                cont_file = self.DESI_Log._open_kpno_file_first(self.DESI_Log.contributer_file)
                if os.path.exists(cont_file):
                    cont_txt = ''
                    f =  open(cont_file, "r")
                    for line in f:
                        cont_txt += line
                    self.contributer_list.value = cont_txt
                time_use_file = self.DESI_Log._open_kpno_file_first(self.DESI_Log.time_use)
                if os.path.exists(time_use_file):
                    df = pd.read_csv(time_use_file)
                    data = df.iloc[0]
                    self.summary_1.value = str(data['summary_1'])
                    self.summary_2.value = str(data['summary_2'])
                    self.obs_time.value =  str(data['obs_time'])
                    self.test_time.value = str(data['test_time'])
                    self.inst_loss_time.value = str(data['inst_loss'])
                    self.weather_loss_time.value = str(data['weather_loss'])
                    self.tel_loss_time.value = str(data['tel_loss'])
                    self.total_time.text = 'Time Documented (hrs): %.2f' % float(data['total'])
            self.current_nl()
            self.get_exposure_list()

        else:
            self.connect_txt.text = 'The Night Log for this {} is not yet initialized.'.format(self.date_init.value)

    def initialize_log(self):
        """ Initialize Night Log with Input Date
        """
        self.get_night('init')
        meta = OrderedDict()
        meta['LO_firstname'], meta['LO_lastname'] = self.LO.value.split(' ')[0], ' '.join(self.LO.value.split(' ')[1:])
        meta['OA_firstname'], meta['OA_lastname'] = self.OA.value.split(' ')[0], ' '.join(self.OA.value.split(' ')[1:])
        meta['os_1_firstname'], meta['os_1_lastname'] = self.os_name_1.value.split(' ')[0], ' '.join(self.os_name_1.value.split(' ')[1:])
        meta['os_2_firstname'], meta['os_2_lastname'] = self.os_name_2.value.split(' ')[0], ' '.join(self.os_name_2.value.split(' ')[1:])

        eph = sky_calendar()

        meta['time_sunset'] = self.get_strftime(eph['sunset'])
        meta['time_sunrise'] = self.get_strftime(eph['sunrise'])
        meta['time_moonrise'] = self.get_strftime(eph['moonrise'])
        meta['time_moonset'] = self.get_strftime(eph['moonset'])
        meta['illumination'] = eph['illumination']
        meta['dusk_18_deg'] = self.get_strftime(eph['dusk_astronomical'])
        meta['dawn_18_deg'] = self.get_strftime(eph['dawn_astronomical'])

        self.full_time = (datetime.datetime.strptime(meta['dawn_18_deg'],'%Y%m%dT%H:%M') - datetime.datetime.strptime(meta['dusk_18_deg'],'%Y%m%dT%H:%M')).seconds/3200
        self.full_time_text.text = 'Total time between 18 deg. twilights (hrs): {}'.format(self.full_time)

        self.DESI_Log.initializing()
        self.DESI_Log.get_started_os(meta)

        self.connect_txt.text = 'Night Log is Initialized'
        self.DESI_Log.write_intro()
        self.display_current_header()
        self.current_nl()

        self.update_nl_list()


    def display_current_header(self):
        path = self.DESI_Log._open_kpno_file_first(self.DESI_Log.header_html)
        nl_file = open(path, 'r')
        intro = ''
        for line in nl_file:
            intro =  intro + line + '\n'
        self.intro_txt.text = intro
        nl_file.closed

    def current_nl(self):
        try:
            now = datetime.datetime.now()
            self.DESI_Log.finish_the_night()
            path = self.DESI_Log.nightlog_html 
            nl_file = open(path,'r')
            nl_txt = ''
            for line in nl_file:
                nl_txt =  nl_txt + line + '\n'
            self.nl_text.text = nl_txt
            nl_file.closed
            self.nl_alert.text = 'Last Updated on this page: {}'.format(now)
            self.nl_subtitle.text = "Current DESI Night Log: {}".format(path)
            self.get_exp_list()
            self.get_weather()
            #self.get_seeing()
            try:
                self.make_telem_plots()
                return True
            except:
                #print('Something wrong with making telemetry plots')
                return True 
        except Exception as e:
            print('current_nl Exception: %s' % str(e))
            self.nl_alert.text = 'You are not connected to a Night Log'
            return False

    def get_exp_list(self):
        try:
            self.exp_df = pd.read_sql_query(f"SELECT * FROM exposure WHERE night = '{self.night}'", self.conn)
            if len(self.exp_df.date_obs) >  0:
                time = self.exp_df.date_obs.dt.tz_convert('US/Arizona')
                self.exp_df['date_obs'] = time
                self.explist_source.data = self.exp_df[['date_obs','id','tileid','program','sequence','flavor','exptime','airmass','seeing']].sort_values(by='id',ascending=False) 
                self.exp_df = self.exp_df.sort_values(by='id')
                self.exp_df.to_csv(self.DESI_Log.explist_file, index=False)
            else:
                self.exptable_alert.text = f'No exposures available for night {self.night}'
        except Exception as e:
            self.exptable_alert.text = 'Cannot connect to Exposure Data Base. {}'.format(e)

    def get_weather(self):
        if os.path.exists(self.DESI_Log.weather):
            obs_df = pd.read_csv(self.DESI_Log.weather)
            t = [datetime.datetime.strptime(tt, "%Y%m%dT%H:%M") for tt in obs_df['Time']]
            obs_df['Time'] = t
            self.weather_source.data = obs_df.sort_values(by='Time')
        else:
            pass

    def get_seeing(self):
        #self.seeing_df = pd.DataFrame()
        seeing = []
        exps = []
        exposures = pd.DataFrame(self.explist_source.data)['id']
        for exp in list(exposures):
            try:
                folder = '/data/platemaker/test/{}/'.format(int(exp))
                filen = os.path.join(folder,'qc-gfaproc-{}.?.info'.format(int(exp)))
                f = glob.glob(filen)[-1]

                try:
                    lines = open(f,'r').readlines()
                    line = lines[5].strip()
                    x0 = line.find('=')
                    x1 = line.find(',')
                    s = float(line[x0+1:x1])
                except:
                    s = np.nan

                seeing.append(s)
                exps.append(exp)
            except:
                pass
            
        # self.seeing_df = pd.DataFrame()
        # self.seeing_df['Seeing'] = seeing
        # self.seeing_df['Exps'] = exps
        # self.seeing_df.to_csv(os.path.join(self.DESI_Log.root_dir,'seeing.csv'),index=False)
        # # KH added to avoid issues with X11 and Display (we only need the png)
        # figure = plt.figure()
        # plt.plot(self.seeing_df.Exps, self.seeing_df.Seeing,'o')
        # plt.xlabel("Exposure")
        # plt.ylabel("Seeing (arcsec)")
        # plt.savefig(os.path.join(self.DESI_Log.root_dir,'seeing.png'))
        # plt.close(figure)

    def get_telem_list(self, df, l, item):
        list_ = []
        for r in list(df[l]):
            try:
                list_.append(r[item])
            except:
                list_.append(None)
        return list_
        
    def make_telem_plots(self):
        dt = datetime.datetime.strptime(self.night, '%Y%m%d').date()
        #start_utc = '{} {}'.format(self.night, '13:00:00')
        dt_2 = dt + datetime.timedelta(days=1)
        start_utc = '{} {}'.format(dt.strftime("%Y%m%d"), '21:00:00')
        end_utc = '{} {}'.format(dt_2.strftime("%Y%m%d"), '21:00:00')
        exp_df = pd.read_sql_query(f"SELECT * FROM exposure WHERE date_obs > '{start_utc}' AND date_obs < '{end_utc}'", self.conn) #night = '{self.night}'", self.conn)
        #self.get_seeing()
        telem_data = pd.DataFrame(columns =
        ['time','exp','mirror_temp','truss_temp','air_temp','temp','humidity','wind_speed','airmass','exptime','seeing','tput','skylevel'])
        if len(exp_df) > 0:
            exp_df.sort_values('date_obs',inplace=True)
            telem_data.time = exp_df.date_obs.dt.tz_convert('US/Arizona')
            telem_data.exp = exp_df.id 
            telem_data.mirror_temp = self.get_telem_list(exp_df, 'telescope','mirror_temp') #[r['mirror_temp'] for r in list(exp_df['telescope'])] #['mirror_temp']
            telem_data.truss_temp = self.get_telem_list(exp_df, 'telescope','truss_temp') #[r['truss_temp'] for r in list(exp_df['telescope'])] #exp_df['telescope']['truss_temp']
            telem_data.air_temp = self.get_telem_list(exp_df, 'telescope','air_temp')#[r['air_temp'] for r in list(exp_df['telescope'])] #['air_temp']
            telem_data.temp = self.get_telem_list(exp_df, 'tower','temperature') #[r['temperature'] for r in list(exp_df['tower'])] #['temperature']
            telem_data.humidity = self.get_telem_list(exp_df, 'tower','humidity') #[r['humidity'] for r in list(exp_df['tower'])] #['humidity']
            telem_data.wind_speed = self.get_telem_list(exp_df, 'tower','wind_speed') #[r['wind_speed'] for r in list(exp_df['tower'])] #['wind_speed']
            telem_data.airmass = exp_df.airmass
            telem_data.exptime = exp_df.exptime
            telem_data.seeing = exp_df.seeing
            telem_data.tput = exp_df.transpar
            telem_data.skylevel = exp_df.skylevel
        self.telem_source.data = telem_data

        if self.save_telem_plots:
            fig = plt.figure(figsize=(8,20))
            ax1 = fig.add_subplot(8,1,1)
            ax1.scatter(exp_df.date_obs.dt.tz_convert('US/Arizona'), self.get_telem_list(exp_df,'telescope','mirror_temp'), s=5, label='mirror temp')    
            ax1.scatter(exp_df.date_obs.dt.tz_convert('US/Arizona'), self.get_telem_list(exp_df,'telescope','truss_temp'), s=5, label='truss temp')  
            ax1.scatter(exp_df.date_obs.dt.tz_convert('US/Arizona'), self.get_telem_list(exp_df,'telescope','air_temp'), s=5, label='air temp') 
            ax1.set_ylabel("Telescop Temperature (C)")
            ax1.legend()
            ax1.grid(True)
            ax1.tick_params(labelbottom=False)

            ax2 = fig.add_subplot(8,1,2, sharex = ax1)
            ax2.scatter(exp_df.date_obs.dt.tz_convert('US/Arizona'), self.get_telem_list(exp_df,'tower','humidity'), s=5, label='humidity') 
            ax2.set_ylabel("Humidity %")
            ax2.grid(True)
            ax2.tick_params(labelbottom=False)

            ax3 = fig.add_subplot(8,1,3, sharex=ax1) 
            ax3.scatter(exp_df.date_obs.dt.tz_convert('US/Arizona'), self.get_telem_list(exp_df,'tower','wind_speed'), s=5, label='wind speed')
            ax3.set_ylabel("Wind Speed (mph)")
            ax3.grid(True)
            ax3.tick_params(labelbottom=False)

            ax4 = fig.add_subplot(8,1,4, sharex=ax1)
            ax4.scatter(exp_df.date_obs.dt.tz_convert('US/Arizona'), exp_df.airmass, s=5, label='airmass')
            ax4.set_ylabel("Airmass")
            ax4.grid(True)
            ax4.tick_params(labelbottom=False)

            ax5 = fig.add_subplot(8,1,5, sharex=ax1)
            ax5.scatter(exp_df.date_obs.dt.tz_convert('US/Arizona'), exp_df.exptime, s=5, label='exptime')
            ax5.set_ylabel("Exposure time (s)")
            ax5.grid(True)
            ax5.tick_params(labelbottom=False)

            ax6 = fig.add_subplot(8,1,6,sharex=ax1)
            ax6.scatter(exp_df.date_obs.dt.tz_convert('US/Arizona'), exp_df.seeing, s=5, label='seeing')   
            ax6.set_ylabel("Seeing")
            ax6.grid(True)
            ax6.tick_params(labelbottom=False)

            ax7 = fig.add_subplot(8,1,7,sharex=ax1)
            ax7.scatter(exp_df.date_obs.dt.tz_convert('US/Arizona'), exp_df.transpar, s=5, label='transparency')
            ax7.set_ylabel("Transparency (%)")
            ax7.grid(True)
            ax7.tick_params(labelbottom=False)

            ax8 = fig.add_subplot(8,1,8,sharex=ax1)
            ax8.scatter(exp_df.date_obs.dt.tz_convert('US/Arizona'), exp_df.skylevel, s=5, label='Sky Level')      
            ax8.set_ylabel("Sky level (AB/arcsec^2)")
            ax8.grid(True)

            ax8.set_xlabel("Local Time (MST)")
            ax8.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M', tz=pytz.timezone("US/Arizona")))
            ax8.tick_params(labelrotation=45)
            fig.suptitle("Telemetry for obsday={}".format(self.night))
            fig.tight_layout()

            plt.savefig(self.DESI_Log.telem_plots_file)

                
    def exp_to_html(self):
        exp_df = pd.read_csv(self.DESI_Log.explist_file)
        exp_df = exp_df[['date_obs','id','tileid','program','sequence','flavor','exptime','airmass','seeing']].sort_values(by='id',ascending=False) 
        exp_df = exp_df.rename(columns={"date_obs": "Time", "id":
        "Exp","tileid":'Tile','program':'Program','sequence':'Sequence','flavor':'Flavor','exptime':'Exptime','airmass':'Airmass','seeing':'Seeing'})
        exp_html = exp_df.to_html()
        return exp_html


    def check_add(self):
        """add checklist time to Night Log
        """
        complete = self.checklist.active
        check_time = datetime.datetime.now().strftime("%Y%m%dT%H:%M")
        if len(complete) == len(self.checklist.labels):
            self.DESI_Log.add_input([self.report_type, check_time, self.check_comment.value], 'checklist')
            self.check_alert.text = "Checklist last submitted at {}".format(check_time[-5:])
        else:
            self.check_alert.text = "Must complete all tasks before submitting checklist"
        self.clear_input(self.check_comment)
        self.checklist.active = []

    def plan_add_new(self):
        self.plan_time = None
        self.plan_add()

    def milestone_add_new(self):
        self.milestone_time = None
        self.milestone_add()

    def plan_add(self):
        if self.plan_time is None:
            ts = datetime.datetime.now().strftime("%Y%m%dT%H:%M")
        else: 
            ts = self.plan_time
        self.DESI_Log.add_input([ts, self.plan_input.value], 'plan')
        self.plan_alert.text = 'Last item input: {}'.format(self.plan_input.value)
        self.clear_input([self.plan_order, self.plan_input])
        self.plan_time = None

    def milestone_add(self):
        if self.milestone_time is None:
            ts = datetime.datetime.now().strftime("%Y%m%dT%H:%M")
        else:
            ts = self.milestone_time
        self.DESI_Log.add_input([ts, self.milestone_input.value, self.milestone_exp_start.value, self.milestone_exp_end.value, self.milestone_exp_excl.value],'milestone')
        self.milestone_alert.text = 'Last Milestone Entered: {}'.format(self.milestone_input.value)
        self.clear_input([self.milestone_input, self.milestone_exp_start, self.milestone_exp_end, self.milestone_exp_excl])
        self.milestone_time = None

    def get_latest_val(self, l):
        try:
            x = list(l.dropna())[-1]
        except:
            x = np.nan
        return x

    def weather_add(self):
        """Adds table to Night Log
        """
        now = datetime.datetime.now().astimezone(tz=self.kp_zone).strftime("%Y%m%dT%H:%M")
        try:
            self.make_telem_plots()
            telem_df = pd.DataFrame(self.telem_source.data)
            this_data = telem_df.iloc[-1]
            desc = self.weather_desc.value
            temp = self.get_latest_val(telem_df.temp) #.dropna())[-1] #list(telem_df)[np.isfinite(list(telem_df.temp))][-1] #this_data.temp
            wind = self.get_latest_val(telem_df.wind_speed) #list(telem_df.wind_speed.dropna())[-1]
            humidity = self.get_latest_val(telem_df.humidity) #list(telem_df.humidity.dropna())[-1] #this_data.humidity
            seeing = self.get_latest_val(telem_df.seeing) #list(telem_df.seeing.dropna())[-1] #this_data.seeing
            tput = self.get_latest_val(telem_df.tput) #list(telem_df.tput.dropna())[-1]
            skylevel = self.get_latest_val(telem_df.skylevel)  #list(telem_df.skylevel.dropna())[-1]
            data = [now, desc, temp, wind, humidity, seeing, tput, skylevel]

        except: 
            data = [now, self.weather_desc.value, None, None, None, None, None, None]
            
            self.weather_alert.text = 'Not connected to the telemetry DB. Only weather description will be recorded.'
        df = self.DESI_Log.add_input(data,'weather')
        self.clear_input([self.weather_desc])
        self.get_weather()

    def image_uploaded(self, mode='comment'):
        img_data = None
        img_name = None

        if mode == 'comment':         
            if self.report_type == 'DQS':
                if hasattr(self, 'img_upload_comments_dqs') and self.img_upload_comments_dqs.filename not in [None,'',np.nan,'nan']:
                    img_data = self.img_upload_comments_dqs.value.encode('utf-8')
                    img_name = str(self.img_upload_comments_dqs.filename)
            else:
                if self.exp_comment.value not in [None, ''] and hasattr(self, 'img_upload_comments_os') and self.img_upload_comments_os.filename not in [None,'','nan',np.nan]:
                    img_data = self.img_upload_comments_os.value.encode('utf-8')
                    img_name = str(self.img_upload_comments_os.filename)

        elif mode == 'problem':
            if hasattr(self, 'img_upload_problems') and self.img_upload_problems.filename not in [None, '',np.nan, 'nan']:
                img_data = self.img_upload_problems.value.encode('utf-8')
                img_name = str(self.img_upload_problems.filename)

        self.image_location_on_server = f'http://desi-www.kpno.noao.edu:8090/{self.night}/images/{img_name}'
        width=400
        height=400 #http://desi-www.kpno.noao.edu:8090/nightlogs
        preview = '<img src="%s" width=%s height=%s alt="Uploaded image %s">\n' % (self.image_location_on_server,str(width),str(height),img_name)
        return img_name, img_data, preview
       
    def prob_add(self):
        """Adds problem to nightlog
        """
        name = self.your_name.value
        if (self.report_type == 'Other') & (name in [None,' ','']):
                self.prob_alert.text = 'You need to enter your name on first page before submitting a comment'
        else:
            img_name, img_data, preview = self.image_uploaded('problem')
            data = [self.report_type, self.get_time(self.prob_time.value.strip()), self.prob_input.value.strip(), self.prob_alarm.value.strip(),
            self.prob_action.value.strip(), name]
            self.DESI_Log.add_input(data, 'problem',img_name=img_name, img_data=img_data)

            # Preview
            if img_name not in [None,'',' ','nan']:
                preview += "<br>"
                preview += "Last Problem Input: '{}' at {}".format(self.prob_input.value.strip(), self.prob_time.value.strip())
                self.prob_alert.text = preview
                self.img_upload_problems = FileInput(accept=".png")
            else:
                self.prob_alert.text = "Last Problem Input: '{}' at {}".format(self.prob_input.value.strip(), self.prob_time.value.strip())
            self.clear_input([self.prob_time, self.prob_input, self.prob_alarm, self.prob_action])

    def progress_add(self):
        if self.os_exp_option.active == 0:
            if self.exp_time.value not in [None, 'None'," ", ""]:
                time = self.get_time(self.exp_time.value.strip())
                comment = self.exp_comment.value.strip()
                exp = None
            else:
                self.exp_alert.text = 'Fill in the time'
                

        elif self.os_exp_option.active == 1:
            if self.exp_option.active == 0:
                exp = int(self.exp_select.value)
            elif self.exp_option.active ==1:
                exp = int(self.exp_enter.value.strip())
            comment = self.exp_comment.value.strip()
            time = self.get_time(datetime.datetime.now().strftime("%H:%M"))


        img_name, img_data, preview = self.image_uploaded('comment')
        data = [time, comment, exp]
        self.DESI_Log.add_input(data, 'os_exp',img_name=img_name, img_data=img_data)
        if img_name is not None:
            preview += "<br>"
            preview += "A comment was added at {}".format(datetime.datetime.now().strftime("%H:%M"))
            self.exp_alert.text = preview
            self.img_upload_comments_os=FileInput(accept=".png")
        else:
            self.exp_alert.text = 'Last Input was at {}'.format(datetime.datetime.now().strftime("%H:%M"))

        self.clear_input([self.exp_time, self.exp_comment, self.exp_enter])
    
    def comment_add(self):
        if self.your_name.value in [None,' ','']:
            self.exp_alert.text = 'You need to enter your name on first page before submitting a comment'
        else:
            if self.os_exp_option.active == 0:
                if self.exp_time.value not in [None, 'None'," ", ""]:
                    time = self.get_time(self.exp_time.value.strip())
                    comment = self.exp_comment.value.strip()
                    exp = None
                else:
                    self.exp_alert.text = 'Fill in the time'
            elif self.os_exp_option.active == 1:
                if self.exp_option.active == 0:
                    try:
                        exp = int(self.exp_select.value)
                    except:
                        self.exp_alert.text = 'Check your exposure input'
                elif self.exp_option.active ==1:
                    try:
                        exp = int(self.exp_enter.value.strip())
                    except:
                        self.exp_alert.text = 'Check your exposure input'
                comment = self.exp_comment.value.strip()
                time = self.get_time(datetime.datetime.now().strftime("%H:%M"))


            img_name, img_data, preview = self.image_uploaded('comment')
            data = [time, comment, exp, self.your_name.value.strip()]
            self.DESI_Log.add_input(data, 'other_exp',img_name=img_name, img_data=img_data)

            if img_name is not None:
                preview += "<br>"
                preview += "A comment was added at {}".format(self.exp_time.value.strip())
                self.exp_alert.text = preview
                self.img_upload_comments=FileInput(accept=".png")
            else:
                self.exp_alert.text = "A comment was added at {}".format(datetime.datetime.now().strftime("%H:%M"))
            self.clear_input([self.exp_time, self.exp_comment])

    def exp_add(self):
        quality = self.quality_list[self.quality_btns.active]
        if self.exp_option.active == 0:
            exp_val = int(self.exp_select.value)
        elif self.exp_option.active ==1:
            exp_val = int(self.exp_enter.value.strip())
        now = datetime.datetime.now().astimezone(tz=self.kp_zone).strftime("%H:%M")

        img_name, img_data, preview = self.image_uploaded('comment')
        data = [self.get_time(now), exp_val, quality, self.exp_comment.value.strip()]
        self.DESI_Log.add_input(data, 'dqs_exp',img_name=img_name, img_data=img_data)

        if img_name is not None:
            preview += "<br>"
            preview += "A comment was added at {}".format(self.exp_time.value.strip())
            self.exp_alert.text = preview
            self.img_upload_comments_dqs=FileInput(accept=".png")
        else:
            self.exp_alert.text = 'Last Exposure input {} at {}'.format(exp_val, now)
        self.clear_input([self.exp_time, self.exp_enter, self.exp_select, self.exp_comment])

    def plan_load(self):
        b, item = self.DESI_Log.load_index(self.plan_order.value, 'plan')
        if b:
            self.plan_input.value = str(item['Objective'])
            self.plan_time = item['Time']
        else:
            self.plan_alert.text = "That plan item doesn't exist yet. {}".format(item)

    def dqs_load(self):
        if self.exp_option.active == 0:
             exp = int(self.exp_select.value)
        if self.exp_option.active == 1:
            exp = int(self.exp_enter.value.strip())
        b, item = self.DESI_Log.load_exp(exp)
        if b:
            self.exp_comment.value = item['Comment']
            qual = np.where(self.quality_list==item['Quality'])[0]
            self.quality_btns.active = int(qual)
        else:
            self.exp_alert.text = "An input for that exposure doesn't exist for this user. {}".format(item)

    def milestone_load(self):
        b, item = self.DESI_Log.load_index(int(self.milestone_load_num.value), 'milestone')
        if b:
            self.milestone_input.value = str(item['Desc'])
            self.milestone_exp_start.value = str(item['Exp_Start'])
            self.milestone_exp_end.value = str(item['Exp_Stop'])
            self.milestone_exp_excl.value = str(item['Exp_Excl'])
            self.milestone_time = item['Time']
        else:
            self.milestone_alert.text = "That milestone index doesn't exist yet. {}".format(item)

    def load_exposure(self):
        #Check if progress has been input with a given timestamp
        _exists, item = self.DESI_Log.load_timestamp(self.get_time(self.exp_time.value.strip()), self.report_type, 'exposure')

        if not _exists:
            self.exp_alert.text = 'This timestamp does not yet have an input from this user. {}'.format(item)
        else:
            self.exp_comment.value = str(item['Comment'])
            self.exp_exposure_start.value = str(item['Exp_Start'])
            #self.exp_exposure_finish.value = str(item['Exp_End'])

    def load_problem(self):
        #Check if progress has been input with a given timestamp
        _exists, item = self.DESI_Log.load_timestamp(self.get_time(self.prob_time.value.strip()), self.report_type, 'problem')

        if not _exists:
            self.prob_alert.text = 'This timestamp does not yet have an input from this user. {}'.format(item)
        else:
            self.prob_input.value = str(item['Problem'])
            self.prob_alarm.value = str(item['alarm_id'])
            self.prob_action.value = str(item['action'])

    def add_contributer_list(self):
        cont_list = self.contributer_list.value
        self.DESI_Log.add_contributer_list(cont_list)

    def add_summary(self):
        now = datetime.datetime.now().strftime("%H:%M")
        data = OrderedDict()
        data['summary_1'] = self.summary_1.value
        data['summary_2'] = self.summary_2.value
        data['obs_time'] = self.obs_time.value
        data['test_time'] = self.test_time.value
        data['inst_loss'] = self.inst_loss_time.value
        data['weather_loss'] = self.weather_loss_time.value
        data['tel_loss'] = self.tel_loss_time.value
        data['18deg'] = self.full_time

        total = 0
        for i in ['obs_time','test_time','inst_loss','weather_loss','tel_loss']:
            try:
                if data[i] not in ['',' ','nan',np.nan]:
                    total += float(data[i])
                else:
                    data[i] = 0
                    total+=0
            except:
                total += 0
        data['total'] = total
        self.total_time.text = 'Time Documented (hrs): %.2f' % total
        self.DESI_Log.add_summary(data)
        self.milestone_alert.text = 'Summary Information Entered at {}'.format(now)

    def upload_image(self, attr, old, new):
        print(f'Local image file upload: {self.img_upload.filename}')

    def upload_image_comments_os(self, attr, old, new):
        print(f'Local image file upload (OS comments): {self.img_upload_comments_os.filename}')

    def upload_image_comments_other(self, attr, old, new):
        print(f'Local image file upload (Other comments): {self.img_upload_comments_other.filename}')

    def upload_image_comments_dqs(self, attr, old, new):
        print(f'Local image file upload (Other comments): {self.img_upload_comments_dqs.filename}')

    def upload_image_problems(self, attr, old, new):
        print(f'Local image file upload (Other comments): {self.img_upload_problems.filename}')

    def time_is_now(self):
        now = datetime.datetime.now().astimezone(tz=self.kp_zone).strftime("%H:%M")

        tab = self.layout.active
        time_input = self.time_tabs[tab]
        try:
            time_input.value = now
        except:
            return time_input

    def nl_submit(self):

        if not self.current_nl():
            self.nl_text.text = 'You cannot submit a Night Log to the eLog until you have connected to an existing Night Log or initialized tonights Night Log'
        else:
            try:
                from ECLAPI import ECLConnection, ECLEntry
            except ImportError:
                ECLConnection = None
                self.nl_text.text = "Can't connect to eLog"

            f = self.DESI_Log._open_kpno_file_first(self.DESI_Log.nightlog_html)
            nl_file=open(f,'r')
            lines = nl_file.readlines()
            nl_html = ' '
            for line in lines:
                nl_html += line

            e = ECLEntry('Synopsis_Night', text=nl_html, textile=True)

            subject = 'Night Summary {}-{}-{}'.format(self.date_init.value[0:4], self.date_init.value[4:6], self.date_init.value[6:])
            e.addSubject(subject)
            url = 'http://desi-www.kpno.noao.edu:8090/ECL/desi'
            user = 'dos'
            pw = 'dosuser'
            if self.test:
                pass
            else:
                elconn = ECLConnection(url, user, pw)
                response = elconn.post(e)
                elconn.close()
                if response[0] != 200:
                   raise Exception(response)
                   self.nl_text.text = "You cannot post to the eLog on this machine"

            self.save_telem_plots = True
            self.current_nl()

            nl_text = "Night Log posted to eLog and emailed to collaboration" + '</br>'
            self.nl_text.text = nl_text
            if self.test:
                self.email_nightsum(user_email = ["parfa30@gmail.com","parkerf@berkeley.edu"])
            else:
                self.email_nightsum(user_email = ["parfa30@gmail.com","satya.gontcho@gmail.com","desi-nightlog@desi.lbl.gov"])

    def email_nightsum(self,user_email = None):

        try:
            self.make_telem_plots()
        except:
            print("Something wrong with telem plots")

        sender = "noreply-ecl@noao.edu"

        # Create message container - the correct MIME type is multipart/alternative.
        msg = MIMEMultipart('html')
        msg['Subject'] = "Night Summary %s" % self.date_init.value #mjd2iso(mjd)
        msg['From'] = sender
        if len(user_email) == 1:
            msg['To'] = user_email[0]
        else:
            msg['To'] = ', '.join(user_email)

        # Create the body of the message (a plain-text and an HTML version).
        f = f = self.DESI_Log._open_kpno_file_first(self.DESI_Log.nightlog_html)
        nl_file=open(f,'r')
        lines = nl_file.readlines()
        nl_html = ' '
        img_names = []
        for line in lines:
            nl_html += line

        # Add exposures
        if os.path.exists(self.DESI_Log.explist_file):
            exp_list = self.exp_to_html()
            nl_html += ("<h3 id='exposures'>Exposures</h3>")
            for line in exp_list:
                nl_html += line

        # Add telem plots
        nl_html += "<h3 id='telem_plots'>Night Telemetry</h3>"
        nl_html += '\n'
        
        #if os.path.exists(self.DESI_Log.telem_plots_file):
        #    nl_html += '<img src="{}"> alt="Telemetry Plots"'.format(self.DESI_Log.telem_plots_file)
        #    nl_html += '\n'

        Html_file = open(os.path.join(self.DESI_Log.root_dir,'NightSummary{}'.format(self.night)),"w")
        Html_file.write(nl_html)
        Html_file.close()

        # Record the MIME types of both parts - text/plain and text/html.
        part1 = MIMEText(nl_html, 'plain')
        part2 = MIMEText(nl_html, 'html')

        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, in this case
        # the HTML message, is best and preferred.
        #msg.attach(part1)
        msg.attach(part2)

        # Add images
        if os.path.exists(self.DESI_Log.image_file):
            for i, img in enumerate(images):
                fp = open(os.path.join(self.DESI_Log.image_dir,img), 'rb')
                msgImage = MIMEImage(fp.read())
                fp.close()
                msgImage.add_header('Content-ID', '<image{}>'.format(i))
                msg.attach(msgImage)
        if os.path.exists(self.DESI_Log.telem_plots_file):
            fp = open(self.DESI_Log.telem_plots_file, 'rb')
            msgImage = MIMEImage(fp.read())
            fp.close()
            msg.attach(msgImage)
        
        text = msg.as_string()
        # Send the message via local SMTP server.
        #yag = yagmail.SMTP(sender)
        #yag.send("parfa30@gmail.com",nl_html,self.DESI_Log.telem_plots_file)
        s = smtplib.SMTP('localhost')
        s.sendmail(sender, user_email, text)
        s.quit()
