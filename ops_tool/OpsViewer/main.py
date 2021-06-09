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


class OpsViewer(object):
    def __init__(self):
        self.test = True

        self.df = pd.read_csv('obs_schedule_official.csv')
        self.df['Date'] = pd.to_datetime(self.df['Date'], format='%m/%d/%y')
        self.user_info = pd.read_csv('user_info.csv')
        self.today = datetime.datetime.now().strftime('%Y-%m-%d')
        self.today_df = self.df[self.df.Date == self.today]

        self.day = self.today
       
        self.datefmt = DateFormatter(format="yyyy-mm-dd")

    def get_names(self):
        self.this_df = self.df[self.df.Date == self.day]
        self.this_df = self.this_df.iloc[0]
        comm = str(self.this_df.Comments)
        if comm in ['nan','None','',' ']:
            comm = ''
        self.comment = comm

        pos = {'LO_1':self.lo_1,'LO_2':self.lo_2,'OS_1':self.os_1,'OS_2':self.os_2,
                'DQS_1':self.dqs_1,'DQS_2':self.dqs_2,'OA':self.oa,'EM':self.em}
        styles = {'LO_1':'lo-style','LO_2':'lo-style','OS_1':'os-style','OS_2':'os-style',
                'DQS_1':'dqs-style','DQS_2':'dqs-style','OA':'oa-style','EM':'em-style'}
        for p, div in pos.items():
            try:
                self.df[p] = self.df[p].str.strip()
                name = str(self.this_df[p])
                self.remote = False
                try:
                    remote = name.split('_')
                    if (len(remote)>1) & (remote[1] == 'remote'):
                        name = remote[0]
                        self.remote = True 
                        self.comment = comm + '; Remote Lead Observer(s)'
                except Exception as e:
                    pass
                if name in ['None','nan',' ','']:
                    div.text = ''
                    div.css_classes = ['plain-style']
                else:
                    x = self.check_first_day(name,p)
                    div.text = x
                    div.css_classes = [styles[p]]
                    if (p in ['LO_1','LO_2']) & (self.remote):
                        div.css_classes = ['remote-lo-style']          
            except:
                    pass

        if str(self.comment) in ['',' ','None','nan','-']:
            self.obs_comment.text = ''
            self.obs_comment.css_classes = ['plain-style']
        else:
            self.obs_comment.text = self.comment
            self.obs_comment.css_classes = ['obs-comment']

    def check_first_day(self, name, ops_type):
        try:
            self.df['value_grp'] = (self.df[ops_type] != self.df[ops_type].shift()).cumsum()
            xx = pd.DataFrame({'BeginDate' : self.df.groupby('value_grp').Date.first(), 
                  'EndDate' : self.df.groupby('value_grp').Date.last(),
                  'Consecutive' : self.df.groupby('value_grp').size()},).reset_index(drop=True)
            xx.set_index('EndDate',inplace=True,drop=False)
            xxx = xx.truncate(before='{}'.format(self.day))
            xxx = xxx.iloc[0]
            xxx['BT_ts'] = pd.Timestamp(xxx.BeginDate)
            xxx['today_ts'] = pd.Timestamp(self.day)
            days = abs((xxx.BT_ts - xxx.today_ts).days) + 1
            return '{} ({}/{} days)'.format(name,days,xxx.Consecutive)

        except:
            return '{}'.format(name)


    def new_day(self):
        self.day = self.enter_date.value
        self.date_title.text = 'DESI Operations Schedule for {}'.format(self.day)
        self.get_names()

    def prev_day(self):
        current = pd.to_datetime(self.day, format='%Y-%m-%d')
        prev_day = current - pd.Timedelta(days=1)
        self.day = prev_day.strftime('%Y-%m-%d')
        self.date_title.text = 'DESI Operations Schedule for {}'.format(self.day)
        self.get_names()

    def next_day(self):
        current = pd.to_datetime(self.day, format='%Y-%m-%d')
        next_day = current + pd.Timedelta(days=1)
        self.day = next_day.strftime('%Y-%m-%d')
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
        self.lo_head = Div(text='LO: ',css_classes=['lo-style'],width=75)
        self.os_1 = Div(text='Obs. Scientist 1',css_classes=['os-style'],width=400)
        self.os_2 = Div(text='Obs. Scientist 2',css_classes=['os-style'],width=400)
        self.os_head = Div(text='OS: ',css_classes=['os-style'],width=75)
        self.dqs_1 = Div(text='Data QA Scientist 1 ',css_classes=['dqs-style'],width=400)
        self.dqs_2 = Div(text='Data QA Scientist 2',css_classes=['dqs-style'],width=400)
        self.dqs_head = Div(text='DQS: ',css_classes=['dqs-style'],width=75)
        self.oa = Div(text='Observing Associate',css_classes=['oa-style'],width=400)
        self.oa_head = Div(text="OA: ",css_classes=['oa-style'],width=75)
        self.em = Div(text='Electronic Mainetenance',css_classes=['em-style'],width=400)
        self.em_head = Div(text='EM: ',css_classes=['em-style'],width=75)
        self.buffer = Div(text='')
        self.date_before = Button(label='Previous Date', css_classes=['next_button'],width=200)
        self.date_after = Button(label='Next Date', css_classes=['next_button'],width=200)
        self.enter_date = TextInput(placeholder = 'YYYY-MM-DD', width=200)
        self.date_btn = Button(label='Enter date', width=200,css_classes=['change_button'])


        main_layout = layout([self.date_title,self.obs_comment,
                  [self.lo_head, self.lo_1,self.lo_2],
                  [self.os_head, self.os_1,self.os_2],
                  [self.dqs_head,self.dqs_1,self.dqs_2],
                  [self.oa_head, self.oa],
                  [self.em_head,self.em],
                  self.buffer,
                  [self.date_before,self.date_after],
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
        self.date_before.on_click(self.prev_day)
        self.date_after.on_click(self.next_day)

Ops = OpsViewer()
Ops.run()
curdoc().title = 'Operations Schedule Viewer'
curdoc().add_root(Ops.layout)
