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
        self.test = True
        self.url = "https://docs.google.com/spreadsheets/d/1vSPSRnhkG7lLRn74pKBqHwSKsVEKMLFnX1nT-ofKWQE/edit#gid=0"
        self.credentials = "./google_access_account.json"
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(self.credentials)
        self.client = gspread.authorize(self.creds)

        self.df = pd.read_csv('obs_schedule.csv')
        self.user_info = pd.read_csv('user_info.csv')
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

        all_names = []
        for name in np.unique(self.df.OS_1):
            all_names.append(name.strip())
        for name in np.unique(self.df.OS_2):
            all_names.append(name.strip())
        for name in np.unique(self.df.DQS):
            all_names.append(name.strip())
        all_names = np.unique(all_names)

        for name in all_names:
            emails = self.user_info[self.user_info['name'] == name]['email']
            try:
                email = emails.values[0]

            except:
                print(name)



    def get_email(self, name):
        try:
            email = self.user_info[self.user_info['name'] == name]['email'].values[0]
        except:
            email = None 
        return email


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
        self.today_emails = {}
        text = ''
        for col in ['LO_1','LO_2','OS_1','OS_2','DQS']:

            text += '{}:\n'.format(col)
            text += '--------------------\n'
            try:
                if today[col] == tomorrow[col]:
                    pass
                else:
                    if str(today[col]) not in [np.nan, '', ' ','nan']:
                        text += 'Starts {} shift tomorrow: {} ({})\n\n'.format(col, tomorrow[col], self.get_email(tomorrow[col]))
                        self.today_emails[tomorrow[col]] = [self.get_email(tomorrow[col]), 'tomorrow']
            except Exception as e:
                print("Issue with reading tomorrow's shift: {}".format(e))

            try:
                if two_weeks[col] == two_weeks_minus_one[col]:
                    pass
                else:
                    if str(two_weeks[col]) not in ['nan','',' ']:
                        text += 'Starts {} shift in 2 weeks: {} ({})\n\n'.format(col, two_weeks[col], self.get_email(two_weeks[col]))
                        self.today_emails[two_weeks[col]] = [self.get_email(two_weeks[col]), 'two_weeks']
            except Exception as e:
                print("Issue with reading shift 2 weeks from now: {}".format(e))

            try:
                if one_month[col] == one_month_minus_one[col]:
                    pass
                else:
                    if str(one_month[col]) not in ['nan','',' ']:
                        text += 'Starts {} shift in 1 month: {} ({})\n\n'.format(col, one_month[col], self.get_email(one_month[col]))
                        self.today_emails[one_month[col]] = [self.get_email(one_month[col]), 'one_month']
            except Exception as e:
                print("Issue with reading shift 1 month from now: {}".format(e))

            try:
                if today[col] == yesterday[col]:
                    pass
                    #text += 'No one finished yesterday\n'
                else:
                    if str(today[col]) not in [np.nan, '', ' ','nan']:
                        text += 'Finished {} shift yesterday: {} ({})\n\n'.format(col, yesterday[col], self.get_email(yesterday[col]))
                        self.today_emails[yesterday[col]] = [self.get_email(yesterday[col]), 'yesterday']
            except Exception as e:
                print("Issue with reading yesterday's shift: {}".format(e))

        self.report.text = text

    def email_one_month(self):
        name = self.one_month_name.value
        email = self.one_month_email.value
        print('This is not quite set up',name)
        t = 'one_month'
        self.email_stuff(name, email, t)

    def email_two_weeks(self):
        email = self.two_weeks_email.value
        name = self.two_weeks_name.value

        t = 'two_weeks'
        self.email_stuff(name, email, t)


    def email_night_before(self):
        email = self.night_before_email.value
        name = self.night_before_name.value
        t = 'tomorrow'
        self.email_stuff(name, email, t)


    def email_follow_up(self):
        email = self.follow_up_email.value
        name = self.follow_up_name.value
        # get email
        t = 'yesterday'
        self.email_stuff(name, email, t)


    def email_stuff(self, name, email, type):
        if type == 'tomorrow':
            subject = 'DESI Observing Tomorrow'
            msg = 'Hello {},<br>'.format(name)
            msgfile = open('./OpsTool/static/night_before_msg.html')
            msg += msgfile.read()
            self.send_email(subject, email, msg)
            self.night_before_email.value = ''
            self.night_before_name.value = ''
            msgfile.close()
        elif type == 'yesterday':
            subject = 'DESI Observing Feedback'
            msg = 'Hello {},<br>'.format(name)
            msgfile = open('./OpsTool/static/follow_up_msg.html')
            msg += msgfile.read()
            self.send_email(subject, email, msg)
            self.follow_up_email.value = ''
            self.follow_up_name.value = ''
            msgfile.close()
        elif type == 'two_weeks':
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
        elif type == 'one_month':
            pass
        else:
            print('Not correct type')

    def email_all(self):
        print(self.today_emails)
        for name, values in self.today_emails.items():
            self.email_stuff(name, values[0], values[1])

    def send_email(self, subject, user_email, message):
        sender = "desioperations1@gmail.com" 

        toaddrs = user_email.split('; ')
        print(toaddrs)
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
        print(toaddrs)

        msg['To'] = user_email

        msgText = MIMEText(message, 'html')
        msg.attach(msgText)
        text = msg.as_string()

        smtp_server = "smtp.gmail.com"
        port = 587
        password = 'M@y@ll-4m@kpno'

        context = ssl.create_default_context()
        try:
            server = smtplib.SMTP(smtp_server,port)
            server.ehlo() # Can be omitted
            server.starttls(context=context) # Secure the connection
            server.ehlo() # Can be omitted
            server.login(sender, password)
            server.sendmail(sender, toaddrs, text)
        except Exception as e:
            # Print any error messages to stdout
            print(e)


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
        self.email_all_btn = Button(label='Make all emails',width=200)

        main_layout = layout([title,today_title,
                  self.data_table,
                  [self.enter_date, self.date_btn],
                  self.update_df_btn,
                  night_report_title,
                  self.report,
                  self.email_all_btn,
                  [[self.one_month_name,self.one_month_email, self.one_month_btn],[self.two_weeks_name,self.two_weeks_email, self.two_weeks_btn],[self.night_before_name,self.night_before_email, self.night_before_btn],[self.follow_up_name,self.follow_up_email, self.follow_up_btn]]])
        main_tab = Panel(child=main_layout, title='Main')

        self.sched_source = ColumnDataSource(self.df)
        sched_columns = [TableColumn(field='Day', title='Day', width=10),
                   TableColumn(field='Date', title='Time', width=50),
                   TableColumn(field='Comments', title='Comment', width=150),
                   TableColumn(field='LO_1', title='Lead Obs. 1', width=75),
                   TableColumn(field='LO_2', title='Lead Obs. 2', width=75),
                   TableColumn(field='OS_1', title='Obs. Sci 1', width=75),
                   TableColumn(field='OS_2', title='Obs. Sci 1', width=75),
                   TableColumn(field='DQS', title='Data QA Sci.', width=75)] #, 

        self.sched_table = DataTable(source=self.sched_source, columns=sched_columns, width=1000, height=500)
        sched_layout = layout([title,
                                self.sched_table])
        sched_tab = Panel(child=sched_layout, title='Schedule')

        self.layout = Tabs(tabs=[main_tab, sched_tab])

        
    def run(self):
        self.layout()
        self.daily_report()
        self.date_btn.on_click(self.new_day)
        self.update_df_btn.on_click(self.sched_load)
        self.one_month_btn.on_click(self.email_one_month)
        self.two_weeks_btn.on_click(self.email_two_weeks)
        self.night_before_btn.on_click(self.email_night_before)
        self.follow_up_btn.on_click(self.email_follow_up)
        self.email_all_btn.on_click(self.email_all)

Ops = OpsTool()
Ops.run()
curdoc().title = 'Operations Scheduling Tool'
curdoc().add_root(Ops.layout)
