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

import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials

import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage


class OpsTool(object):
    def __init__(self):
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

    def sched_load(self):
        sheet = client.open_by_url(url).sheet1
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
        print('This is not quite ready',name)

    def email_night_before(self):
        email = self.night_before_email.value
        name = self.night_before_name.value
        
        subject = 'DESI Observing Tomorrow'
        msg = 'Hello {},<br>'.format(name)
        msg += """You are signed up to start your observing shift tomorrow. Please attend
        the planning meeting at 4pm MT/PST where you will meet the rest of your observing team.
        If you'd like to sign on tonight to shadow the current observers for a couple hours, you 
        are certainly welcome. Please let us know if you would like to do that. <br>
        <br>
        Before starting your shift tomorrow, make sure that you are able to connect to all the tools 
        you will need. We recommmend reading through the wiki: https://desi.lbl.gov/trac/wiki/DESIOperations.
        Please let us know if you have any questions.<br>
        <br>

        Cheers,<br>
        Parker & Arjun<br>
        """
        self.send_email(subject, email, msg)
        self.night_before_email.value = ''
        self.night_before_name.value = ''

    def email_follow_up(self):
        email = self.follow_up_email.value
        name = self.follow_up_name.value
        # get email
        subject = 'DESI Observing Feedback'
        msg = 'Hello {},<br>'.format(name)
        msg += """Thank you very much for recently observing for DESI! We would like to collect feedback from all 
        observers after their shift so we might identify areas of improvement. 
        Please take 5 minutes to give us some feedback on your recent observing shift!<br>
        <br>
        https://forms.gle/N246QVnU5tDBcroY8<br>
        <br>
        Cheers,<br>
        Parker & Arjun<br>
        """
        self.send_email(subject, email, msg)
        self.follow_up_email.value = ''
        self.follow_up_name.value = ''

    def send_email(self, subject, user_email, message):
        sender = "pfagrelius@noao.edu" 

        # Create message container - the correct MIME type is multipart/alternative.
        msg = MIMEMultipart('html')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['CC'] = 'dey@noao.edu'

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
        s.sendmail(sender, user_email, text)
        s.quit()

    def layout(self):
        self.report = PreText(text=' ')
        info = Div(text=' ')
        title = Div(text='Operations Planning Tool')
        today_title = Div(text="Today's Observers: ")
        night_report_title = Div(text='Daily Report: ')
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
        self.night_before_btn = Button(label="Email Night Before Info", width=200)
        self.follow_up_btn = Button(label="Email Follow Up", width=200)
        self.update_df_btn = Button(label='Update DataFrame', width=200)

        self.layout = layout([title,today_title,
                  self.data_table,
                  self.update_df_btn,
                  night_report_title,
                  self.report,
                  [[self.one_month_name,self.one_month_email, self.one_month_btn],[self.two_weeks_name,self.two_weeks_email, self.two_weeks_btn],[self.night_before_name,self.night_before_email, self.night_before_btn],[self.follow_up_name,self.follow_up_email, self.follow_up_btn]]])

        
    def run(self):
        self.layout()
        self.daily_report()
        self.update_df_btn.on_click(self.sched_load)
        self.one_month_btn.on_click(self.email_one_month)
        self.two_weeks_btn.on_click(self.email_two_weeks)
        self.night_before_btn.on_click(self.email_night_before)
        self.follow_up_btn.on_click(self.email_follow_up)

Ops = OpsTool()
Ops.run()
curdoc().title = 'Operations Scheduling Tool'
curdoc().add_root(Ops.layout)
