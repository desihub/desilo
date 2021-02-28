#Imports
import os, sys
import glob
import time, sched
from datetime import datetime
import numpy as np
import pandas as pd
import socket
import psycopg2
import subprocess
import pytz

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

import ephem
from util import sky_calendar

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

sys.path.append(os.getcwd())
sys.path.append('./ECLAPI-8.0.12/lib')
import nightlog as nl


class Report():
    def __init__(self, type):

        self.test = False 

        self.report_type = type
        self.utc = TimezoneInfo()
        self.kp_zone = TimezoneInfo(utc_offset=-7*u.hour)
        self.zones = [self.utc, self.kp_zone]
        self.datefmt = DateFormatter(format="%m/%d/%Y %H:%M:%S")
        self.timefmt = DateFormatter(format="%m/%d %H:%M")

        self.line = Div(text='-----------------------------------------------------------------------------------------------------------------------------', width=1000)
        self.line2 = Div(text='-----------------------------------------------------------------------------------------------------------------------------', width=1000)

        self.nl_file = None

        self.intro_subtitle = Div(text="Connect to Night Log", css_classes=['subt-style'])
        self.time_note = Div(text="<b> Note: </b> Enter all times as HH:MM (18:18 = 1818 = 6:18pm) in Kitt Peak local time. Either enter the time or hit the <b> Now </b> button if it just occured.", css_classes=['inst-style'])
        self.exp_info = Div(text="Mandatory fields have an asterisk*.", css_classes=['inst-style'],width=500)

        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        if 'desi' in hostname:
            self.location = 'kpno'
            self.conn = psycopg2.connect(host="desi-db", port="5442", database="desi_dev", user="desi_reader", password="reader")
        elif 'app' in hostname: #this is not true. Needs to change.
            self.location = 'nersc'
        else:
            self.location = 'other'

        nw_dirs = {'nersc':'/global/cfs/cdirs/desi/spectro/nightwatch/nersc/', 'kpno':'/exposures/nightwatch/', 'other':None}
        self.nw_dir = nw_dirs[self.location]
        self.nl_dir = os.environ['NL_DIR']

        self.your_name = TextInput(title ='Your Name', placeholder = 'John Smith')

        self.intro_txt = Div(text=' ')
        self.comment_txt = Div(text=" ", css_classes=['inst-style'], width=1000)

        self.date_init = Select(title="Existing Night Logs")
        self.time_title = Paragraph(text='Time* (Kitt Peak local time)', align='center')
        self.now_btn = Button(label='Now', css_classes=['now_button'], width=75)
        days = [d for d in os.listdir(self.nl_dir) if os.path.isdir(os.path.join(self.nl_dir, d))]
        init_nl_list = np.sort([day for day in days if 'nightlog_meta.json' in os.listdir(os.path.join(self.nl_dir,day))])[::-1][0:10]
        self.date_init.options = list(init_nl_list)
        self.date_init.value = init_nl_list[0]
        self.connect_txt = Div(text=' ', css_classes=['alert-style'])

        self.connect_bt = Button(label="Connect to Existing Night Log", css_classes=['connect_button'])
        self.nl_info = Div(text="Night Log Info:", css_classes=['inst-style'], width=500)        
        self.img_subtitle = Div(text="Images", css_classes=['subt-style'])
        
        self.img_upinst = Div(text="Include images in the Night Log by uploading a png image from your local computer. Select file, write a comment and click Add", css_classes=['inst-style'], width=1000)
        self.img_upinst2 = Div(text="           Choose image to include with comment:  ", css_classes=['inst-style'])
        self.img_upload = FileInput(accept=".png")
        self.img_upload.on_change('value', self.upload_image)
        # self.img_upload_comments_other = FileInput(accept=".png")
        # self.img_upload_comments_other.on_change('value', self.upload_image_comments_other)
        self.img_upload_comments_os = FileInput(accept=".png")
        self.img_upload_comments_os.on_change('value', self.upload_image_comments_os)
        self.img_upload_comments_dqs = FileInput(accept=".png")
        self.img_upload_comments_dqs.on_change('value', self.upload_image_comments_dqs)
        self.img_upload_problems = FileInput(accept=".png")
        self.img_upload_problems.on_change('value', self.upload_image_problems)


        self.img_btn = Button(label='Add', css_classes=['add_button'])
        self.img_alert = Div(text=" ",width=1000)

        self.milestone_time = None
        self.plan_time = None

        self.DESI_Log = None
        self.save_telem_plots = False

    def clear_input(self, items):
        """ After submitting something to the log, this will clear the form.
        """
        if isinstance(items, list):
            for item in items:
                item.value = None
        else:
            items.value = None

    def get_exposure_list(self):
        try:
            dir_ = self.nw_dir+'/'+self.date_init.value
            exposures = []
            for path, subdirs, files in os.walk(dir_): 
                for s in subdirs: 
                    exposures.append(s)  
            exposures = list([str(int(e)) for e in list(exposures)])
            self.exp_select.options = exposures
            self.exp_select.value = exposures[0] 
        except:
            self.exp_select.options = []

    def get_intro_layout(self):
        intro_layout = layout([self.title,
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
        <li>Add the major elements of the night plan found at the link below in the order expected for their completion using the <b>Add/New</b> button.</li>
        <li>You can recall submitted plans using their index, as found on the Current DESI Night Log tab.</li>
        <li>If you'd like to modify a submitted plan, <b>Load</b> the index, make your modifications, and then press <b>Update</b></li>.
        </ul>
        """
        self.plan_inst = Div(text=inst, css_classes=['inst-style'], width=1000)
        self.plan_txt = Div(text='<a href="https://desi.lbl.gov/trac/wiki/DESIOperations/ObservingPlans/">Tonights Plan Here</a>', css_classes=['inst-style'], width=500)
        self.plan_order = TextInput(title ='Plan Index (see Current NL):', placeholder='0', value=None, width=75)
        self.plan_input = TextAreaInput(placeholder="description", rows=5, cols=3, title="Enter item of the night plan:",max_length=5000, width=800)
        self.plan_btn = Button(label='Update', css_classes=['add_button'], width=75)
        self.plan_new_btn = Button(label='Add New', css_classes=['add_button'])
        self.plan_load_btn = Button(label='Load', css_classes=['connect_button'], width=75)
        self.plan_alert = Div(text=' ', css_classes=['alert-style'])

        plan_layout = layout([self.title,
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
        <b>Plan</b> tab. Include exposure numbers that correspond with the accomplishment, and if applicable, indicate any exposures to ignore in a series.</li>
        <li>If you'd like to modify a submitted milestone, <b>Load</b> the index, make your modifications, and then press <b>Update</b>.</li>
        <li>At the end of your shift, either at the end of the night or half way through, summarize the activities of the night in the <b>End fo Night Summary</b>.</li>
        </ul>
        """
        self.milestone_inst = Div(text=inst, css_classes=['inst-style'],width=1000)
        self.milestone_input = TextAreaInput(placeholder="Description", title="Enter a Milestone:", rows=5, cols=3, max_length=5000, width=800)
        self.milestone_exp_start = TextInput(title ='Exposure Start', placeholder='12345', value=None, width=200)
        self.milestone_exp_end = TextInput(title='Exposure End', placeholder='12345', value=None, width=200)
        self.milestone_exp_excl = TextInput(title='Excluded Exposures', placeholder='12346', value=None, width=200)
        self.milestone_btn = Button(label='Update', css_classes=['add_button'],width=75)
        self.milestone_new_btn = Button(label='Add New Milestone', css_classes=['add_button'], width=300)
        self.milestone_load_num = TextInput(title='Milestone Index', placeholder='0', value=None, width=75)
        self.milestone_load_btn = Button(label='Load', css_classes=['connect_button'], width=75)
        self.milestone_alert = Div(text=' ', css_classes=['alert-style'])
        self.summary = TextAreaInput(rows=10, title='End of Night Summary',max_length=5000)
        self.summary_btn = Button(label='Add Summary', css_classes=['add_button'], width=300)

        milestone_layout = layout([self.title,
                        self.milestone_subtitle,
                        self.milestone_inst,
                        [self.milestone_input,[self.milestone_load_num, self.milestone_load_btn, self.milestone_btn]] ,
                        [self.milestone_exp_start,self.milestone_exp_end, self.milestone_exp_excl],
                        [self.milestone_new_btn],
                        self.milestone_alert,
                        self.line,
                        self.summary,
                        self.summary_btn,
                        ], width=1000)
        self.milestone_tab = Panel(child=milestone_layout, title='Milestones')

    def exp_layout(self):
        self.exp_comment = TextAreaInput(title ='Comment/Remark', placeholder = 'Humidity high for calibration lamps',value=None,rows=10, cols=5,width=800,max_length=5000)
        self.exp_time = TextInput(placeholder = '20:07',value=None, width=100) #title ='Time in Kitt Peak local time*', 
        self.exp_btn = Button(label='Add/Update', css_classes=['add_button'])
        self.exp_load_btn = Button(label='Load', css_classes=['connect_button'], width=75)
        self.exp_alert = Div(text=' ', css_classes=['alert-style'])
        self.dqs_load_btn = Button(label='Load', css_classes=['connect_button'], width=75)

    def get_os_exp_layout(self):
        self.exp_layout()
        exp_subtitle = Div(text="Nightly Progress", css_classes=['subt-style'])
        inst="""<ul>
        <li>Throughout the night record the progress, including comments on calibrations and exposures. 
        All exposures are recorded in the eLog, so only enter information that can provide additional information.</li>
        <li>If you enter an Exposure Number, the Night Log will include data from the eLog and connect it to any inputs
        from the Data Quality Scientist.</li>
        <li>If you'd like to modify a submitted comment, enter the time of the submission and hit the b>Load</b> button. 
        After making your modifications, resubmit using the <b>Add/Update</b>.</li>
        </ul>
        """
        exp_inst = Div(text=inst, width=800, css_classes=['inst-style'])
        
        self.exp_exposure_start = TextInput(title='Exposure Number: First', placeholder='12345', value=None, width=200)
        self.exp_exposure_finish = TextInput(title='Exposure Number: Last', placeholder='12346', value=None, width=200)

        self.exp_layout = layout(children=[self.title,
                        exp_subtitle,
                        exp_inst,
                        self.time_note,
                        self.exp_info,
                        [self.time_title, self.exp_time, self.now_btn, self.exp_load_btn],
                        [self.exp_exposure_start, self.exp_exposure_finish],
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
        After making your modifications, resubmit using the <b>Add/Update</b>.</li>
        </ul>
        """
        exp_inst = Div(text=inst, css_classes=['inst-style'], width=1000)

        self.exp_comment = TextAreaInput(title ='Comment/Remark', placeholder = 'CCD4 has some bright columns',value=None,rows=10, cols=5,width=500,max_length=5000)
        self.quality_title = Div(text='Data Quality: ', css_classes=['inst-style'])
        
        self.exp_select = Select(title='(1) Select Exposure',options=['None'],width=150)
        self.exp_enter = TextInput(title='(2) Enter Exposure', placeholder='12345', value=None, width=150)
        self.exp_update = Button(label='Update Selection List', css_classes=['connect_button'], width=200)
        self.exp_option = RadioButtonGroup(labels=['(1) Select','(2) Enter'], active=0, width=200)

        self.get_exposure_list()
        self.exp_layout = layout(self.title,
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
        <li>Describe problems as they come up and at what time they occur. If there is an Alarm ID associated with the problem, 
        include it, but leave blank if not. </li>
        <li>If possible, include a description of the resolution. </li>
        <li>If you'd like to modify or add to a submission, you can <b>Load</b> it using its timestamp. After making the modifications 
        or additions, press the <b>Add/Update</b> button.</li>
        </ul>
        """
        self.prob_inst = Div(text=inst, css_classes=['inst-style'], width=1000)
        self.prob_time = TextInput(placeholder = '20:07', value=None, width=100) #title ='Time in Kitt Peak local time*', 
        self.prob_input = TextAreaInput(placeholder="NightWatch not plotting raw data", rows=10, cols=5, title="Problem Description*:",width=400)
        self.prob_alarm = TextInput(title='Alarm ID', placeholder='12', value=None, width=100)
        self.prob_action = TextAreaInput(title='Resolution/Action',placeholder='description',rows=10, cols=5,width=400)
        self.prob_btn = Button(label='Add/Update', css_classes=['add_button'])
        self.prob_load_btn = Button(label='Load', css_classes=['connect_button'], width=75)
        self.prob_alert = Div(text=' ', css_classes=['alert-style'])

        prob_layout = layout([self.title,
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
        <li>Every hour, as part of the OS checklist, include a description of the weather observing conditions.</li>
        <li>Additional weather and observing condition information will be added to the table below and the Night Log when you <b>Add Weather Description</b></li>
        <li>Below the table there are plots of the ongoing telemetry for the observing conditions. These will be added to the Night Log when submitted at the end of the night.</li> 
        </ul>
        """
        self.weather_inst = Div(text=inst, width=1000, css_classes=['inst-style'])

        data = pd.DataFrame(columns = ['Time','desc','temp','wind','humidity','seeing','tput','skylevel'])
        self.weather_source = ColumnDataSource(data)
        obs_columns = [TableColumn(field='Time', title='Time (UTC)', width=50, formatter=self.timefmt),
                   TableColumn(field='desc', title='Description', width=150),
                   TableColumn(field='temp', title='Temperature (C)', width=75),
                   TableColumn(field='wind', title='Wind Speed (mph)', width=75),
                   TableColumn(field='humidity', title='Humidity (%)', width=50),
                   TableColumn(field='seeing', title='Seeing (arcsec)', width=50),
                   TableColumn(field='tput', title='Throughput', width=50),
                   TableColumn(field='skylevel', title='Sky Level', width=50)] #, 

        self.weather_table = DataTable(source=self.weather_source, columns=obs_columns, width=1000)

        telem_data = pd.DataFrame(columns = ['tel_time','tower_time','exp_time','exp','mirror_temp','truss_temp','air_temp','humidity','wind_speed','airmass','exptime','seeing'])
        self.telem_source = ColumnDataSource(telem_data)

        plot_tools = 'pan,wheel_zoom,lasso_select,reset,undo,save'
        p1 = figure(plot_width=800, plot_height=300, x_axis_label='UTC Time', y_axis_label='Temp (C)',x_axis_type="datetime", tools=plot_tools)
        p2 = figure(plot_width=800, plot_height=300, x_axis_label='UTC Time', y_axis_label='Humidity (%)', x_axis_type="datetime",tools=plot_tools)
        p3 = figure(plot_width=800, plot_height=300, x_axis_label='UTC Time', y_axis_label='Wind Speed (mph)', x_axis_type="datetime",tools=plot_tools)
        p4 = figure(plot_width=800, plot_height=300, x_axis_label='UTC Time', y_axis_label='Airmass', x_axis_type="datetime",tools=plot_tools)
        p5 = figure(plot_width=800, plot_height=300, x_axis_label='UTC Time', y_axis_label='Exptime (sec)', x_axis_type="datetime",tools=plot_tools)
        p6 = figure(plot_width=800, plot_height=300, x_axis_label='Exposure', y_axis_label='Seeing (arcsec)', tools=plot_tools)

        p1.circle(x = 'tel_time',y='mirror_temp',source=self.telem_source,color='orange', size=10, alpha=0.5) #legend_label = 'Mirror', 
        p1.circle(x = 'tel_time',y='truss_temp',source=self.telem_source, size=10, alpha=0.5) #legend_label = 'Truss', 
        p1.circle(x = 'tel_time',y='air_temp',source=self.telem_source, color='green', size=10, alpha=0.5) #legend_label = 'Air',
        p1.legend.location = "top_right"

        p2.circle(x = 'tower_time',y='humidity',source=self.telem_source, size=10, alpha=0.5)
        p3.circle(x = 'tower_time',y='wind_speed',source=self.telem_source, size=10, alpha=0.5)
        p4.circle(x = 'exp_time',y='airmass',source=self.telem_source, size=10, alpha=0.5)
        p5.circle(x = 'exp_time',y='exptime',source=self.telem_source, size=10, alpha=0.5)
        p6.circle(x = 'exp',y='seeing',source=self.telem_source, size=10, alpha=0.5)

        self.weather_desc = TextInput(title='Weather Description', placeholder='description', value=None, width=500)
        self.weather_btn = Button(label='Add Weather Description', css_classes=['add_button'], width=100)
        self.weather_alert = Div(text=' ', css_classes=['alert-style'])

        if self.report_type == 'OS':
            weather_layout = layout([self.title,
                            self.weather_subtitle,
                            self.weather_inst,
                            [self.weather_desc, self.weather_btn],
                            self.weather_alert,
                            self.weather_table,
                            p6,p1,p2,p3,p4,p5], width=1000)
        else:
            weather_layout = layout([self.title,
                self.weather_subtitle,
                self.weather_table,
                p6,p1,p2,p3,p4,p5], width=1000)
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

        self.check_time = TextInput(placeholder = '20:07', value=None) #title ='Time in Kitt Peak local time*', 
        self.check_alert = Div(text=" ", css_classes=['alert-style'])
        self.check_btn = Button(label='Submit', css_classes=['add_button'])
        self.check_comment = TextAreaInput(title='Comment', placeholder='comment if necessary', rows=3, cols=3)
        
        if self.report_type == 'OS':
            self.checklist.labels = self.os_checklist
            self.check_subtitle = Div(text="OS Checklist", css_classes=['subt-style'])
        elif self.report_type == 'DQS':
            self.checklist.labels = self.dqs_checklist
            self.check_subtitle = Div(text="DQS Checklist", css_classes=['subt-style'])
        checklist_layout = layout(self.title,
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
        self.nl_text = Div(text=" ", css_classes=['inst-style'], width=1000)
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

        nl_layout = layout([self.title,
                        self.nl_subtitle,
                        self.nl_alert,
                        self.nl_text,
                        self.exptable_alert,
                        self.exp_table,
                        self.nl_submit_btn], width=1000)
        self.nl_tab = Panel(child=nl_layout, title="Current DESI Night Log")

    def short_time(self, time, mode):
        """Returns %H%M in whichever time zone selected
        """
        if mode == 'str':
            try:
                t = datetime.strptime(time, "%Y%m%dT%H:%M")
                zone = self.kp_zone #zones[time_select.active]
                time = datetime(t.year, t.month, t.day, t.hour, t.minute, tzinfo = zone)
                return "{}:{}".format(str(time.hour).zfill(2), str(time.minute).zfill(2))
            except:
                return str_time
        if mode == 'dt':
            return "{}:{}".format(str(time.hour).zfill(2), str(time.minute).zfill(2))

    def get_time(self, time):
        """Returns strptime with utc. Takes time zone selection
        """
        date = self.night
        zone = self.kp_zone #zones[time_select.active]
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

    def get_strftime(self, time):
        date = self.date_init.value
        year, month, day = int(date[0:4]), int(date[4:6]), int(date[6:8])
        d = datetime(year, month, day)
        dt = datetime.combine(d,time)
        return dt.strftime("%Y%m%dT%H:%M")

    def get_night(self, mode='connect'):
        if mode == 'connect':
            try:
                date = datetime.strptime(self.date_init.value, '%Y%m%d')
            except:
                date = datetime.now()
        elif mode == 'init':
            date = datetime.now()
        self.night = str(date.year)+str(date.month).zfill(2)+str(date.day).zfill(2)
        self.DESI_Log=nl.NightLog(str(date.year),str(date.month).zfill(2),str(date.day).zfill(2))

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
                meta_dict = self.DESI_Log.get_meta_data()
                self.your_name.value = meta_dict['{}_1'.format(self.report_type.lower())]+' '+meta_dict['{}_last'.format(self.report_type.lower())]
            elif self.report_type == 'OS':
                meta_dict = self.DESI_Log.get_meta_data()
                self.os_name_1.value = meta_dict['{}_1_first'.format(self.report_type.lower())]+' '+meta_dict['{}_1_last'.format(self.report_type.lower())]
                self.os_name_2.value = meta_dict['{}_2_first'.format(self.report_type.lower())]+' '+meta_dict['{}_2_last'.format(self.report_type.lower())]

            self.display_current_header()
            self.nl_file = os.path.join(self.DESI_Log.root_dir,'nightlog.html')
            self.nl_subtitle.text = "Current DESI Night Log: {}".format(self.nl_file)

            if self.report_type == 'OS':
                plan_txt_text="https://desi.lbl.gov/trac/wiki/DESIOperations/ObservingPlans/OpsPlan{}".format(self.night)
                self.plan_txt.text = '<a href={}>Tonights Plan Here</a>'.format(plan_txt_text)
                self.LO.value = meta_dict['os_lo_1']+' '+meta_dict['os_lo_last']
                self.OA.value = meta_dict['os_oa_1']+' '+meta_dict['os_oa_last']
                if os.path.exists(self.DESI_Log.contributer_file):
                    cont_txt = ''
                    f =  open(self.DESI_Log.contributer_file, "r")
                    for line in f:
                        cont_txt += line
                    self.contributer_list.value = cont_txt
            self.current_nl()

        else:
            self.connect_txt.text = 'The Night Log for this {} is not yet initialized.'.format(self.date_init.value)

    def initialize_log(self):
        """ Initialize Night Log with Input Date
        """

        date = datetime.now()
        self.get_night('init')
        LO_firstname, LO_lastname = self.LO.value.split(' ')[0], ' '.join(self.LO.value.split(' ')[1:])
        OA_firstname, OA_lastname = self.OA.value.split(' ')[0], ' '.join(self.OA.value.split(' ')[1:])
        os_1_firstname, os_1_lastname = self.os_name_1.value.split(' ')[0], ' '.join(self.os_name_1.value.split(' ')[1:])
        os_2_firstname, os_2_lastname = self.os_name_2.value.split(' ')[0], ' '.join(self.os_name_2.value.split(' ')[1:])

        eph = sky_calendar()
        time_sunset = self.get_strftime(eph['sunset'])
        time_sunrise = self.get_strftime(eph['sunrise'])
        time_moonrise = self.get_strftime(eph['moonrise'])
        time_moonset = self.get_strftime(eph['moonset'])
        illumination = eph['illumination']
        dusk_18_deg = self.get_strftime(eph['dusk_astronomical'])
        dawn_18_deg = self.get_strftime(eph['dawn_astronomical'])

        self.DESI_Log.initializing()
        self.DESI_Log.get_started_os(os_1_firstname,os_1_lastname,os_2_firstname,os_2_lastname,LO_firstname,LO_lastname,
            OA_firstname,OA_lastname,time_sunset,dusk_18_deg,dawn_18_deg,time_sunrise,time_moonrise,time_moonset,illumination)

        #update_weather_source_data()
        self.connect_txt.text = 'Night Log is Initialized'
        self.DESI_Log.write_intro()
        self.display_current_header()
        self.current_nl()
        days = [f for f in os.listdir(self.nl_dir) if os.path.isdir(os.path.join(self.nl_dir,f))]
        init_nl_list = np.sort([day for day in days if 'nightlog_meta.json' in os.listdir(os.path.join(self.nl_dir,day))])[::-1][0:10]
        self.date_init.options = list(init_nl_list)
        self.date_init.value = init_nl_list[0]

    def display_current_header(self):
        path = os.path.join(self.DESI_Log.root_dir, "header.html")
        nl_file = open(path, 'r')
        intro = ''
        for line in nl_file:
            intro =  intro + line + '\n'
        self.intro_txt.text = intro
        nl_file.closed

    def current_nl(self):
        try:
            now = datetime.now()
            self.DESI_Log.finish_the_night()
            path = os.path.join(self.DESI_Log.root_dir,"nightlog.html")
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
            self.get_seeing()
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
        if self.location == 'kpno':
            exp_df = pd.read_sql_query(f"SELECT * FROM exposure WHERE night = '{self.night}'", self.conn)
            if len(exp_df.date_obs) != 0:
                time = exp_df.date_obs.dt.tz_convert('US/Arizona')
                exp_df['date_obs'] = time
                self.explist_source.data = exp_df[['date_obs','id','tileid','program','sequence','flavor','exptime','airmass','seeing']].sort_values(by='id',ascending=False) 
                exp_df = exp_df.sort_values(by='id')
                exp_df.to_csv(self.DESI_Log.explist_file, index=False)
            else:
                self.exptable_alert.text = f'No exposures available for night {self.night}'
        else:
            self.exptable_alert.text = 'Cannot connect to Exposure Data Base'

    def get_weather(self):
        if os.path.exists(self.DESI_Log.weather):
            obs_df = pd.read_pickle(self.DESI_Log.weather)
            t = [datetime.strptime(tt, "%Y%m%dT%H:%M") for tt in obs_df['Time']]
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
            
        self.seeing_df = pd.DataFrame()
        self.seeing_df['Seeing'] = seeing
        self.seeing_df['Exps'] = exps
        self.seeing_df.to_csv(os.path.join(self.DESI_Log.root_dir,'seeing.csv'),index=False)
        # KH added to avoid issues with X11 and Display (we only need the png)
        figure = plt.figure()
        plt.plot(self.seeing_df.Exps, self.seeing_df.Seeing,'o')
        plt.xlabel("Exposure")
        plt.ylabel("Seeing (arcsec)")
        plt.savefig(os.path.join(self.DESI_Log.root_dir,'seeing.png'))
        plt.close(figure)

    def make_telem_plots(self):
        start_utc = '{} {}'.format(int(self.night), '13:00:00')
        end_utc = '{} {}'.format(int(self.night)+1, '13:00:00')
        tel_df  = pd.read_sql_query(f"SELECT * FROM environmentmonitor_telescope WHERE time_recorded > '{start_utc}' AND time_recorded < '{end_utc}'", self.conn)
        exp_df = pd.read_sql_query(f"SELECT * FROM exposure WHERE night = '{self.night}'", self.conn)
        tower_df = pd.read_sql_query(f"SELECT * FROM environmentmonitor_tower WHERE time_recorded > '{start_utc}' AND time_recorded < '{end_utc}'", self.conn) 

        #self.get_seeing()
        telem_data = pd.DataFrame(columns = ['tel_time','tower_time','exp_time','exp','mirror_temp','truss_temp','air_temp','temp','humidity','wind_speed','airmass','exptime','seeing'])
        telem_data.tel_time = tel_df.time_recorded.dt.tz_convert('US/Arizona')
        telem_data.tower_time = tower_df.time_recorded.dt.tz_convert('US/Arizona')
        telem_data.exp_time = exp_df.date_obs.dt.tz_convert('US/Arizona')
        telem_data.exp = self.seeing_df.Exps
        telem_data.mirror_temp = tel_df.mirror_temp
        telem_data.truss_temp = tel_df.truss_temp
        telem_data.air_temp = tel_df.air_temp
        telem_data.temp = tower_df.temperature
        telem_data.humidity = tower_df.humidity
        telem_data.wind_speed = tower_df.wind_speed
        telem_data.airmass = exp_df.airmass
        telem_data.exptime = exp_df.exptime
        telem_data.seeing = self.seeing_df.Seeing

        self.telem_source.data = telem_data

        if self.save_telem_plots:
            if set(list(exp_df.seeing)) == set([None]):
                sky_monitor = False
                fig = plt.figure(figsize= (8, 15))
                #fig, axarr = plt.subplots(5, 1, figsize = (8,15), sharex=True)
            else:
                sky_monitor = True
                fig, axarr = plt.subplots(9, 1, figsize = (8,20), sharex=True)

            ax1 = fig.add_subplot(6,1,1)
            ax1.scatter(telem_data.exp, telem_data.seeing, s=5, label='Seeing')
            ax1.set_ylabel("Seeing (arcsec)")
            ax1.grid(True)
            ax1.set_xlabel("Exposure")
            #ax = axarr.ravel()
            ax2 = fig.add_subplot(6,1,2)
            ax2.scatter(tel_df.time_recorded.dt.tz_convert('US/Arizona'), tel_df.mirror_temp, s=5, label='mirror temp')    
            ax2.scatter(tel_df.time_recorded.dt.tz_convert('US/Arizona'), tel_df.truss_temp, s=5, label='truss temp')  
            ax2.scatter(tel_df.time_recorded.dt.tz_convert('US/Arizona'), tel_df.air_temp, s=5, label='air temp') 
            ax2.set_ylabel("Telescop Temperature (C)")
            ax2.legend()
            ax2.grid(True)
            ax2.tick_params(labelbottom=False)

            ax3 = fig.add_subplot(6,1,3, sharex = ax2)
            ax3.scatter(tower_df.time_recorded.dt.tz_convert('US/Arizona'), tower_df.humidity, s=5, label='humidity') 
            ax3.set_ylabel("Humidity %")
            ax3.grid(True)
            ax3.tick_params(labelbottom=False)

            ax4 = fig.add_subplot(6,1,4, sharex=ax2) 
            ax4.scatter(tower_df.time_recorded.dt.tz_convert('US/Arizona'), tower_df.wind_speed, s=5, label='wind speed')
            ax4.set_ylabel("Wind Speed (mph)")
            ax4.grid(True)
            ax4.tick_params(labelbottom=False)

            ax5 = fig.add_subplot(6,1,5, sharex=ax2)
            ax5.scatter(exp_df.date_obs.dt.tz_convert('US/Arizona'), exp_df.airmass, s=5, label='airmass')
            ax5.set_ylabel("Airmass")
            ax5.grid(True)
            ax5.tick_params(labelbottom=False)

            ax6 = fig.add_subplot(6,1,6, sharex=ax2)
            ax6.scatter(exp_df.date_obs.dt.tz_convert('US/Arizona'), exp_df.exptime, s=5, label='exptime')
            ax6.set_ylabel("Exposure time (s)")
            ax6.grid(True)

            if sky_monitor:
                ax6.scatter(exp_df.date_obs.dt.tz_convert('US/Arizona'), exp_df.seeing, s=5, label='seeing')   
                ax6.set_ylabel("Seeing")

                ax7.scatter(exp_df.date_obs.dt.tz_convert('US/Arizona'), exp_df.transpar, s=5, label='transparency')
                ax7.set_ylabel("Transparency (%)")

                ax8.scatter(exp_df.date_obs.dt.tz_convert('US/Arizona'), exp_df.skylevel, s=5, label='Sky Level')      
                ax8.set_ylabel("Sky level (AB/arcsec^2)")

            ax6.set_xlabel("Local Time (MST)")
            ax6.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M', tz=pytz.timezone("US/Arizona")))
            ax6.tick_params(labelrotation=45)
            fig.suptitle("Telemetry for obsday={}".format(self.night))
            fig.tight_layout()

            plt.savefig(self.DESI_Log.telem_plots_file)

                
    def exp_to_html(self):
        exp_df = pd.read_csv(self.DESI_Log.explist_file)
        exp_df = exp_df[['night','id','program','sequence','flavor','exptime']]
        exp_html = exp_df.to_html()
        return exp_html


    def check_add(self):
        """add checklist time to Night Log
        """
        complete = self.checklist.active
        check_time = datetime.now().strftime("%Y%m%dT%H:%M")
        if len(complete) == len(self.checklist.labels):
            self.DESI_Log.write_checklist([check_time, self.check_comment.value], self.report_type)
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
            ts = self.get_time(datetime.now())
        else: 
            ts = self.plan_time
        self.DESI_Log.write_plan([ts, self.plan_input.value])
        self.plan_alert.text = 'Last item input: {}'.format(self.plan_input.value)
        self.clear_input([self.plan_order, self.plan_input])
        self.plan_time = None

    def milestone_add(self):
        if self.milestone_time is None:
            ts = self.get_time(datetime.now())
        else:
            ts = self.milestone_time
        self.DESI_Log.write_milestone([ts, self.milestone_input.value, self.milestone_exp_start.value, self.milestone_exp_end.value, self.milestone_exp_excl.value])
        self.milestone_alert.text = 'Last Milestone Entered: {}'.format(self.milestone_input.value)
        self.clear_input([self.milestone_input, self.milestone_exp_start, self.milestone_exp_end, self.milestone_exp_excl])
        self.milestone_time = None

    def weather_add(self):
        """Adds table to Night Log
        """
        now = datetime.now().astimezone(tz=self.kp_zone) 
        now_time = self.short_time(datetime.strftime(now, "%Y%m%dT%H:%M"), mode='str')
        time = self.get_time(now_time) #self.short_time(datetime.strftime(now, "%Y%m%dT%H:%M"), mode='str')
        if self.location == 'kpno':
            self.make_telem_plots()
            telem_df = pd.DataFrame(self.telem_source.data)
            this_data = telem_df.iloc[-1]
            desc = self.weather_desc.value
            temp = this_data.temp
            wind = this_data.wind_speed
            humidity = this_data.humidity
            seeing = this_data.seeing
            #tput = this_data.tput
            #skylevel = this_data.skylevel
            data = [time, desc, temp, wind, humidity, seeing, None, None]
            df = self.DESI_Log.write_weather(data)

        else: 
            data = [time, self.weather_desc.value, None, None, None, None, None, None]
            df = self.DESI_Log.write_weather(data)
            self.weather_alert.text = 'Not connected to the telemetry DB. Only weather description will be recorded.'

        self.clear_input([self.weather_desc])
        self.get_weather()

    def image_uploaded(self, mode='comment'):
        img_data = None
        img_name = None

        if mode == 'comment':         
            if self.report_type == 'DQS':
                if hasattr(self, 'img_upload_comments_dqs') and self.img_upload_comments_dqs.filename not in [None,'']:
                    img_data = self.img_upload_comments_dqs.value.encode('utf-8')
                    img_name = str(self.img_upload_comments_dqs.filename)
            else:
                if self.exp_comment.value not in [None, ''] and hasattr(self, 'img_upload_comments_os') and self.img_upload_comments_os.filename not in [None,'']:
                    img_data = self.img_upload_comments_os.value.encode('utf-8')
                    img_name = str(self.img_upload_comments_os.filename)

        elif mode == 'problem':
            if hasattr(self, 'img_upload_problems') and self.img_upload_problems.filename not in [None, '']:
                img_data = self.img_upload_problems.value.encode('utf-8')
                img_name = str(self.img_upload_problems.filename)

        self.image_location_on_server = f'{os.environ["NL_DIR"]}/{self.night}/images/{img_name}' #http://desi-www.kpno.noao.edu:8090/nightlogs
        preview = '<img src="{}" style="width:300px;height:300px;">'.format(self.image_location_on_server)
        return img_name, img_data, preview
       
    def prob_add(self):
        """Adds problem to nightlog
        """
        if self.report_type == 'Other':
            name = self.your_name.value
        else:
            name = None

        img_name, img_data, preview = self.image_uploaded('problem')
        data = [self.get_time(self.prob_time.value), self.prob_input.value, self.prob_alarm.value, self.prob_action.value, name]
        self.DESI_Log.write_problem(data, self.report_type, img_name=img_name, img_data=img_data)

        # Preview
        if img_name != None:
            preview += "<br>"
            preview += "Last Problem Input: '{}' at {}".format(self.prob_input.value, self.prob_time.value)
            self.prob_alert.text = preview
            self.img_upload_problems = FileInput(accept=".png")
        else:
            self.prob_alert.text = "Last Problem Input: '{}' at {}".format(self.prob_input.value, self.prob_time.value)
        self.clear_input([self.prob_time, self.prob_input, self.prob_alarm, self.prob_action])

    def progress_add(self):
        if self.exp_time.value not in [None, 'None'," ", ""]:
            data = [self.get_time(self.exp_time.value), self.exp_comment.value, self.exp_exposure_start.value, self.exp_exposure_finish.value]
            img_name, img_data, preview = self.image_uploaded('comment')

            self.DESI_Log.write_os_exp(data, img_name=img_name, img_data=img_data)
            if img_name is not None:
                preview += "<br>"
                preview += "A comment was added at {}".format(self.exp_time.value)
                self.exp_alert.text = preview
                self.img_upload_comments_os=FileInput(accept=".png")
            else:
                self.exp_alert.text = 'Last Input was at {}'.format(self.exp_time.value)
            self.clear_input([self.exp_time, self.exp_comment, self.exp_exposure_start, self.exp_exposure_finish])
        else:
            self.exp_alert.text = 'Could not submit entry for Observation Type *{}* because not all mandatory fields were filled.'.format(self.hdr_type.value)
    
    def comment_add(self):
        if self.your_name.value in [None,' ','']:
            self.comment_alert.text = 'You need to enter your name on first page before submitting a comment'
        else:
            if self.exp_time.value not in [None, 'None'," ", ""]:
                img_name, img_data, preview = self.image_uploaded('comment')
                data = [self.get_time(self.exp_time.value), self.exp_comment.value, self.exp_exposure_start.value, self.exp_exposure_finish.value, self.your_name.value]
                self.DESI_Log.write_other_exp(data, img_name=img_name, img_data=img_data)

                if img_name is not None:
                    preview += "<br>"
                    preview += "A comment was added at {}".format(self.exp_time.value)
                    self.exp_alert.text = preview
                    self.img_upload_comments=FileInput(accept=".png")
                else:
                    self.exp_alert.text = "A comment was added at {}".format(self.exp_time.value)
                self.clear_input([self.exp_time, self.exp_comment])

    def exp_add(self):
        quality = self.quality_list[self.quality_btns.active]
        if self.exp_option.active == 0:
            exp_val = int(self.exp_select.value)
        elif self.exp_option.active ==1:
            exp_val = int(self.exp_enter.value)
        now = datetime.now().astimezone(tz=self.kp_zone) 
        now_time = self.short_time(datetime.strftime(now, "%Y%m%dT%H:%M"), 'str')

        img_name, img_data, preview = self.image_uploaded('comment')
        data = [self.get_time(now_time), exp_val, quality, self.exp_comment.value]
        self.DESI_Log.write_dqs_exp(data, img_name=img_name, img_data=img_data)

        if img_name is not None:
            preview += "<br>"
            preview += "A comment was added at {}".format(self.exp_time.value)
            self.exp_alert.text = preview
            self.img_upload_comments_dqs=FileInput(accept=".png")
        else:
            self.exp_alert.text = 'Last Exposure input {} at {}'.format(exp_val, now_time)
        self.clear_input([self.exp_time, self.exp_enter, self.exp_select, self.exp_comment])

    def plan_load(self):
        b, item = self.DESI_Log.load_index(self.plan_order.value, 'plan')
        if b:
            self.plan_order.value = str(item.index[0])
            self.plan_input.value = item['Objective'].values[0]
            self.plan_time = item['Time'].values[0]
        else:
            self.plan_alert.text = "That plan item doesn't exist yet"

    def dqs_load(self):
        if self.exp_option.active == 0:
             exp = int(self.exp_select.value)
        if self.exp_option.active == 1:
            exp = int(self.exp_enter.value)
        b, item = self.DESI_Log.load_exp(exp)
        if b:
            self.exp_comment.value = item['Comment'].values[0]
            qual = np.where(self.quality_list==item['Quality'].values[0])[0]
            self.quality_btns.active = int(qual)
        else:
            self.exp_alert.text = "An input for that exposure doesn't exist."

    def milestone_load(self):
        b, item = self.DESI_Log.load_index(int(self.milestone_load_num.value), 'milestone')
        if b:
            self.milestone_input.value = item['Desc'].values[0]
            self.milestone_exp_start.value = item['Exp_Start'].values[0]
            self.milestone_exp_end.value = item['Exp_Stop'].values[0]
            self.milestone_exp_excl.value = item['Exp_Excl'].values[0]
            self.milestone_time = item['Time'].values[0]
        else:
            self.milestone_alert.text = "That milestone index doesn't exist yet"

    def load_exposure(self):
        #Check if progress has been input with a given timestamp
        _exists, item = self.DESI_Log.load_timestamp(self.get_time(self.exp_time.value), self.report_type, 'exposure')

        if not _exists:
            self.exp_alert.text = 'This timestamp does not yet have an input'
        else:
            self.exp_comment.value = item['Comment'].values[0]
            self.exp_exposure_start.value = item['Exp_Start'].values[0]
            self.exp_exposure_finish.value = item['Exp_End'].values[0]

    def load_problem(self):
        #Check if progress has been input with a given timestamp
        _exists, item = self.DESI_Log.load_timestamp(self.get_time(self.prob_time.value), self.report_type, 'problem')

        if not _exists:
            self.prob_alert.text = 'This timestamp does not yet have an input'
        else:
            self.prob_input.value = item['Problem'].values[0]
            self.prob_alarm.value = item['alarm_id'].values[0]
            self.prob_action.value = item['action'].values[0]



    def add_contributer_list(self):
        cont_list = self.contributer_list.value
        self.DESI_Log.add_contributer_list(cont_list)

    def add_summary(self):
        now = datetime.now()
        summary = self.summary.value
        self.DESI_Log.add_summary(summary)
        self.clear_input([self.summary])
        self.milestone_alert.text = 'Summary Entered at {}'.format(self.short_time(now, 'dt'))

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

    # def image_add(self):
    #     """Copies image from the input location to the image folder for the nightlog.
    #     Then calls add_image() from nightlog.py which writes it to the html file
    #     Then gives preview of image of last image.
    #     """
    #     image_loc = self.img_input.value
    #     if image_loc in [None, '']:
    #         # got a local upload
    #         img_data = self.img_upload.value.encode('utf-8')
    #         self.DESI_Log.upload_image(img_data, self.img_comment.value, self.img_upload.filename)
    #         # move to class initialization
    #         image_location_on_server = f'http://desi-www.kpno.noao.edu:8090/nightlogs/{self.night}/images/{self.img_upload.filename}'
    #         preview = '<img src="{}" style="width:300px;height:300px;">'.format(image_location_on_server)
    #         preview += "<br>"
    #         preview += "{}".format(self.img_comment.value)
    #         self.img_alert.text = preview
    #         return
    #     image_name = os.path.split(image_loc)[1]
    #     image_type = os.path.splitext(image_name)[1]
    #     bashCommand1 = "cp {} {}".format(image_loc,self.DESI_Log.image_dir)
    #     bashCommand2 = "cp {} {}".format(image_loc,self.report_type+"_Report/static/images/tmp_img{}".format(image_type))
    #     results = subprocess.run(bashCommand1.split(), text=True, stdout=subprocess.PIPE, check=True)
    #     results = subprocess.run(bashCommand2.split(), text=True, stdout=subprocess.PIPE, check=True)
    #     self.DESI_Log.add_image(os.path.join(self.DESI_Log.image_dir,image_name), self.img_comment.value)
    #     #KH: this is something you need to reconsider. It is bad practice to write into the source code directory
    #     preview = '<img src="{}_Report/static/images/tmp_img{}" style="width:300px;height:300px;">'.format(self.report_type,image_type)
    #     preview += "\n"
    #     preview += "{}".format(self.img_comment.value)
    #     self.img_alert.text = preview
    #     self.clear_input([self.img_input, self.img_comment])

    def time_is_now(self):
        now = datetime.now().astimezone(tz=self.kp_zone) 
        now_time = self.short_time(datetime.strftime(now, "%Y%m%dT%H:%M"), mode='str')
        tab = self.layout.active
        time_input = self.time_tabs[tab]
        try:
            time_input.value = now_time
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

            f = self.nl_file[:-5]
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

        if self.location == 'kpno':
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
        f = self.nl_file
        nl_file=open(f,'r')
        lines = nl_file.readlines()
        nl_html = ' '
        img_names = []
        for line in lines:
            nl_html += line

        # Add images
        x = nl_html.find('Images')
        nl_html = nl_html[:x]
        nl_html += "<h3 id='images'>Images</h3>"
        nl_html += '\n'
        
        if os.path.exists(self.DESI_Log.image_file):
            images = os.listdir(self.DESI_Log.image_dir)
            images = [s for s in images if os.path.splitext(s)[1] != '']
            f = open(self.DESI_Log.image_file,'r')
            image_lines = f.readlines()

            for ii, line in enumerate(image_lines):
                for i, img in enumerate(images):
                    if img in line:
                        nl_html += '<img src="cid:image{}" style="width:300px;height:300px;">'.format(i)
                        nl_html += '\n'
                        nl_html += '{}'.format(image_lines[ii+1])
                        nl_html += '\n'

        # Add exposures
        if os.path.exists(self.DESI_Log.explist_file):
            exp_list = self.exp_to_html()
            nl_html += ("<h3 id='exposures'>Exposures</h3>")
            for line in exp_list:
                nl_html += line

        # Add telem plots
        nl_html += "<h3 id='telem_plots'>Night Telemetry</h3>"
        nl_html += '\n'
        
        if os.path.exists(self.DESI_Log.telem_plots_file):
            nl_html += '<img src="{}">'.format(self.DESI_Log.telem_plots_file)
            nl_html += '\n'

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
