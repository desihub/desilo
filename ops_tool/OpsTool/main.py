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
import logging
from bokeh.io import curdoc
from bokeh.models import TextInput, Button, TextAreaInput, Select
from bokeh.models.widgets.markups import Div, PreText
from bokeh.layouts import layout, column, row
from bokeh.models.widgets import Panel, Tabs
import datetime
import socket


from bokeh.layouts import column, layout, row, gridplot
from bokeh.models.widgets import Panel
from bokeh.models import CustomJS, ColumnDataSource, Select, Slider, CheckboxGroup, RadioButtonGroup
from bokeh.models import ColumnDataSource, DataTable, DateFormatter, TableColumn
from bokeh.models import CheckboxButtonGroup

import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials

import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

os.environ['OPSTOOL_DIR'] = '/Users/pfagrelius/Research/DESI/Operations/desilo/ops_tool'

class OpsTool(object):
    def __init__(self):
        self.test = True

        logging.basicConfig(filename=os.path.join(os.environ['OPSTOOL_DIR'], 'auto_ops_tool.log'), 
            level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        self.logger = logging.getLogger(__name__)

        self.df = pd.read_csv(os.path.join(os.environ['OPSTOOL_DIR'], 'obs_schedule_official_2.csv'))
        self.df['Date'] = pd.to_datetime(self.df['Date'], format='%m/%d/%y')
        self.user_info = pd.read_csv(os.path.join(os.environ['OPSTOOL_DIR'], 'user_info.csv'))
        self.today = datetime.datetime.now().strftime('%Y-%m-%d')
        self.today_df = self.df[self.df.Date == self.today]
        self.today_source = ColumnDataSource(self.today_df)

        hostname = socket.gethostname()
        if 'desi' in hostname:
            self.location = 'kpno'
        else:
            self.location = 'home'

        today_columns = [
            TableColumn(field="Date", title='Date',formatter=DateFormatter()),
            TableColumn(field="LO", title='Lead Observer 1'),
            TableColumn(field='SO_1', title='Support Observing Scientist 1'),
            TableColumn(field='SO_2', title='Support Observing Scientist 2')]

        self.data_table = DataTable(source=self.today_source, columns=today_columns, width=1000, height=50)

        all_names = []
        for name in np.unique(self.df.SO_1):
            all_names.append(name.strip())
        for name in np.unique(self.df.SO_2):
            all_names.append(name.strip())
        all_names = np.unique(all_names)

        print('These Names Dont have Emails:')
        for name in all_names:
            emails = self.user_info[self.user_info['name'] == name]['email']
            try:
                email = emails.values[0]

            except:
                print(name)

    def get_email(self, name):
        try:
            email = self.user_info[self.user_info['name'] == str(name).strip()]['email'].values[0]
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
        self.df = df.dropna(thresh=1)
        self.df.Date = pd.to_datetime(self.df.Date,format='%b. %d, %Y')
        self.df.to_csv('obs_schedule.csv',index=False)

    def daily_report(self):
        """Checks who starts their shift tomorrow, two-weeks and in one month. Also 
        checks who completed their shift yesterday. Then compiles a list of people to email
        based on this.
        """
        idx = self.df[self.df.Date == self.today].index
        try:
            yesterday = self.df.iloc[idx[0]-1]
            tomorrow = self.df.iloc[idx[0]+1]
            today = self.today_df.iloc[0]
        except Exception as e:
            self.logger.debug(e)

        try:
            two_weeks = self.df.iloc[idx[0]+14]
        except Exception as e:
            self.logger.debug("issue with 2 weeks: %s",e)
            two_weeks = None
        try:
            two_weeks_minus_one = self.df.iloc[idx[0]+13]
        except Exception as e:
            self.logger.debug("issue with 2 weeks: %s",e)
            two_weeks_minus_one = None
        
        try:
            one_month = self.df.iloc[idx[0]+30]
        except Exception as e:
            self.logger.debug('issue with 1 month: %s',e)
            one_month = None
        try:
            one_month_minus_one =self.df.iloc[idx[0]+29]
        except Exception as e:
            self.logger.debug('issue with 1 month: %s',e)
            one_month_minus_one = None 

        self.today_emails = {}
        text = ''
        for col in ['LO','SO_1','SO_2']:
            try:
                if str(today[col]).strip() == str(tomorrow[col]).strip():
                    pass
                else:
                    if str(today[col]) not in [np.nan, '', ' ', 'nan', 'None']:
                        self.today_emails[tomorrow[col]] = [self.get_email(tomorrow[col]), 'tomorrow', col, None]
                        self.timing = 'tomorrow'
            except Exception as e:
                self.logger.debug("Issue with reading tomorrow's shift: %s",e)

            try:
                if str(two_weeks[col]).strip() == str(two_weeks_minus_one[col]).strip():
                    pass
                else:
                    if str(two_weeks[col]) not in ['nan', '', ' ', 'None']:
                        self.today_emails[two_weeks[col]] = [self.get_email(two_weeks[col]), 'two_weeks', col, two_weeks['Date'].strftime('%Y-%m-%d')]
            except Exception as e:
                self.logger.debug("Issue with reading shift 2 weeks from now: %s",e)

            try:
                if str(one_month[col]).strip() == str(one_month_minus_one[col]).strip():
                    pass
                else:
                    if str(one_month[col]) not in ['nan','',' ','None']:
                        self.today_emails[one_month[col]] = [self.get_email(one_month[col]), 'one_month', col, one_month['Date'].strftime('%Y-%m-%d')]
            except Exception as e:
                self.logger.debug("Issue with reading shift 1 month from now: %s",e)

            try:
                if str(today[col]).strip() == str(yesterday[col]).strip():
                    pass
                else:
                    if str(today[col]) not in [np.nan, '', ' ','nan','None']:
                        self.today_emails[yesterday[col]] = [self.get_email(yesterday[col]), 'yesterday', col, None]
            except Exception as e:
                self.logger.debug("Issue with reading yesterday's shift: %s",e)

        for key, values in self.today_emails.items():
            text += key+' '
            for val in values:
                text += str(val)+' '
            text += '\n'

        self.report.text = text

    def email_semester_start(self):
        t = 'semester'
        for obs in ['SO_1','SO_2']: #,
            observers = np.unique(self.df[obs])
            for name in [observers[0]]:
                email = self.get_email(name)
                idx = np.where(self.df[obs] == name)

                first = min(idx[0])
                print(name, email, idx, first)
                start_date = self.df.iloc[first]['Date']
                self.email_content(name, email, t, start_date)
        

    def email_one_month(self):
        name = self.one_month_name.value
        email = self.one_month_email.value
        t = 'one_month'
        self.email_content(name, email, t, None)

    def email_two_weeks(self):
        email = self.two_weeks_email.value
        name = self.two_weeks_name.value
        if self.two_weeks_select.active == 0:
            self.observer = 'SO'
        elif self.two_weeks_select.active == 1:
            self.observer = 'LO'
        t = 'two_weeks'
        self.email_content(name, email, t, None)


    def email_night_before(self):
        email = self.night_before_email.value
        name = self.night_before_name.value
        t = 'tomorrow'
        if self.weekend_select.active == 0:
            self.timing = 'tomorrow'
        elif self.weekend_select.active == 1:
            self.timing = 'weekend'
        self.email_content(name, email, t, None)


    def email_follow_up(self):
        email = self.follow_up_email.value
        name = self.follow_up_name.value
        # get email
        t = 'yesterday'
        self.email_content(name, email, t, None)

    def email_all(self):
        print('Sending emails to the following people:', self.today_emails)
        for name, values in self.today_emails.items():
            observer = values[2].split('_')[0]
            self.email_content(name, values[0], values[1], values[3], obs_type=observer)


    def email_content(self, name, email, email_type, date, obs_type=None):
        """Based on the email type, selects the content that should be emailed and then calls the send_email() function.

        date = start date
        obs_type = LO or SO
        """
        msg_dir = os.path.join(os.environ['OPSTOOL_DIR'],'OpsTool','static')
        if email_type == 'semester':
            subject = 'DESI Observing Semester 2021B'
            msg = 'Hello {},<br>'.format(name)
            if date is not None:
                msg += '<b> Shift starting {}</b><br><br>'.format(date)
            else:
                print("No start date for {}".format(name))
            msgfile = open(os.path.join(msg_dir,'semester_start_msg.html'))
            msg += msgfile.read()
            self.send_email(subject, email, msg)

            msgfile.close()
        if email_type == 'tomorrow':
            subject = 'DESI Observing Tomorrow'
            msg = 'Hello {},<br>'.format(name)
            if self.timing == 'tomorrow':
                subject = 'DESI Observing Tomorrow'
                msgfile = open(os.path.join(msg_dir,'night_before_msg.html'))
            if self.timing == 'weekend':
                subject = 'DESI Observing This Weekend'
                msgfile = open(os.path.join(msg_dir,'weekend_before_msg.html'))
            msg += msgfile.read()
            self.send_email(subject, email, msg)
            msgfile.close()

        elif email_type == 'yesterday':
            subject = 'DESI Observing Feedback'
            msg = 'Hello {},<br>'.format(name)
            msgfile = open(os.path.join(msg_dir,'follow_up_msg.html'))
            msg += msgfile.read()
            self.send_email(subject, email, msg)
            msgfile.close()

        elif email_type == 'two_weeks':
            subject = 'Preparation for DESI Observing'
            msg = 'Hello {},<br><br>'.format(name)
            if date is not None:
                msg += '<b> Shift starting {}</b><br><br>'.format(date)
            else:
                msg += '<b> Shift starting {}</b><br><br>'.format(self.two_weeks_start.value)
            if obs_type == 'SO':
                msgfile = open(os.path.join(msg_dir,'two_week_info_msg_so.html'))
            elif obs_type == 'LO':
                msgfile = open(os.path.join(msg_dir,'two_week_info_msg_lo.html'))
            msg += msgfile.read()
            self.send_email(subject, email, msg)
            msgfile.close()

        elif email_type == 'one_month':
            subject = 'Confirmation of DESI Observing Shift'
            msg = 'Hello {},<br><br>'.format(name)
            if date is not None:
                msg += '<b> Shift starting {}</b><br><br>'.format(date)
            else:
                msg += '<b> Shift starting {}</b><br><br>'.format(self.one_month_start.value)
            msgfile = open(os.path.join(msg_dir,'one_month_info_msg.html'))
            msg += msgfile.read()
            self.send_email(subject, email, msg)
            msgfile.close()

        else:
            self.logger.debug('Not correct email type')



    def send_email(self, subject, user_email, message):
        """Sends email to an observer from desioperations1@gmail.com using gmail smtp server
        """
        sender = "desioperations1@gmail.com" 
        if user_email in [None, 'None']:
            pass
        else:
            toaddrs = user_email.split(';')
            toaddrs = [addr.strip() for addr in toaddrs]
            all_addrs = [x for x in toaddrs]


            # Create message container - the correct MIME type is multipart/alternative.
            msg = MIMEMultipart('html')
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = ", ".join(toaddrs)
            if self.test:
                msg['To'] = 'parfa30@gmail.com'
                msg['CC'] = 'parker.fagrelius@noirlab.edu'
                all_addrs = ['parfa30@gmail.com', 'parker.fagrelius@noirlab.edu']
                self.logger.debug('test mode, no emails')
            else:
                msg['To'] = ", ".join(toaddrs)
                recipients = ['parker.fagrelius@noirlab.edu','arjun.dey@noirlab.edu']
                msg['CC'] = ", ".join(recipients)
                all_addrs.append('parker.fagrelius@noirlab.edu')
                all_addrs.append('arjun.dey@noirlab.edu')

            msgText = MIMEText(message, 'html')
            msg.attach(msgText)
            text = msg.as_string()

            if self.location == 'kpno':
                smtp_server = 'localhost'
                try:
                    server = smtplib.SMTP(smtp_server)
                    server.sendmail(sender, all_addrs, text)
                    server.quit()
                except Exception as e:
                    self.logger.debug(e)

            elif self.location == 'home':
                smtp_server = 'smtp.gmail.com'
                port = 587
                password = os.environ['OPS_PW'] #input("Input password: ")

                context = ssl.create_default_context()
                try:
                    server = smtplib.SMTP(smtp_server,port)
                    server.starttls(context=context) # Secure the connection
                    server.login(sender, password)
                    server.sendmail(sender, all_addrs, text)
                    server.quit()
                except Exception as e:
                    # Print any error messages to stdout
                    self.logger.debug(e)
            else:
                self.logger.debug('Location not identified')


    def get_layout(self):
        self.report = PreText(text=' ', css_classes=['box-style'])
        info = Div(text=' ')
        title = Div(text='Operations Planning Tool', css_classes=['h1-title-style'])
        today_title = Div(text="Today's Observers: ")
        night_report_title = Div(text='Daily Report: ', css_classes=['title-style'])

        self.line1 = Div(text='------------------------------------------------------------------')
        self.enter_date = TextInput(title='Date', placeholder='YYYY-MM-DD', width=200)
        self.date_btn = Button(label='Change date', width=200, css_classes=['change_button'])
        self.email_all_btn = Button(label='Send emails to all in report',width=200, css_classes=['change_button'])
        self.update_df_btn = Button(label='Update DataFrame', width=200, css_classes=['next_button'])

        self.semester_start_btn = Button(label="Semester Start Email (emails all)", width=200, css_classes=['next_button'])

        self.one_month_email = TextInput(title='Email: ', placeholder='Serena Williams', width=200)
        self.one_month_title = Div(text='One Month: ', css_classes=['title-style'])
        self.one_month_name = TextInput(title='Name: ', placeholder='Serena Williams', width=200)
        self.one_month_btn = Button(label="Email One Month Info", width=200, css_classes=['next_button'])
        self.one_month_start = TextInput(title='Date Start: ', placeholder='Month DD, YYYY',width=200)

        self.two_weeks_email = TextInput(title='Email: ', placeholder='Lindsay Vonn', width=200)
        self.two_weeks_title = Div(text='Two Weeks: ', css_classes=['title-style'])
        self.two_weeks_name = TextInput(title='Name: ', placeholder='Lindsay Vonn', width=200)
        self.two_weeks_btn = Button(label="Email Two Weeks Info", width=200, css_classes=['next_button'])
        self.two_weeks_start = TextInput(title='Date Start: ', placeholder='Month DD, YYYY', width=200)
        self.two_weeks_select = RadioButtonGroup(labels=['SO','LO'], active=0)

        self.night_before_email = TextInput(title='Email: ', placeholder='Mia Hamm', width=200)
        self.night_before_title = Div(text='Night/Weekend Before : ', css_classes=['title-style'])
        self.night_before_name = TextInput(title='Name: ', placeholder='Mia Hamm', width=200)
        self.night_before_btn = Button(label="Email Night Before Info", width=200, css_classes=['next_button'])
        self.weekend_select = RadioButtonGroup(labels=['Tomorrow','Weekend'], active=0)

        self.follow_up_email = TextInput(title='Email: ', placeholder='Danica Patrick', width=200)
        self.follow_up_name = TextInput(title='Name: ', placeholder='Danica Patrick', width=200)
        self.follow_up_title = Div(text='Follow Up: ', css_classes=['title-style'])
        self.follow_up_btn = Button(label="Email Follow Up", width=200, css_classes=['next_button'])
             
        main_layout = layout([title,today_title,
                  self.data_table,
                  [self.enter_date, self.date_btn],
                  night_report_title,
                  self.report,
                  self.email_all_btn,
                  self.semester_start_btn,
                  self.line1,
                  [[self.one_month_title, self.one_month_name,self.one_month_email, self.one_month_start, self.one_month_btn],
                  [self.two_weeks_title,self.two_weeks_name,self.two_weeks_email, self.two_weeks_select,self.two_weeks_start,self.two_weeks_btn],
                  [self.night_before_title, self.night_before_name, self.weekend_select, self.night_before_email, self.night_before_btn],
                  [self.follow_up_title,self.follow_up_name,self.follow_up_email, self.follow_up_btn]]])
        main_tab = Panel(child=main_layout, title='Main')

        self.sched_source = ColumnDataSource(self.df)
        sched_columns = [TableColumn(field='Day', title='Day', width=10),
                   TableColumn(field='Date', title='Time', width=50,formatter=DateFormatter()),
                   TableColumn(field='Comments', title='Comment', width=150),
                   TableColumn(field='LO', title='Lead Obs. 1', width=75),
                   TableColumn(field='SO_1', title='Supp. Obs. 1', width=75),
                   TableColumn(field='SO_2', title='Supp. Obs. 2', width=75)] #, 

        self.sched_table = DataTable(source=self.sched_source, columns=sched_columns, width=1000, height=500)
        sched_layout = layout([title, self.sched_table])
        sched_tab = Panel(child=sched_layout, title='Schedule')

        self.layout = Tabs(tabs=[main_tab, sched_tab])

        
    def run(self):
        self.get_layout()
        self.daily_report()
        self.date_btn.on_click(self.new_day)
        self.update_df_btn.on_click(self.sched_load)
        self.semester_start_btn.on_click(self.email_semester_start)
        self.one_month_btn.on_click(self.email_one_month)
        self.two_weeks_btn.on_click(self.email_two_weeks)
        self.night_before_btn.on_click(self.email_night_before)
        self.follow_up_btn.on_click(self.email_follow_up)
        self.email_all_btn.on_click(self.email_all)

Ops = OpsTool()
Ops.run()
curdoc().title = 'Operations Scheduling Tool'
curdoc().add_root(Ops.layout)
