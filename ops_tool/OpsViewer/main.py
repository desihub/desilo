"""
Created on May 25, 2021

@author: Parker Fagrelius
"""

import os, sys
import pandas as pd
import numpy as np
from bokeh.io import curdoc
from bokeh.models import TextInput, Button, TextAreaInput, Select
from bokeh.models.widgets.markups import Div, PreText
from bokeh.layouts import layout, column, row
from bokeh.models.widgets import Panel, Tabs
import datetime


from bokeh.layouts import column, layout, row, gridplot
from bokeh.models.widgets import Panel
from bokeh.models import CustomJS, ColumnDataSource, Select, Slider, CheckboxGroup
from bokeh.models import ColumnDataSource, DataTable, DateFormatter, TableColumn
from bokeh.models import CheckboxButtonGroup

import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials

import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage


class OpsViewer(object):
    def __init__(self):
        self.test = True

        self.df = pd.read_csv('obs_schedule_corrected.csv')
        self.df['Date'] = pd.to_datetime(self.df['Date'], format='%m/%d/%y')
        self.user_info = pd.read_csv('user_info.csv')
        self.today = datetime.datetime.now().strftime('%Y-%m-%d')
        self.today_df = self.df[self.df.Date == self.today]

        self.day = self.today
       
        self.datefmt = DateFormatter(format="yyyy-mm-dd")

    def get_names(self):
        self.this_df = self.df[self.df.Date == self.day]
        self.this_df = self.this_df.iloc[0]
        if str(self.this_df.Comments) in ['',' ','None','nan','-']:
            self.obs_comment.text = ''
            self.obs_comment.css_classes = ['plain-style']
        else:
            self.obs_comment.text = str(self.this_df.Comments)
            self.obs_comment.css_classes = ['obs-comment']
        pos = {'LO_1':self.lo_1,'LO_2':self.lo_2,'OS_1':self.os_1,'OS_2':self.os_2,
                'DQS_1':self.dqs_1,'DQS_2':self.dqs_2,'OA':self.oa,'EM':self.em}
        styles = {'LO_1':'lo-style','LO_2':'lo-style','OS_1':'os-style','OS_2':'os-style',
                'DQS_1':'dqs-style','DQS_2':'dqs-style','OA':'oa-style','EM':'em-style'}
        for p, div in pos.items():
            try:
                name = str(self.this_df[p])
                if name in ['None','nan',' ','']:
                    div.text = ''
                    div.css_classes = ['plain-style']
                else:
                    x = self.check_first_day(name,p)
                    div.text = x
                    div.css_classes = [styles[p]]
            except:
                    pass

    def check_first_day(self, name, ops_type):
        try:
            self.df['value_grp'] = (self.df[ops_type] != self.df[ops_type].shift()).cumsum()
            xx = pd.DataFrame({'BeginDate' : self.df.groupby('value_grp').Date.first(), 
                  'EndDate' : self.df.groupby('value_grp').Date.last(),
                  'Consecutive' : self.df.groupby('value_grp').size()}).reset_index(drop=True)
            xx.set_index('EndDate',inplace=True,drop=False)
            xxx = xx.truncate(before='{}'.format(self.day))
            xxx = xxx.iloc[0]
            xxx['BT_ts'] = pd.Timestamp(xxx.BeginDate)
            xxx['today_ts'] = pd.Timestamp(self.day)
            days = abs((xxx.BT_ts - xxx.today_ts).days) + 1
            return '{} ({}/{} days)'.format(name,days,xxx.Consecutive)

        except:
            return '{}'.format(name)
        #find BeginDate of closest day
        #determine how many days total vs how many days in


    def new_day(self):
        self.day = self.enter_date.value
        self.date_title.text = 'DESI Operations Schedule for {}'.format(self.day)
        self.get_names()

    def layout(self):
        self.report = PreText(text=' ')
        info = Div(text=' ')
        title = Div(text='Operations Schedule Viewer',css_classes=['h1-title-style'],width=800)
        self.date_title = Div(text='DESI Operations Schedule for {}'.format(self.day),css_classes=['h1-title-style'],width=800)
        self.obs_comment = Div(text='',css_classes=['obs-comment'])
        self.lo_1 = Div(text='Lead Obs. 1',css_classes=['lo-style'],width=400)
        self.lo_2 = Div(text='Lead Obs. 2',css_classes=['lo-style'],width=400)
        self.lo_head = Div(text='LO: ',css_classes=['lo-style'],width=50)
        self.os_1 = Div(text='Obs. Scientist 1',css_classes=['os-style'],width=400)
        self.os_2 = Div(text='Obs. Scientist 2',css_classes=['os-style'],width=400)
        self.os_head = Div(text='OS: ',css_classes=['os-style'],width=50)
        self.dqs_1 = Div(text='Data QA Scientist 1 ',css_classes=['dqs-style'],width=400)
        self.dqs_2 = Div(text='Data QA Scientist 2',css_classes=['dqs-style'],width=400)
        self.dqs_head = Div(text='DQS: ',css_classes=['dqs-style'],width=50)
        self.oa = Div(text='Observing Associate',css_classes=['oa-style'],width=400)
        self.oa_head = Div(text="OA: ",css_classes=['oa-style'],width=50)
        self.em = Div(text='Electronic Mainetenance',css_classes=['em-style'],width=400)
        self.em_head = Div(text='EM: ',css_classes=['em-style'],width=50)
        self.buffer = Div(text='')
        self.enter_date = TextInput(placeholder = 'YYYY-MM-DD', width=200)
        self.date_btn = Button(label='Change date', width=200,css_classes=['change_button'])


        main_layout = layout([self.date_title,self.obs_comment,
                  [self.lo_head, self.lo_1,self.lo_2],
                  [self.os_head, self.os_1,self.os_2],
                  [self.dqs_head,self.dqs_1,self.dqs_2],
                  [self.oa_head, self.oa],
                  [self.em_head,self.em],
                  self.buffer,
                  [self.enter_date, self.date_btn]])
        main_tab = Panel(child=main_layout, title='Main')

        self.sched_source = ColumnDataSource(self.df)
        sched_columns = [TableColumn(field='Day', title='Day', width=10),
                   TableColumn(field='Date', title='Date', width=75,formatter=DateFormatter()),
                   TableColumn(field='Comments', title='Comment', width=150),
                   TableColumn(field='LO_1', title='LO 1', width=150),
                   TableColumn(field='LO_2', title='LO 2', width=150),
                   TableColumn(field='OS_1', title='OS 1', width=150),
                   TableColumn(field='OS_2', title='OS 2', width=150),
                   TableColumn(field='DQS_1', title='DQS 1', width=150),
                   TableColumn(field='DQS_2', title='DQS 2', width=150),
                   TableColumn(field='OA', title='OA', width=150),
                   TableColumn(field='EM', title='EM', width=150)] #, 

        self.sched_table = DataTable(source=self.sched_source, columns=sched_columns, width=1200, height=2000,fit_columns=False)
        sched_layout = layout([title, self.sched_table])
        sched_tab = Panel(child=sched_layout, title='Schedule')
        #highlight current row
        #only show one row previously

        self.layout = Tabs(tabs=[main_tab, sched_tab])

        
    def run(self):
        self.layout()
        self.get_names()
        self.date_btn.on_click(self.new_day)

Ops = OpsViewer()
Ops.run()
curdoc().title = 'Operations Schedule Viewer'
curdoc().add_root(Ops.layout)