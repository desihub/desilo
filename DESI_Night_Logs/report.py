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

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from bokeh.io import curdoc  # , output_file, save
from bokeh.models import (TextInput, ColumnDataSource, DateFormatter, Paragraph, Button, TextAreaInput, Select,CheckboxGroup, RadioButtonGroup)
from bokeh.models.widgets.markups import Div
from bokeh.layouts import layout, column, row
from bokeh.models.widgets import Panel, Tabs
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

        self.inst_style = {'font-size':'150%'}
        self.subt_style = {'font-size':'200%','font-style':'bold'}
        self.title_style = {'font-size':'250%','font-style':'bold'}
        self.alert_style = {'font-size':'150%','color':'red'}

        self.nl_file = None

        self.intro_subtitle = Div(text="Connect to Night Log",css_classes=['subt-style'])
        self.time_note = Div(text="<b> Note: </b> Enter all times as HHMM (1818 = 18:18 = 6:18pm) in Kitt Peak local time. Either enter the time or hit the <b> Now </b> button if it just occured.", css_classes=['inst-style'])

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
        self.os_name_1 = TextInput(title ='Observing Scientist 1', placeholder = 'Ruth Bader Ginsberg')
        self.os_name_2 = TextInput(title ='Observing Scientist 2', placeholder = "Sandra Day O'Connor")
        self.lo_names = ['None ','Liz Buckley-Geer','Ann Elliott','Parker Fagrelius','Satya Gontcho A Gontcho','James Lasker','Martin Landriau','Claire Poppett','Michael Schubnell','Luke Tyas','Other ']
        self.oa_names = ['None ','Karen Butler','Amy Robertson','Anthony Paat','Dave Summers','Doug Williams','Other ']
        self.intro_txt = Div(text=' ')
        self.comment_txt = Div(text=" ", css_classes=['inst-style'], width=1000)

        self.date_init = Select(title="Existing Night Logs")
        self.time_title = Paragraph(text='Time* (Kitt Peak local time)')#, align='center')
        self.now_btn = Button(label='Now', css_classes=['now_button'], width=50)
        days = [d for d in os.listdir(self.nl_dir) if os.path.isdir(os.path.join(self.nl_dir, d))]
        init_nl_list = np.sort([day for day in days if 'nightlog_meta.json' in os.listdir(os.path.join(self.nl_dir,day))])[::-1][0:10]
        self.date_init.options = list(init_nl_list)
        self.date_init.value = init_nl_list[0]
        self.connect_txt = Div(text=' ', css_classes=['alert-style'])

        self.connect_bt = Button(label="Connect to Existing Night Log", css_classes=['connect_button'])

        self.exp_info = Div(text="Fill In Only Relevant Data. Mandatory fields have an asterisk*.", css_classes=['inst-style'],width=500)
        self.exp_comment = TextAreaInput(title ='Comment/Remark', placeholder = 'Humidity high for calibration lamps',value=None,rows=10, cols=5,width=800,max_length=5000)
        self.exp_time = TextInput(placeholder = '20:07',value=None, width=100) #title ='Time in Kitt Peak local time*',
        self.exp_btn = Button(label='Add', css_classes=['add_button'])
        self.exp_type = Select(title="Exposure Type", value = None, options=['None','Zero','Focus','Dark','Arc','FVC','DESI'])
        self.exp_alert = Div(text=' ', css_classes=['alert-style'])
        self.exp_exposure_start = TextInput(title='Exposure Number: First', placeholder='12345', value=None)
        self.exp_exposure_finish = TextInput(title='Exposure Number: Last', placeholder='12346', value=None)

        self.nl_subtitle = Div(text="Current DESI Night Log: {}".format(self.nl_file), css_classes=['subt-style'])
        self.nl_btn = Button(label='Get Current DESI Night Log', css_classes=['connect_button'])
        self.nl_text = Div(text=" ", css_classes=['inst-style'], width=1000)
        self.nl_alert = Div(text='You must be connected to a Night Log', css_classes=['alert-style'], width=500)
        self.nl_info = Div(text="Night Log Info:", css_classes=['inst-style'], width=500)
        self.exptable_alert = Div(text=" ",css_classes=['alert-style'], width=500)

        self.checklist = CheckboxGroup(labels=[])
        self.check_time = TextInput(placeholder = '20:07', value=None) #title ='Time in Kitt Peak local time*',
        self.check_alert = Div(text=" ", css_classes=['alert-style'])
        self.check_btn = Button(label='Submit', css_classes=['add_button'])
        self.check_comment = TextAreaInput(title='Comment', placeholder='comment if necessary', rows=3, cols=3)

        self.prob_subtitle = Div(text="Problems", css_classes=['subt-style'])
        self.prob_inst = Div(text="Describe problems as they come up and at what time they occur. If there is an Alarm ID associated with the problem, include it, but leave blank if not. If possible, include a description of the remedy.", css_classes=['inst-style'], width=1000)
        self.prob_time = TextInput(placeholder = '20:07', value=None, width=100) #title ='Time in Kitt Peak local time*',
        self.prob_input = TextAreaInput(placeholder="NightWatch not plotting raw data", rows=10, cols=3, title="Problem Description*:")
        self.prob_alarm = TextInput(title='Alarm ID', placeholder='12', value=None, width=100)
        self.prob_action = TextAreaInput(title='Resolution/Action',placeholder='description',rows=10, cols=3)
        self.prob_btn = Button(label='Add', css_classes=['add_button'])
        self.prob_alert = Div(text=' ', css_classes=['alert-style'])

        self.img_subtitle = Div(text="Images", css_classes=['subt-style'])
        self.img_inst = Div(text="Include images in the Night Log by entering the location of the images on the desi server", css_classes=['inst-style'], width=1000)
        self.img_input = TextInput(title='image file location', placeholder='/n/home/desiobserver/image.png',value=None)
        self.img_comment = TextAreaInput(placeholder='comment about image', rows=8, cols=3, title='Image caption')
        self.img_btn = Button(label='Add', css_classes=['add_button'])
        self.img_alert = Div(text=" ",width=1000)

        self.plot_subtitle = Div(text="Telemetry Plots", css_classes=['subt-style'])

        self.DESI_Log = None
        self.save_telem_plots = False

    def clear_input(self, items):
        """
        After submitting something to the log, this will clear the form.
        """
        if isinstance(items, list):
            for item in items:
                item.value = None
        else:
            items.value = None

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

    def get_checklist_layout(self):
        checklist_layout = layout(self.title,
                                self.check_subtitle,
                                self.checklist_inst,
                                self.checklist,
                                self.check_comment,
                                [self.check_btn],
                                self.check_alert, width=1000)
        self.check_tab = Panel(child=checklist_layout, title="DQS Checklist")

    def get_prob_layout(self):
        prob_layout = layout([self.title,
                            self.prob_subtitle,
                            self.prob_inst,
                            self.time_note,
                            [self.time_title, self.prob_time, self.now_btn],
                            self.prob_alarm,
                            [self.prob_input, self.prob_action],
                            [self.prob_btn],
                            self.prob_alert], width=1000)

        self.prob_tab = Panel(child=prob_layout, title="Problems")

    def get_plots_layout(self):
        telem_data = pd.DataFrame(columns = ['tel_time','tower_time','exp_time','exp','mirror_temp','truss_temp','air_temp','humidity','wind_speed','airmass','exptime','seeing'])
        self.telem_source = ColumnDataSource(telem_data)

        plot_tools = 'pan,wheel_zoom,lasso_select,reset,undo,save'
        p1 = figure(plot_width=800, plot_height=300, x_axis_label='UTC Time', y_axis_label='Temp (C)',x_axis_type="datetime", tools=plot_tools)
        p2 = figure(plot_width=800, plot_height=300, x_axis_label='UTC Time', y_axis_label='Humidity (%)', x_axis_type="datetime",tools=plot_tools)
        p3 = figure(plot_width=800, plot_height=300, x_axis_label='UTC Time', y_axis_label='Wind Speed (mph)', x_axis_type="datetime",tools=plot_tools)
        p4 = figure(plot_width=800, plot_height=300, x_axis_label='UTC Time', y_axis_label='Airmass', x_axis_type="datetime",tools=plot_tools)
        p5 = figure(plot_width=800, plot_height=300, x_axis_label='UTC Time', y_axis_label='Exptime (sec)', x_axis_type="datetime",tools=plot_tools)
        p6 = figure(plot_width=800, plot_height=300, x_axis_label='Exposure', y_axis_label='Seeing (arcsec)', tools=plot_tools)

        p1.circle(x = 'tel_time',y='mirror_temp',source=self.telem_source,color='orange', legend_label = 'Mirror', size=10, alpha=0.5)
        p1.circle(x = 'tel_time',y='truss_temp',source=self.telem_source, legend_label = 'Truss', size=10, alpha=0.5)
        p1.circle(x = 'tel_time',y='air_temp',source=self.telem_source, color='green',legend_label = 'Air', size=10, alpha=0.5)
        p1.legend.location = "top_right"

        p2.circle(x = 'tower_time',y='humidity',source=self.telem_source, size=10, alpha=0.5)
        p3.circle(x = 'tower_time',y='wind_speed',source=self.telem_source, size=10, alpha=0.5)
        p4.circle(x = 'exp_time',y='airmass',source=self.telem_source, size=10, alpha=0.5)
        p5.circle(x = 'exp_time',y='exptime',source=self.telem_source, size=10, alpha=0.5)

        p6.circle(x = 'exp',y='seeing',source=self.telem_source, size=10, alpha=0.5)

        plot_layout = layout([self.title,
                        self.plot_subtitle,
                        p6,p1,p2,p3,p4,p5], width=1000)
        self.plot_tab = Panel(child=plot_layout, title="Telemetry Plots")


    def get_nl_layout(self):
        exp_data = pd.DataFrame(columns = ['date_obs','id','program','sequence','flavor','exptime'])
        self.explist_source = ColumnDataSource(exp_data)

        columns = [TableColumn(field='date_obs', title='Time (UTC)', width=50, formatter=self.datefmt),
                   TableColumn(field='id', title='Exposure', width=50),
                   TableColumn(field='sequence', title='Sequence', width=100),
                   TableColumn(field='flavor', title='Flavor', width=50),
                   TableColumn(field='exptime', title='Exptime', width=50),
                   TableColumn(field='program', title='Program', width=300)]

        self.exp_table = DataTable(source=self.explist_source, columns=columns, width=1000)

        nl_layout = layout([self.title,
                        self.nl_subtitle,
                        self.nl_alert,
                        self.nl_text,
                        self.exptable_alert,
                        self.exp_table], width=1000)
        self.nl_tab = Panel(child=nl_layout, title="Current DESI Night Log")

    def get_img_layout(self):
        img_layout = layout([self.title,
                            self.img_subtitle,
                            self.img_inst,
                            self.img_input,
                            self.img_comment,
                            self.img_btn,
                            self.img_alert], width=1000)
        self.img_tab = Panel(child=img_layout, title='Images')


    def short_time(self, str_time):
        """Returns %H%M in whichever time zone selected
        """
        try:
            t = datetime.strptime(str_time, "%Y%m%dT%H:%M")
            zone = self.kp_zone #zones[time_select.active]
            time = datetime(t.year, t.month, t.day, t.hour, t.minute, tzinfo = zone)
            return "{}:{}".format(str(time.hour).zfill(2), str(time.minute).zfill(2))
        except:
            return str_time

    def get_time(self, time):
        """Returns strptime with utc. Takes time zone selection
        """
        date = self.date_init.value
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

    def connect_log(self):
        """
        Initialize Night Log with Input Date
        """
        try:
            date = datetime.strptime(self.date_init.value, '%Y%m%d')
        except:
            date = datetime.now()

        self.night = str(date.year)+str(date.month).zfill(2)+str(date.day).zfill(2)
        self.DESI_Log=nl.NightLog(str(date.year),str(date.month).zfill(2),str(date.day).zfill(2))
        exists = self.DESI_Log.check_exists()


        your_firstname, your_lastname = self.your_name.value.split(' ')[0], ' '.join(self.your_name.value.split(' ')[1:])
        if exists:
            self.connect_txt.text = 'Connected to Night Log for {}'.format(self.date_init.value)

            meta_dict = self.DESI_Log.get_meta_data()
            if self.report_type == 'DQS':
                self.DESI_Log.add_dqs_observer(your_firstname, your_lastname)
                self.your_name.value = meta_dict['{}_1'.format(self.report_type.lower())]+' '+meta_dict['{}_last'.format(self.report_type.lower())]
            elif self.report_type == 'OS':
                self.os_name_1.value = meta_dict['{}_1_first'.format(self.report_type.lower())]+' '+meta_dict['{}_1_last'.format(self.report_type.lower())]
                self.os_name_2.value = meta_dict['{}_2_first'.format(self.report_type.lower())]+' '+meta_dict['{}_2_last'.format(self.report_type.lower())]

            self.current_header()
            #if self.location == 'nersc':
            self.nl_file = os.path.join(self.DESI_Log.root_dir,'nightlog.html')
            # else:
            #     self.nl_file = os.getcwd()+'/'+self.DESI_Log.root_dir+'nightlog.html'
            self.nl_subtitle.text = "Current DESI Night Log: {}".format(self.nl_file)

            if self.report_type == 'OS':
                plan_txt_text="https://desi.lbl.gov/trac/wiki/DESIOperations/ObservingPlans/OpsPlan{}{}{}".format(date.year,str(date.month).zfill(2),str(date.day).zfill(2))
                self.plan_txt.text = '<a href={}>Tonights Plan Here</a>'.format(plan_txt_text)
                self.LO.value = meta_dict['os_lo_1']+' '+meta_dict['os_lo_last']
                self.OA.value = meta_dict['os_oa_1']+' '+meta_dict['os_oa_last']
                try:
                    self.weather_source.data = new_data
                    new_data = pd.read_csv(self.DESI_Log.weather_file)
                    new_data = new_data[['time','desc','temp','wind','humidity','seeing']]
                except:
                    pass
                if os.path.exists(self.DESI_Log.contributer_file):
                    cont_txt = ''
                    f =  open(self.DESI_Log.contributer_file, "r")
                    for line in f:
                        cont_txt += line
                    self.contributer_list.value = cont_txt
                if os.path.exists(self.DESI_Log.weather_file):
                    data = pd.read_csv(self.DESI_Log.weather_file)[['time','desc','temp','wind','humidity','seeing']]
                    self.weather_source.data = data
            self.current_nl()

        else:
            self.connect_txt.text = 'The Night Log for this {} is not yet initialized.'.format(self.date_init.value)

    def initialize_log(self):
        """
        Initialize Night Log with Input Date
        """

        date = datetime.now()

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

        self.DESI_Log=nl.NightLog(str(date.year),str(date.month).zfill(2),str(date.day).zfill(2))
        self.DESI_Log.initializing()
        self.DESI_Log.get_started_os(os_1_firstname,os_1_lastname,os_2_firstname,os_2_lastname,LO_firstname,LO_lastname,
            OA_firstname,OA_lastname,time_sunset,dusk_18_deg,dawn_18_deg,time_sunrise,time_moonrise,time_moonset,illumination)

        #update_weather_source_data()
        self.connect_txt.text = 'Night Log is Initialized'
        self.current_header()
        self.current_nl()
        days = os.listdir(self.nl_dir)
        init_nl_list = np.sort([day for day in days if 'nightlog_meta.json' in os.listdir(os.path.join(self.nl_dir,day))])[::-1][0:10]
        self.date_init.options = list(init_nl_list)
        self.date_init.value = init_nl_list[0]

    def current_header(self):
        self.DESI_Log.write_intro()
        path = os.path.join(self.DESI_Log.root_dir,"header.html")
        nl_file = open(path,'r')
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
            self.get_seeing()
            try:
                self.make_telem_plots()
                return True
            except:
                #print('Something wrong with making telemetry plots')
                return True
        except:
            self.nl_alert.text = 'You are not connected to a Night Log'
            return False

    def get_exp_list(self):
        if self.location == 'kpno':
            exp_df = pd.read_sql_query(f"SELECT * FROM exposure WHERE night = '{self.night}'", self.conn)
            time = exp_df.date_obs.dt.tz_convert('US/Arizona')
            exp_df['date_obs'] = time
            self.explist_source.data = exp_df[['date_obs','id','program','sequence','flavor','exptime']].sort_values(by='id',ascending=False)
            exp_df = exp_df.sort_values(by='id')
            exp_df.to_csv(self.DESI_Log.explist_file, index=False)
        else:
            self.exptable_alert.text = 'Cannot connect to Exposure Data Base'

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
        plt.plot(self.seeing_df.Exps, self.seeing_df.Seeing,'o')
        plt.xlabel("Exposure")
        plt.ylabel("Seeing (arcsec)")
        plt.savefig(os.path.join(self.DESI_Log.root_dir,'seeing.png'))


    def make_telem_plots(self):
        start_utc = '{} {}'.format(int(self.night)+1, '00:00:00')
        end_utc = '{} {}'.format(int(self.night)+1, '13:00:00')
        tel_df  = pd.read_sql_query(f"SELECT * FROM environmentmonitor_telescope WHERE time_recorded > '{start_utc}' AND time_recorded < '{end_utc}'", self.conn)
        exp_df = pd.read_sql_query(f"SELECT * FROM exposure WHERE night = '{self.night}'", self.conn)
        tower_df = pd.read_sql_query(f"SELECT * FROM environmentmonitor_tower WHERE time_recorded > '{start_utc}' AND time_recorded < '{end_utc}'", self.conn)

        #self.get_seeing()
        telem_data = pd.DataFrame(columns = ['tel_time','tower_time','exp_time','exp','mirror_temp','truss_temp','air_temp','humidity','wind_speed','airmass','exptime','seeing'])
        telem_data.tel_time = tel_df.time_recorded.dt.tz_convert('US/Arizona')
        telem_data.tower_time = tower_df.time_recorded.dt.tz_convert('US/Arizona')
        telem_data.exp_time = exp_df.date_obs.dt.tz_convert('US/Arizona')
        telem_data.exp = self.seeing_df.Exps
        telem_data.mirror_temp = tel_df.mirror_temp
        telem_data.truss_temp = tel_df.truss_temp
        telem_data.air_temp = tel_df.air_temp
        telem_data.humidity = tower_df.humidity
        telem_data.wind_speed = tower_df.wind_speed
        telem_data.airmass = exp_df.airmass
        telem_data.exptime = exp_df.exptime
        telem_data.seeing = self.seeing_df.Seeing

        self.telem_source.data = telem_data

        if self.save_telem_plots:
            if set(list(exp_df.seeing)) == set([None]):
                sky_monitor = False
                fig = plt.figure(figsize= (8,15))
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
            ax2.set_ylabel("Temperature (C)")
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

            #ax1 = fig.add_subplot(6,1,6)
            #ax1.scatter(telem_data.exp, telem_data.seeing, s=5, label='Seeing')
            #ax1.set_ylabel("Seeing (arcsec)")


            if sky_monitor:
                ax[6].scatter(exp_df.date_obs.dt.tz_convert('US/Arizona'), exp_df.seeing, s=5, label='seeing')
                ax[6].set_ylabel("Seeing")

                ax[7].scatter(exp_df.date_obs.dt.tz_convert('US/Arizona'), exp_df.transpar, s=5, label='transparency')
                ax[7].set_ylabel("Transparency (%)")

                ax[8].scatter(exp_df.date_obs.dt.tz_convert('US/Arizona'), exp_df.skylevel, s=5, label='Sky Level')
                ax[8].set_ylabel("Sky level (AB/arcsec^2)")

            #for i in range(len(ax)):
            #    ax[i].grid(True)

        #X label ticks as local time
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
            self.DESI_Log.add_to_checklist(check_time, self.check_comment.value, self.report_type)
            self.check_alert.text = "Checklist last submitted at {}".format(check_time[-5:])
        else:
            self.check_alert.text = "Must complete all tasks before submitting checklist"
        self.clear_input(self.check_comment)
        self.checklist.active = []

    def prob_add(self):
        """Adds problem to nightlog
        """
        if self.report_type == 'Other':
            self.DESI_Log.add_problem(self.get_time(self.prob_time.value), self.prob_input.value, self.prob_alarm.value, self.prob_action.value,self.report_type, self.your_name.value)
        else:
            self.DESI_Log.add_problem(self.get_time(self.prob_time.value), self.prob_input.value, self.prob_alarm.value, self.prob_action.value,self.report_type)
        self.prob_alert.text = "Last Problem Input: '{}' at {}".format(self.prob_input.value, self.prob_time.value)
        self.clear_input([self.prob_time, self.prob_input, self.prob_alarm, self.prob_action])

    def plan_add(self):
        self.DESI_Log.add_plan_os([self.plan_order.value, self.plan_input.value])
        self.plan_alert.text = 'Last item input: {}'.format(self.plan_input.value)
        self.clear_input([self.plan_order, self.plan_input])

    def milestone_add(self):
        now = datetime.now()
        self.DESI_Log.add_milestone_os([self.milestone_input.value, self.milestone_exp_start.value, self.milestone_exp_end.value, self.milestone_exp_excl.value])
        self.milestone_alert.text = 'Last Milestone Entered: {} at {}'.format(self.milestone_input.value, now)
        self.clear_input([self.milestone_input, self.milestone_exp_start, self.milestone_exp_end, self.milestone_exp_excl])

    def weather_add(self):
        """Adds table to Night Log
        """
        if self.weather_time.value not in [None, "NaN",'None'," ", ""]:
            new_data = pd.DataFrame([[self.weather_time.value, self.weather_desc.value, self.weather_temp.value, self.weather_wind.value, self.weather_humidity.value, self.weather_seeing.value]],
                                columns = ['time','desc','temp','wind','humidity','seeing'])
            old_data = pd.DataFrame(self.weather_source.data)[['time','desc','temp','wind','humidity','seeing']]
            data = pd.concat([old_data, new_data])
            data.drop_duplicates(subset=['time'], keep='last',inplace=True)
            self.weather_source.data = data
            self.DESI_Log.add_weather_os(data)
            self.clear_input([self.weather_time, self.weather_desc, self.weather_temp, self.weather_wind, self.weather_humidity, elf.weather_seeing])
        else:
            self.exp_alert.text = 'Could not submit entry because not all mandatory fields were filled.'.format(self.hdr_type.value)

    def progress_add(self):
        if self.exp_time.value not in [None, 'None'," ", ""]:
            data = [self.hdr_type.value, self.get_time(self.exp_time.value), self.exp_comment.value, self.exp_exposure_start.value, self.exp_exposure_finish.value,self.exp_type.value, self.exp_script.value, self.get_time(self.exp_time_end.value), self.exp_focus_trim.value, self.exp_tile.value, self.exp_tile_type.value]
            self.DESI_Log.add_progress(data)
            self.exp_alert.text = 'Last Input was for Observation Type *{}* at {}'.format(self.hdr_type.value, self.exp_time.value)

            self.clear_input([self.exp_time, self.exp_comment, self.exp_exposure_start, self.exp_exposure_finish, self.exp_type, self.exp_script,self.exp_time_end, self.exp_focus_trim, self.exp_tile, self.exp_tile_type])

        else:
            self.exp_alert.text = 'Could not submit entry for Observation Type *{}* because not all mandatory fields were filled.'.format(self.hdr_type.value)

    def comment_add(self):

        if self.your_name.value in [None,' ','']:
            self.comment_alert.text = 'You need to enter your name on first page before submitting a comment'
        else:
            self.DESI_Log.add_comment_other(self.get_time(self.exp_time.value), self.exp_comment.value, self.your_name.value)
            self.comment_alert.text = "A comment was added at {}".format(self.exp_time.value)
            self.clear_input([self.exp_time, self.exp_comment])


    def add_contributer_list(self):
        cont_list = self.contributer_list.value
        self.DESI_Log.add_contributer_list(cont_list)

    def add_summary(self):
        now = datetime.now()
        summary = self.summary.value
        self.DESI_Log.add_summary(summary)
        self.clear_input([self.summary])
        self.milestone_alert.text = 'Summary Entered at {}'.format(self.milestone_input.value, now)

    def image_add(self):
        """Copies image from the input location to the image folder for the nightlog.
        Then calls add_image() from nightlog.py which writes it to the html file
        Then gives preview of image of last image.
        """
        image_loc = self.img_input.value
        image_name = os.path.split(image_loc)[1]
        image_type = os.path.splitext(image_name)[1]
        bashCommand1 = "cp {} {}".format(image_loc,self.DESI_Log.image_dir)
        bashCommand2 = "cp {} {}".format(image_loc,self.report_type+"_Report/static/images/tmp_img{}".format(image_type))
        results = subprocess.run(bashCommand1.split(), text=True, stdout=subprocess.PIPE, check=True)
        results = subprocess.run(bashCommand2.split(), text=True, stdout=subprocess.PIPE, check=True)
        self.DESI_Log.add_image(os.path.join(self.DESI_Log.image_dir,image_name), self.img_comment.value)
        preview = '<img src="{}_Report/static/images/tmp_img{}" style="width:300px;height:300px;">'.format(self.report_type,image_type)
        preview += "\n"
        preview += "{}".format(self.img_comment.value)
        self.img_alert.text = preview
        self.clear_input([self.img_input, self.img_comment])

    def time_is_now(self):
        now = datetime.now().astimezone(tz=self.kp_zone)
        now_time = self.short_time(datetime.strftime(now, "%Y%m%dT%H:%M"))
        tab = self.layout.active
        time_input = self.time_tabs[tab]

        time_input.value = now_time

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
