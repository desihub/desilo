#Imports
import os, sys
from datetime import datetime
import numpy as np 
import pandas as pd
import socket

from bokeh.io import curdoc  # , output_file, save
from bokeh.models import (TextInput, ColumnDataSource, Paragraph, Button, TextAreaInput, Select,CheckboxGroup, RadioButtonGroup)
from bokeh.models.widgets.markups import Div
from bokeh.layouts import layout
from bokeh.models.widgets import Panel, Tabs
from astropy.time import TimezoneInfo
import astropy.units.si as u 

sys.path.append(os.getcwd())

import nightlog as nl

class Report():
    def __init__(self, type):
        self.report_type = type
        self.utc = TimezoneInfo()
        self.kp_zone = TimezoneInfo(utc_offset=-7*u.hour)
        self.zones = [self.utc, self.kp_zone]

        self.inst_style = {'font-family':'serif','font-size':'150%'}
        self.subt_style = {'font-family':'serif','font-size':'200%'}
        self.title_style = {'font-family':'serif','font-size':'250%'}
        self.alert_style = {'font-family':'serif','font-size':'150%','color':'red'}

        self.page_logo = Div(text="<img src='DQS_Report/static/logo.png'>", width=350, height=300)
        self.intro_subtitle = Div(text="Connect to Night Log",width=500,style=self.subt_style)
        self.intro_info = Div(text="Time Formats: 6:18pm = 18:18 = 1818. You can use any of these formats. <b>Input all times in Local Kitt Peak time.</b> When you input the date and your name, press the blue button. All relevant Night Log meta data will be displayed below.",width=800,style=self.inst_style)

        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        if 'desi' in hostname:
            self.location = 'kpno'
            from DOSlib.util import sky_calendar
        elif '128.55' in ip_address:
            self.location = 'nersc'
        else:
            self.location = 'other'
        nw_dirs = {'nersc':'/global/cfs/cdirs/desi/spectro/nightwatch/nersc/', 'kpno':'/exposures/nightwatch/', 'other':None}
        self.nw_dir = nw_dirs[self.location] 

        self.your_name = TextInput(title ='Your Name', placeholder = 'John Smith')
        self.lo_names = ['None ','Liz Buckley-Geer','Sarah Eftekharzadeh','Ann Elliott','Parker Fagrelius','Satya Gontcho A Gontcho','James Lasker','Martin Landriau','Claire Poppett','Michael Schubnell','Luke Tyas','Other ']
        self.oa_names = ['None ','Karen Butler','Amy Robertson','Anthony Paat','Dave Summers','Doug Williams','Other ']
        self.intro_txt = Div(text=' ')
        self.comment_txt = Div(text=" ",width=500,style=self.inst_style)

        self.date_init = Select(title="Initialized Night Logs")
        days = os.listdir('nightlogs')
        init_nl_list = np.sort([day for day in days if 'nightlog_meta.json' in os.listdir('nightlogs/'+day)])[::-1][0:10]
        self.date_init.options = list(init_nl_list)
        self.date_init.value = init_nl_list[0]
        self.connect_txt = Div(text=' ', width=600, style=self.alert_style)

        self.connect_bt = Button(label="Connect to Night Log", button_type='primary',width=300)

        self.exp_info = Div(text="Fill In Only Relevant Data",width=500, style=self.inst_style)
        self.exp_comment = TextAreaInput(title ='Comment/Remark', placeholder = 'Humidity high for calibration lamps',value=None,rows=6)
        self.exp_time = TextInput(title ='Time', placeholder = '2007',value=None)
        self.exp_btn = Button(label='Add', button_type='primary')
        self.exp_type = Select(title="Exposure Type", value = None, options=['None','Zero','Focus','Dark','Arc','FVC','DESI'])
        self.exp_alert = Div(text=' ', width=600, style=self.alert_style)
        self.exp_exposure_start = TextInput(title='Exposure Number: First', placeholder='12345', value=None)
        self.exp_exposure_finish = TextInput(title='Exposure Number: Last', placeholder='12346', value=None)

        self.nl_subtitle = Div(text="Current DESI Night Log", width=500, style=self.subt_style)
        self.nl_btn = Button(label='Get Current DESI Night Log', button_type='primary')
        self.nl_text = Div(text="Current DESI Night Log",width=500, style=self.inst_style)
        self.nl_alert = Div(text=' ',width=600, style=self.inst_style)
        self.nl_info = Div(text="Night Log Info:", width=500, style=self.inst_style)

        self.checklist = CheckboxGroup(labels=[])
        self.check_time = TextInput(title ='Time', placeholder = '2007', value=None)
        self.check_alert = Div(text=" ", width=800, style=self.alert_style)
        self.check_btn = Button(label='Submit', button_type='primary')

        self.prob_subtitle = Div(text="Problems", width=500, style=self.subt_style)
        self.prob_inst = Div(text="Describe problems as they come up and at what time they occur. If possible, include a description of the remedy.", width=800, style=self.inst_style)
        self.prob_time = TextInput(title ='Time', placeholder = '2007', value=None)
        self.prob_input = TextAreaInput(placeholder="NightWatch not plotting raw data", rows=6, title="Problem Description:")
        self.prob_alarm = TextInput(title='Alarm ID', placeholder='12', value=None)
        self.prob_action = TextAreaInput(title='Resolution/Action',placeholder='description',rows=6)
        self.prob_btn = Button(label='Add', button_type='primary')
        self.prob_alert = Div(text=' ', width=600, style=self.alert_style)
          

        self.DESI_Log = None

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
        intro_layout = layout([[self.title],
                            [self.page_logo, self.instructions],                 
                            [self.intro_subtitle],
                            [self.intro_info],
                            [self.date_init, self.your_name],
                            [self.connect_bt],
                            [self.connect_txt],
                            [self.nl_info],
                            [self.intro_txt]])
        self.intro_tab = Panel(child=intro_layout, title="Initialization")

    def get_checklist_layout(self):
        checklist_layout = layout([[self.title],
                                [self.check_subtitle],
                                [self.checklist_inst],
                                [self.checklist],
                                [self.check_time, self.check_btn],
                                [self.check_alert]])
        self.check_tab = Panel(child=checklist_layout, title="DQS Checklist")

    def get_prob_layout(self):
        prob_layout = layout([[self.title],
                            [self.prob_subtitle],
                            [self.prob_inst],
                            [self.prob_time, self.prob_input],
                            [self.prob_alarm, self.prob_action],
                            [self.prob_btn],
                            [self.prob_alert]])

        self.prob_tab = Panel(child=prob_layout, title="Problems")

    def get_nl_layout(self):
        nl_layout = layout([[self.title],
                            [self.nl_subtitle],
                            [self.nl_btn, self.nl_alert],
                            [self.nl_text]])
        self.nl_tab = Panel(child=nl_layout, title="Current DESI Night Log")


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
        year, month, day = int(date[0:4]), int(date[5:6]), int(date[7:8])
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
                self.your_name.value = meta_dict['{}_1'.format(self.report_type.lower())]+' '+meta_dict['{}_last'.format(self.report_type.lower())]
            self.current_header()
            try:
                plan_txt_text="https://desi.lbl.gov/trac/wiki/DESIOperations/ObservingPlans/OpsPlan{}{}{}".format(date.year,str(date.month).zfill(2),str(date.day).zfill(2))
                self.plan_txt.text = '<a href={}>Tonights Plan Here</a>'.format(plan_txt_text)
                self.LO.value = meta_dict['{}_lo_1'.format(self.report_type.lower())]+' '+meta_dict['{}_lo_last'.format(self.report_type.lower())]
                self.OA.value = meta_dict['{}_oa_1'.format(self.report_type.lower())]+' '+meta_dict['{}_oa_last'.format(self.report_type.lower())]
                new_data = pd.read_csv(self.DESI_Log.weather_file)
                new_data = new_data[['time','desc','temp','wind','humidity']]
                self.weather_source.data = new_data
            except:
                pass


        else:
            self.connect_txt.text = 'The Night Log for this {} is not yet initialized.'.format(self.date_init.value)

    def initialize_log(self):
        """
        Initialize Night Log with Input Date
        """

        date = datetime.now()

        LO_firstname, LO_lastname = self.LO.value.split(' ')[0], ' '.join(self.LO.value.split(' ')[1:])
        OA_firstname, OA_lastname = self.OA.value.split(' ')[0], ' '.join(self.OA.value.split(' ')[1:])
        your_firstname, your_lastname = self.your_name.value.split(' ')[0], ' '.join(self.your_name.value.split(' ')[1:])

        if location == 'kpno':
            ephem = sky_calendar()
            time_sunset = self.get_strftime(ephem['sunset'])
            time_sunrise = self.get_strftime(ephem['sunrise'])
            time_moonrise = self.get_strftime(ephem['moonrise'])
            time_moonset = self.get_strftime(ephem['moonset'])
            illumination = ephem['illumination']
            dusk_18_deg = self.get_strftime(ephem['dusk_astronomical'])
            dawn_18_deg = self.get_strftime(ephem['dawn_astronomical'])
        else:
            time_sunset = None
            time_sunrise = None
            time_moonrise = None
            time_moonset = None
            illumination = None
            dusk_18_deg = None
            dawn_18_deg = None


        self.DESI_Log=nl.NightLog(str(date.year),str(date.month).zfill(2),str(date.day).zfill(2))
        self.DESI_Log.initializing()
        self.DESI_Log.get_started_os(your_firstname,your_lastname,LO_firstname,LO_lastname,
            OA_firstname,OA_lastname,time_sunset,dusk_18_deg,dawn_18_deg,time_sunrise,time_moonrise,time_moonset,illumination)

        #update_weather_source_data()
        self.connect_txt.text = 'Night Log is Initialized'
        self.current_header()

    def current_header(self):
        self.DESI_Log.write_intro()
        path = "nightlogs/"+self.DESI_Log.obsday+"/header.html"
        nl_file = open(path,'r')
        intro = ''
        for line in nl_file:
            intro =  intro + line + '\n'
        self.intro_txt.text = intro
        nl_file.closed

    def current_nl(self):
        now = datetime.now()
        self.DESI_Log.finish_the_night()
        path = "nightlogs/"+self.DESI_Log.obsday+"/nightlog.html"
        nl_file = open(path,'r')
        nl_txt = ''
        for line in nl_file:
            nl_txt =  nl_txt + line + '\n'
        self.nl_text.text = nl_txt
        nl_file.closed
        self.nl_alert.text = 'Last Updated on this page: {}'.format(now)

    def check_add(self):
        """add checklist time to Night Log
        """
        complete = self.checklist.active
        if len(complete) == len(self.checklist.labels):
            if self.check_time.value is not None:
                self.DESI_Log.add_to_checklist(self.get_time(self.check_time.value), self.report_type)
                self.check_alert.text = "Checklist last submitted at {}".format(self.check_time.value)
            else:
                self.check_alert.text = "Must input a valid time to submit checklist"
        else:
            self.check_alert.text = "Must complete all tasks before submitting checklist"
        self.clear_input(self.check_time)
        self.checklist.active = []

    def prob_add(self):
        """Adds problem to nightlog
        """
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
        self.clear_input([self.milestone_input, self.milestone_exp_start, self.milestone_exp_end, self.milestone_exp_excl])
        self.milestone_alert.text = 'Last Milestone Entered: {} at {}'.format(self.milestone_input.value, now)

    def weather_add(self):
        """Adds table to Night Log
        """
        new_data = pd.DataFrame([[self.weather_time.value, self.weather_desc.value, self.weather_temp.value, self.weather_wind.value, self.weather_humidity.value]],
                                columns = ['time','desc','temp','wind','humidity'])
        old_data = pd.DataFrame(self.weather_source.data)[['time','desc','temp','wind','humidity']]
        data = pd.concat([old_data, new_data])
        self.weather_source.data = data
        self.DESI_Log.add_weather_os(data)
        self.clear_input([self.weather_time, self.weather_desc, self.weather_temp, self.weather_wind, self.weather_humidity])

    def progress_add(self):
        data = [self.hdr_type.value, self.get_time(self.exp_time.value), self.exp_comment.value, self.exp_exposure_start.value, self.exp_exposure_finish.value,
                self.exp_type.value, self.exp_script.value, self.get_time(self.exp_time_end.value), self.exp_focus_trim.value, self.exp_tile.value, self.exp_tile_type.value]
        self.DESI_Log.add_progress(data)
        self.exp_alert.text = 'Last Input was for Observation Type *{}* at {}'.format(self.hdr_type.value, self.exp_time.value)

        self.clear_input([self.exp_time, self.exp_comment, self.exp_exposure_start, self.exp_exposure_finish, self.exp_type, self.exp_script,
                    self.exp_time_end, self.exp_focus_trim, self.exp_tile, self.exp_tile_type])

    def comment_add(self):

        if self.your_name.value in [None,' ','']:
            self.comment_alert.text = 'You need to enter your name on first page before submitting a comment'
        else:
            self.DESI_Log.add_comment_other(self.get_time(self.exp_time.value), self.exp_comment.value, self.your_name.value)
            self.clear_input([self.exp_time, self.exp_comment])
            self.comment_alert.text = "Currently this is not being published to the Night Log."