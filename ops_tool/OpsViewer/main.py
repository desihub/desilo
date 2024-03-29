"""
Created on May 25, 2021

Shows the current observing schedule for DESI Operations. Schedule based on google sheet here:
https://docs.google.com/spreadsheets/d/1LruPgnsanCn6D18y5_uo_nIXrWOFC3bmTw0U0hl3bfo/edit#gid=0

Includes a day view as well as the full schedule

@author: Parker Fagrelius
"""

import datetime
import pandas as pd
import numpy as np

from bokeh.io import curdoc
from bokeh.models.widgets.markups import Div
from bokeh.layouts import layout
from bokeh.models.widgets import Panel, Tabs
from bokeh.models import ColumnDataSource, DataTable, DateFormatter, TableColumn, TextInput, Button

import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials


class OpsViewer(object):
    def __init__(self):

        self.url = "https://docs.google.com/spreadsheets/d/1nzShIvgfqqeibVcGpHzm7dSpjJ78vDtWz-3N0wV9hu0/edit#gid=0"
        self.credentials = "./credentials.json"
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(self.credentials)
        self.client = gspread.authorize(self.creds)

        self.today = datetime.datetime.now().strftime('%Y-%m-%d')
        self.day = self.today
        self.datefmt = DateFormatter(format="yyyy-mm-dd")

        self.remote = False #To determine if LO is remote
        self.comment = None
        self.this_df = None #Line in df for today

        self.get_all_shifts = True
        self.observers_list = []
        self.shift_list = []
        self.start_list = []
        self.end_list = []

    def get_names(self):
        """
        * Pulls names for the selected date
        * Prints any comments for the day
        * Calls check_first_day for each observer to get length of shifts
        """

        self.this_df = self.df[self.df.Date == self.day]
        self.this_df = self.this_df.iloc[0]
        comm = str(self.this_df.Comment)
        if comm in ['nan', 'None', '', ' ']:
            comm = ''
        self.comment = comm

        divs = {'LO':self.lo, 'SO_1':self.so_1, 'SO_2':self.so_2, 'SVY':self.svy, 'OA':self.oa, 'EM':self.em}
        styles = {'LO':'lo-style', 'SO_1':'os-style', 'SO_2':'os-style', 'SVY':'svy-style','OA':'oa-style', 'EM':'em-style'}
        for obs_, div in divs.items():
            try:
                self.df[obs_] = self.df[obs_].str.strip()
                name = str(self.this_df[obs_])
                self.remote = False

                #Check if LO is remote (will have _remote in schedule)
                if obs_ == 'LO':
                    try:
                        remote = name.split('_')
                        if (len(remote) > 1) & (remote[1] == 'remote'):
                            name = remote[0]
                            self.remote = True 
                            if comm == '':
                                self.comment = 'Remote Lead Observer(s)'
                            else:
                                self.comment = comm + '; Remote Lead Observer(s)'
                    except Exception as e:
                        print(e)

                #Leave empty if value is None
                if name in [np.nan, 'None', 'nan', ' ', '']:
                    div.text = ''
                    div.css_classes = ['plain-style']
                else:
                    x = self.check_first_day(name,obs_)
                    div.text = x
                    div.css_classes = [styles[obs_]]

                    #Unique class for remote LOs
                    if (obs_ in ['LO']) & (self.remote):
                        div.css_classes = ['remote-lo-style']          
            except Exception as e:
                print(obs_, e)

        if str(self.comment) in ['', ' ', 'None', 'nan', '-']:
            self.obs_comment.text = ''
            self.obs_comment.css_classes = ['plain-style']
        else:
            self.obs_comment.text = self.comment
            self.obs_comment.css_classes = ['obs-comment']

    def check_first_day(self, name, ops_type):
        """
        Counts number of days in shift and how many remaining

        Returns name and remaining days/total days
        """
        try:
            self.df['value_grp'] = (self.df[ops_type] != self.df[ops_type].shift()).cumsum()
            xx = pd.DataFrame({'BeginDate':self.df.groupby('value_grp').Date.first(), 
                                'EndDate':self.df.groupby('value_grp').Date.last(),
                                'Consecutive':self.df.groupby('value_grp').size()},).reset_index(drop=True)
            xx.set_index('EndDate', inplace=True, drop=False)

            xxx = xx.sort_index().truncate(before='{}'.format(self.day))
            xxx = xxx.iloc[0]
            if ops_type in ['LO','SO_1','SO_2']:
                self.observers_list.append(name)
                self.shift_list.append(ops_type)
                self.start_list.append(xxx[['BeginDate']].values[0].date().strftime('%m/%d/%Y'))
                self.end_list.append(xxx[['EndDate']].values[0].date().strftime('%m/%d/%Y'))
                
            xxx['BT_ts'] = pd.Timestamp(xxx.BeginDate)
            xxx['today_ts'] = pd.Timestamp(self.day)
            days = abs((xxx.BT_ts - xxx.today_ts).days) + 1
            return '{} ({}/{} days)'.format(name, days, xxx.Consecutive)

        except Exception as e:
            print(name, e)
            return '{}'.format(name)

    def new_day(self):
        """
        Shows schedule for entered day
        """
        if self.get_all_shifts:
            current = pd.to_datetime('2021-09-13', format='%Y-%m-%d')
            for day in range(140):
                next_day = current + pd.Timedelta(days=day)
                self.day = next_day.strftime('%Y-%m-%d')
                self.get_names()
            all_shifts = pd.DataFrame(columns=['Observer','Shift','Start','End'])
            all_shifts['Observer'] = np.array(self.observers_list)
            all_shifts['Shift'] = np.array(self.shift_list)
            all_shifts['Start'] = np.array(self.start_list)
            all_shifts['End'] = np.array(self.end_list)
            all_shifts.drop_duplicates(keep='first',inplace=True)
            all_shifts.to_csv('all_shifts.csv',index=False)

        else:
            self.day = self.enter_date.value
            self.date_title.text = 'DESI Operations Schedule for {}'.format(self.day)
            self.get_names()


    def prev_day(self):
        """
        Shows schedule for previous day
        """
        current = pd.to_datetime(self.day, format='%Y-%m-%d')
        prev_day = current - pd.Timedelta(days=1)
        self.day = prev_day.strftime('%Y-%m-%d')
        self.date_title.text = 'DESI Operations Schedule for {}'.format(self.day)
        self.get_names()

    def next_day(self):
        """
        Shows schedule for next day
        """
        current = pd.to_datetime(self.day, format='%Y-%m-%d')
        next_day = current + pd.Timedelta(days=1)
        self.day = next_day.strftime('%Y-%m-%d')
        self.date_title.text = 'DESI Operations Schedule for {}'.format(self.day)
        self.get_names()

    def get_layout(self):
        """
        Defines layout for Bokeh App for both Tabs: Main, Schedule
        """
        title = Div(text='Operations Schedule Viewer', css_classes=['h1-title-style'], width=800)
        self.date_title = Div(text='DESI Operations Schedule for {}'.format(self.day), css_classes=['h1-title-style'], width=800)

        self.obs_comment = Div(text='', css_classes=['obs-comment'])
        self.lo = Div(text='Lead Obs.', css_classes=['lo-style'], width=400)
        self.lo_head = Div(text='LO: ', css_classes=['lo-style'], width=75)
        self.so_1 = Div(text='Support Obs. 1', css_classes=['os-style'], width=400)
        self.so_2 = Div(text='Support Obs. 2', css_classes=['os-style'], width=400)
        self.so_head = Div(text='SO: ', css_classes=['os-style'], width=75)
        self.oa = Div(text='Observing Associate', css_classes=['oa-style'], width=400)
        self.oa_head = Div(text="OA: ", css_classes=['oa-style'], width=75)
        self.em = Div(text='Electronic Mainetenance', css_classes=['em-style'], width=400)
        self.em_head = Div(text='EM: ', css_classes=['em-style'], width=75)
        self.svy = Div(text='Survey Planning', css_classes=['svy-style'], width=400)
        self.svy_head = Div(text='SVY: ', css_classes=['svy-style'], width=75)
        self.buffer = Div(text='')
        self.date_before = Button(label='Previous Date', css_classes=['next_button'], width=200)
        self.date_after = Button(label='Next Date', css_classes=['next_button'], width=200)
        self.enter_date = TextInput(placeholder='YYYY-MM-DD', width=200)
        self.date_btn = Button(label='Enter date', width=200, css_classes=['change_button'])

        main_layout = layout([self.date_title, 
                              self.obs_comment,
                              [self.lo_head, self.lo],
                              [self.so_head, self.so_1, self.so_2],
                              [self.svy_head, self.svy],
                              [self.oa_head, self.oa],
                              [self.em_head, self.em],
                              self.buffer,
                              [self.date_before, self.date_after],
                              [self.enter_date, self.date_btn]])

        main_tab = Panel(child=main_layout, title='Main')

        self.sched_source = ColumnDataSource(self.df)
        sched_columns = [TableColumn(field='Day', title='Day', width=10),
                         TableColumn(field='Date', title='Date', width=75, formatter=DateFormatter()),
                         TableColumn(field='Comment', title='Comment', width=150),
                         TableColumn(field='LO', title='LO', width=150),
                         TableColumn(field='SO_1', title='SO 1', width=150),
                         TableColumn(field='SO_2', title='SO 2', width=150),
                         TableColumn(field='SVY', title='SVY', width=150),
                         TableColumn(field='OA', title='OA', width=150),
                         TableColumn(field='EM', title='EM', width=150)]

        self.sched_table = DataTable(source=self.sched_source, columns=sched_columns, width=1200, height=2000, fit_columns=False)
        sched_layout = layout([title, self.sched_table])
        sched_tab = Panel(child=sched_layout, title='Schedule')

        self.layout = Tabs(tabs=[main_tab, sched_tab])

    def update_sched(self):
        """
        Grabs schedule from google sheet. Ran twice a day to pick up any changes.
        """
        self.sheet = self.client.open_by_url(self.url).sheet1
        self.df = get_as_dataframe(self.sheet, header=0)
        self.df = self.df[['Date', 'Comment', 'LO', 'SO_1', 'SO_2', 'SVY','OA', 'EM']]
        
        #self.df = pd.read_csv('obs_schedule_official_2.csv')
        self.df['Date'] = pd.to_datetime(self.df['Date'], format='%m/%d/%y')
        self.user_info = pd.read_csv('user_info.csv') #for email addresses, etc.

    def run(self):
        self.update_sched()
        self.get_layout()
        self.get_names()
        self.date_btn.on_click(self.new_day)
        self.date_before.on_click(self.prev_day)
        self.date_after.on_click(self.next_day)


Ops = OpsViewer()
Ops.run()
curdoc().title = 'Operations Schedule Viewer'
curdoc().add_root(Ops.layout)
curdoc().add_periodic_callback(Ops.update_sched, 43200000) #twice a day
