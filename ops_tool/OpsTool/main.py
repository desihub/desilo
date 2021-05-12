"""
Created on May 21, 2020

@author: Parker Fagrelius

start server with the following command:

bokeh serve --show OS_Report

view at: http://localhost:5006/OS_Report
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


class OpsTool(object):
    def __init__(self):
        self.test = False 
        self.url = "https://docs.google.com/spreadsheets/d/1vSPSRnhkG7lLRn74pKBqHwSKsVEKMLFnX1nT-ofKWQE/edit#gid=0"
        self.credentials = "/n/home/desiobserver/parkerf/desilo/ops_tool/google_access_account.json"
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(self.credentials)
        self.client = gspread.authorize(self.creds)

        self.df = pd.read_csv('obs_schedule.csv')
        self.today = datetime.datetime.now().strftime('%Y-%m-%d')
        self.today_df = self.df[self.df.Date == self.today]
        self.today_source = ColumnDataSource(self.today_df)

        today_columns = [
            TableColumn(field="Date", title='Date'),
            TableColumn(field="LO_1", title='Lead Observer 1'),
            TableColumn(field="LO_2", title="Lead Observer 2"),
            TableColumn(field='OS_1', title='Observing Scientist 1'),
            TableColumn(field='OS_2', title='Observing Scientist 2'),
            TableColumn(field='DQS', title='Data Quality Scientist')]

        self.data_table = DataTable(source = self.today_source, columns = today_columns, width=1000,height=100)

    def new_day(self):
        self.today = self.enter_date.value
        self.today_df = self.df[self.df.Date == self.today]
        self.today_source.data = self.today_df
        self.daily_report()

    def sched_load(self):
        sheet = self.client.open_by_url(self.url).sheet1
        df = get_as_dataframe(sheet, usecols = [0,1,2,3,4,5,6,7], header = 5)
        df = df.rename(columns={'Unnamed: 1':'Date','Date':'Day', 'Local Lead Observer':'LO_1',
        'Remote Lead Observer':'LO_2', 'OS Remote Early Shift ':'OS_1',
        'OS Remote Late Shift ':'OS_2', 'DQS Remote Shift':'DQS'})
        self.df = df.dropna(thresh=1)
        self.df.Date = pd.to_datetime(self.df.Date,format='%b. %d, %Y')
        self.df.to_csv('obs_schedule.csv',index=False)

    def daily_report(self):
        idx = self.df[self.df.Date == self.today].index
        yesterday = self.df.iloc[idx[0]-1]
        tomorrow = self.df.iloc[idx[0]+1]
        today = self.today_df.iloc[0]
        two_weeks = self.df.iloc[idx[0]+14]
        two_weeks_minus_one = self.df.iloc[idx[0]+13]
        one_month = self.df.iloc[idx[0]+30]
        one_month_minus_one =self.df.iloc[idx[0]+31]
        text = ''
        for col in ['LO_1','LO_2','OS_1','OS_2','DQS']:

            text += '{}:\n'.format(col)
            text += '--------------------\n'
            try:
                if today[col] == tomorrow[col]:
                    pass
                else:
                    if str(today[col]) not in [np.nan, '', ' ','nan']:
                        text += 'Starts {} shift tomorrow: {}\n\n'.format(col, tomorrow[col])
            except Exception as e:
                print("Issue with reading tomorrow's shift: {}".format(e))

            try:
                if two_weeks[col] == two_weeks_minus_one[col]:
                    pass
                else:
                    if str(two_weeks[col]) not in ['nan','',' ']:
                        text += 'Starts {} shift in 2 weeks: {}\n\n'.format(col, two_weeks[col])
            except Exception as e:
                print("Issue with reading shift 2 weeks from now: {}".format(e))

            try:
                if one_month[col] == one_month_minus_one[col]:
                    pass
                else:
                    if str(one_month[col]) not in ['nan','',' ']:
                        text += 'Starts {} shift in 1 month: {}\n\n'.format(col, one_month[col])
            except Exception as e:
                print("Issue with reading shift 1 month from now: {}".format(e))

            try:
                if today[col] == yesterday[col]:
                    pass
                    #text += 'No one finished yesterday\n'
                else:
                    if str(today[col]) not in [np.nan, '', ' ','nan']:
                        text += 'Finished {} shift yesterday: {}\n\n'.format(col, yesterday[col])
            except Exception as e:
                print("Issue with reading yesterday's shift: {}".format(e))

        self.report.text = text

    def email_one_month(self):
        name = self.one_month_name.value
        email = self.one_month_email.value
        print('This is not quite set up',name)

    def email_two_weeks(self):
        email = self.two_weeks_email.value
        name = self.two_weeks_name.value

        subject = 'Preparation for DESI Observing'
        msg = 'Hello {},<br>'.format(name)
        if self.two_weeks_select.active[0] == 0:
            msgfile = open('./OpsTool/static/two_week_info_msg_os.html')
        elif self.two_weeks_select.active[0] == 1:
            msgfile = open('./OpsTool/static/two_week_info_msg_dqs.html')
        msg += msgfile.read()
        self.send_email(subject, email, msg)
        self.two_weeks_email.value = ''
        self.two_weeks_name.value = ''
        msgfile.close()

    def email_night_before(self):
        email = self.night_before_email.value
        name = self.night_before_name.value
        
        subject = 'DESI Observing Tomorrow'
        msg = 'Hello {},<br>'.format(name)
        msgfile = open('./OpsTool/static/night_before_msg.html')
        msg += msgfile.read()
        self.send_email(subject, email, msg)
        self.night_before_email.value = ''
        self.night_before_name.value = ''
        msgfile.close()

    def email_follow_up(self):
        email = self.follow_up_email.value
        name = self.follow_up_name.value
        # get email
        subject = 'DESI Observing Feedback'
        msg = 'Hello {},<br>'.format(name)
        msgfile = open('./OpsTool/static/follow_up_msg.html')
        msg += msgfile.read()
        self.send_email(subject, email, msg)
        self.follow_up_email.value = ''
        self.follow_up_name.value = ''
        msgfile.close()

    def send_email(self, subject, user_email, message):
        sender = "pfagrelius@noao.edu" 

        toaddrs = [user_email]
        # Create message container - the correct MIME type is multipart/alternative.
        msg = MIMEMultipart('html')
        msg['Subject'] = subject
        msg['From'] = sender
        if self.test == False:
            recipients = ['parker.fagrelius@noirlab.edu','arjun.dey@noirlab.edu']
            msg['CC'] = ", ".join(recipients)
            toaddrs.append('parker.fagrelius@noirlab.edu')
            toaddrs.append('arjun.dey@noirlab.edu')
        else:
            msg['CC'] = 'parker.fagrelius@noirlab.edu'
            toaddrs.append('parker.fagrelius@noirlab.edu')

        msg['To'] = user_email

        msgText = MIMEText(message, 'html')
        msg.attach(msgText)
        text = msg.as_string()
        # context = ssl.create_default_context()
        # with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        #     server.login(sender, password)
        #     server.sendmail(sender, user_email, text)
        #     server.quit()
        
        s = smtplib.SMTP('localhost')
        s.sendmail(sender, toaddrs, text)
        s.quit()

    def layout(self):
        self.report = PreText(text=' ')
        info = Div(text=' ')
        title = Div(text='Operations Planning Tool')
        today_title = Div(text="Today's Observers: ")
        night_report_title = Div(text='Daily Report: ')
        self.enter_date = TextInput(title='Date', placeholder = 'YYYY-MM-DD', width=200)
        self.date_btn = Button(label='Change date', width=200)
        self.one_month_email = TextInput(title='Email: ', placeholder='Serena Williams', width=200)
        self.two_weeks_email = TextInput(title='Email: ', placeholder='Lindsay Vonn', width=200)
        self.night_before_email = TextInput(title='Email: ', placeholder='Mia Hamm', width=200)
        self.follow_up_email = TextInput(title='Email: ', placeholder='Danica Patrick', width=200)
        self.one_month_name = TextInput(title='Name: ', placeholder='Serena Williams', width=200)
        self.two_weeks_name = TextInput(title='Name: ', placeholder='Lindsay Vonn', width=200)
        self.night_before_name = TextInput(title='Name: ', placeholder='Mia Hamm', width=200)
        self.follow_up_name = TextInput(title='Name: ', placeholder='Danica Patrick', width=200)
        self.one_month_btn = Button(label="Email One Month Info", width=200)
        self.two_weeks_btn = Button(label="Email Two Weeks Info", width=200)
        self.two_weeks_select = CheckboxGroup(labels=['OS','DQS'], active=[0])
        self.night_before_btn = Button(label="Email Night Before Info", width=200)
        self.follow_up_btn = Button(label="Email Follow Up", width=200)
        self.update_df_btn = Button(label='Update DataFrame', width=200)

        self.layout = layout([title,today_title,
                  self.data_table,
                  [self.enter_date, self.date_btn],
                  self.update_df_btn,
                  night_report_title,
                  self.report,
                  [[self.one_month_name,self.one_month_email,
                  self.one_month_btn],[self.two_weeks_name,self.two_weeks_email,self.two_weeks_select, self.two_weeks_btn],[self.night_before_name,self.night_before_email, self.night_before_btn],[self.follow_up_name,self.follow_up_email, self.follow_up_btn]]])

        
    def run(self):
        self.layout()
        self.daily_report()
        self.date_btn.on_click(self.new_day)
        self.update_df_btn.on_click(self.sched_load)
        self.one_month_btn.on_click(self.email_one_month)
        self.two_weeks_btn.on_click(self.email_two_weeks)
        self.night_before_btn.on_click(self.email_night_before)
        self.follow_up_btn.on_click(self.email_follow_up)

Ops = OpsTool()
Ops.run()
curdoc().title = 'Operations Scheduling Tool'
curdoc().add_root(Ops.layout)