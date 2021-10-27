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
from bokeh.models import ColumnDataSource, DataTable, DateFormatter, StringFormatter, BooleanFormatter, TableColumn
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
        self.get_all_emails = False #Change this if you want the code to print out all email addresses.
        self.semester = '2022A' #None means all combined. Options are 2021B, 2022A

        logging.basicConfig(filename=os.path.join(os.environ['OPSTOOL_DIR'], 'auto_ops_tool.log'), 
            level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        self.logger = logging.getLogger(__name__)

        self.url = "https://docs.google.com/spreadsheets/d/1nzShIvgfqqeibVcGpHzm7dSpjJ78vDtWz-3N0wV9hu0/edit#gid=0"
        self.feedback_url = "https://docs.google.com/spreadsheets/d/1rivcM5d5U2_WcVTfNcLFQRkZSE8I55VuEdS3ui2e_VU/edit?resourcekey#gid=1162490958"
        self.preops_url = 'https://docs.google.com/spreadsheets/d/1HkoRySeJmrU_K39L_jsFLLhXl2mCbzG9OPgacRRN1xU/edit?resourcekey#gid=1462663923'
        self.credentials = "./credentials.json"
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(self.credentials)
        self.client = gspread.authorize(self.creds)
        #self.sheet = self.client.open_by_url(self.url).sheet1
        #self.df = get_as_dataframe(self.sheet, header=0)
        #self.df = self.df[['Date', 'Comment', 'LO', 'SO_1', 'SO_2', 'OA', 'EM']]

        self.feedback_sheet = self.client.open_by_url(self.feedback_url).sheet1
        self.feedback_df = get_as_dataframe(self.feedback_sheet, header=0)

        self.preops_sheet = self.client.open_by_url(self.preops_url).sheet1
        self.preops_df = get_as_dataframe(self.preops_sheet, header=0)
        for col in ['Timestamp','Your Name','Start date of your shift']:
            self.preops_df[col] = self.preops_df[col].astype(str)

        self.title = Div(text='Observing Operations Dashboard', css_classes=['h1-title-style'])

        if self.semester == None:
            pass
        else:
            try:
                self.df = pd.read_csv(os.path.join(os.environ['OPSTOOL_DIR'], 'obs_schedule_{}.csv'.format(self.semester)))
            except Exception as e:
                print(e)
        self.df['Date'] = pd.to_datetime(self.df['Date'], format='%m/%d/%y')

        self.user_info = pd.read_csv(os.path.join(os.environ['OPSTOOL_DIR'], 'user_info.csv'))
        self.today = datetime.datetime.now().strftime('%Y-%m-%d')
        self.today_df = self.df[self.df.Date == self.today]

        self.per_shift_filen = os.path.join(os.environ['OPSTOOL_DIR'], 'per_shift.csv') 
        self.per_shift_df = pd.read_csv(self.per_shift_filen)
        self.per_observer_filen = os.path.join(os.environ['OPSTOOL_DIR'], 'per_observer.csv')
        self.per_observer_df = pd.read_csv(self.per_observer_filen)
        for col in self.per_observer_df.columns:
            self.per_observer_df[col] = self.per_observer_df[col].astype(str)

        hostname = socket.gethostname()
        if 'desi' in hostname:
            self.location = 'kpno'
        else:
            self.location = 'home'


        all_names = []
        for name in np.unique(self.df.SO_1):
            all_names.append(name.strip())
        for name in np.unique(self.df.SO_2):
            all_names.append(name.strip())
        all_names = np.unique(all_names)
        self.all_names = all_names

        email_list = []
        print('These Names Dont have Emails:')
        for name in all_names:
            emails = self.user_info[self.user_info['name'] == name]['email']
            try:
                email = emails.values[0]
                email_list.append(email)
            except:
                print(name)


        if self.get_all_emails:
            print(email_list)

    def gave_feedback(self, shift_df):
        """Expect columns to be Observer, Shift Type, Start, End
        """
        returns = []
        for i, row in shift_df.iterrows():
            obs = row['Observer']
            these_rows = self.feedback_df[self.feedback_df['Observer Name'] == obs]
            try:
                last_row = these_rows.iloc[[-1]]
                if row['Start'] == last_row['Observing Start'].values[0]:
                    returns.append(last_row['Timestamp'].values[0])
                else:
                    returns.append('{}'.format(last_row['Timestamp'].values[0]))
            except:
                returns.append('None')
        return returns

    def filled_preops_form(self, shift_df):
        """Expect columns to be Observer, Shift Type, Start, End
        """
        returns = []
        for i, row in shift_df.iterrows():
            obs = row['Observer']
            these_rows = self.preops_df[self.preops_df['Your Name'] == obs.strip()]
            try:
                last_row = these_rows.iloc[[-1]]
                if row['Start'] == last_row['Start date of your shift'].values[0]:
                    returns.append(last_row['Timestamp'].values[0])
                else:
                    returns.append('{}'.format(last_row['Timestamp'].values[0]))
            except:
                returns.append('None')
        return returns


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
        #Do just once at the beginning of the semester
        df = pd.DataFrame(columns=['Observer','Observed','VPN_Requested','VPN_Sent','VPN_Replied','VPN_Activated'])
        df['Observer'] = self.all_names

        self.per_observer_df = pd.concat([self.per_observer_df,df])

        self.per_observer_df.drop_duplicates('Observer',keep='first',inplace=True)
        self.per_observer_df.to_csv(self.per_observer_filen,index=False)

        t = 'semester'
        for obs in ['SO_1','SO_2']:
            for name in np.unique(df['Observer']):
                email = self.get_email(name)
                idx = np.where(self.df[obs] == name)
                if len(idx[0])>0:
                    first = min(idx[0])
                    start_date = self.df.iloc[first]['Date'].date()
                    print(name, start_date)
                    self.email_content(name, email, t, start_date)
        

    def email_one_month(self):
        name = self.one_month_name.value
        email = self.one_month_email.value
        t = 'one_month'
        if str(self.one_month_start.value) not in ['nan','None','',' ']:
            date = str(self.one_month_start.value)
        else:
            date = None
        self.email_content(name, email, t, None)

    def email_two_weeks(self):
        email = self.two_weeks_email.value
        name = self.two_weeks_name.value
        if self.two_weeks_select.active == 0:
            self.observer = 'SO'
        elif self.two_weeks_select.active == 1:
            self.observer = 'LO'
        t = 'two_weeks'
        if str(self.two_weeks_start.value) not in ['nan','None','',' ']:
            date = str(self.two_weeks_start.value)
        else:
            date = None
        self.email_content(name, email, t, date, obs_type=self.observer)


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
            msg = 'Hello {},<br><br>'.format(name)
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

            print('here')
            print(obs_type)
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
        sender = "parker.fagrelius@noirlab.edu" 
        if user_email in [None, 'None']:
            pass
        else:
            toaddrs = user_email.split(';')
            print(toaddrs)
            toaddrs = [addr.strip() for addr in toaddrs]
            print(toaddrs)
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
                recipients = ['parker.fagrelius@noirlab.edu','clpoppett@lbl.gov']
                msg['CC'] = ", ".join(recipients)
                all_addrs.append('parker.fagrelius@noirlab.edu')
                all_addrs.append('clpoppett@lbl.gov')

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
                print('here')
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
                    print(e)
                    self.logger.debug(e)
            else:
                self.logger.debug('Location not identified')


    def table_source(self):
        table_df = pd.merge(self.per_observer_df, self.per_shift_df, on=['Observer'],how='outer')

        for col in ['Observed','Start','End','VPN_Requested','VPN_Sent','VPN_Replied','VPN_Activated']:
            table_df[col] = table_df[col].astype(str)

        table_df['Start_index'] = pd.to_datetime(table_df.Start, format='%m/%d/%Y')
        table_df['End_index'] = pd.to_datetime(table_df.End, format='%m/%d/%Y')
        today = datetime.datetime.now().strftime('%m/%d/%Y')

        
        current_df = table_df[(table_df.Start_index<=today)&(table_df.End_index>=today)]

        los = table_df[table_df.Shift == 'LO']
        so1 = table_df[table_df.Shift == 'SO_1']
        so2 = table_df[table_df.Shift == 'SO_2']
        prev_idx = []
        prev_df = table_df.sort_values(by='End_index') #et_index('End_index',drop=False).sort_index()
        for obs in ['LO','SO_1','SO_2']:
            prev_idx.append(prev_df[(prev_df.End_index<today)&(prev_df.Shift == obs)].index.values[-1])
        previous_df = prev_df.loc[prev_idx]

        next_idx = []
        next_d = table_df.sort_values(by='Start_index')
        for obs in ['LO','SO_1','SO_2']:
            next_idx.append(next_d[(next_d.Start_index>today)&(next_d.Shift == obs)].index.values[0])
        next_df = next_d.loc[next_idx]


        for df in [current_df, previous_df, next_df]:
            df['feedback'] = self.gave_feedback(df)
            df['pre_obs_form'] = self.filled_preops_form(df)

        self.current_source = ColumnDataSource(current_df)
        self.previous_source = ColumnDataSource(previous_df)
        self.next_source = ColumnDataSource(next_df)


    def get_main_layout(self):
            #TableColumn(field='post_obs',title='Post Obs Email', formatter=StringFormatter()),
            #TableColumn(field='one_month',title='One Month Email', formatter=StringFormatter()),
            #TableColumn(field='two_week',title='Two Weeks Email', formatter=StringFormatter()),
            #TableColumn(field='night_before',title='Night Before Email', formatter=StringFormatter()),

        table_columns = [
            TableColumn(field="Observer", title='Observer', width=200),
            TableColumn(field='Observed', title='Observed', width=10),
            TableColumn(field='Shift',title='Shift',formatter=StringFormatter(), width=50),
            TableColumn(field='Start',title='Start', formatter=StringFormatter(),width=200),
            TableColumn(field='End',title='End', formatter=StringFormatter(),width=200),
            TableColumn(field='pre_obs_form',title='Pre-Obs Form', formatter=StringFormatter(),width=100),
            TableColumn(field='feedback',title='Post-Obs Feedback', formatter=StringFormatter(),width=100),
            TableColumn(field='VPN_Requested',title='VPN Requested', formatter=StringFormatter(),width=100),
            TableColumn(field='VPN_Sent',title='VPN Email Sent', formatter=StringFormatter(),width=100),
            TableColumn(field='VPN_Replied',title='VPN Replied', formatter=StringFormatter(),width=100),
            TableColumn(field='VPN_Activated',title='VPN Activated', formatter=StringFormatter(),width=100),]


        self.current_table = DataTable(source=self.current_source, columns=table_columns, editable=True, width=1800, height=100, css_classes=['badtable'])
        self.previous_table = DataTable(source=self.previous_source, columns=table_columns, editable=True, width=1800, height=100, css_classes=['badtable'])
        self.next_table = DataTable(source=self.next_source, columns=table_columns, editable=True, width=1800, height=100, css_classes=['badtable'])
        current_title = Div(text='Current Shift', css_classes=['h1-title-style'])
        previous_title = Div(text='Previous Shift', css_classes=['h1-title-style'])
        next_title = Div(text='Next Shift', css_classes=['h1-title-style'])

        self.report = PreText(text=' ', css_classes=['box-style'])
        info = Div(text=' ')
        
        desc = Div(text='Check out the Observing Schedule: https://obsschedule.desi.lbl.gov/OpsViewer ')
        today_title = Div(text="PreObs Form: https://docs.google.com/spreadsheets/d/1HkoRySeJmrU_K39L_jsFLLhXl2mCbzG9OPgacRRN1xU/edit?resourcekey#gid=1462663923<br/>Feedback Form: https://docs.google.com/spreadsheets/d/1rivcM5d5U2_WcVTfNcLFQRkZSE8I55VuEdS3ui2e_VU/edit?resourcekey#gid=1162490958 ")
        night_report_title = Div(text='Daily Report: ', css_classes=['title-style'])

        self.line1 = Div(text='------------------------------------------------------------------')
        self.enter_date = TextInput(title='Date', placeholder='YYYY-MM-DD', width=200)
        self.date_btn = Button(label='Change date', width=200, css_classes=['change_button'])
        self.last_save = Div(text='Last Saved: {}')
        
        #                  self.data_table,     
        main_layout = layout([self.title,today_title,
                  desc,
                  current_title,
                  self.current_table,
                  previous_title,
                  self.previous_table,
                  next_title,
                  self.next_table,
                  self.last_save,
                  night_report_title,
                  self.report,
                  ])
        self.main_tab = Panel(child=main_layout, title='Main')

    def get_sched_layout(self):
        self.sched_source = ColumnDataSource(self.df)
        sched_columns = [
                   TableColumn(field='Date', title='Time', width=50,formatter=DateFormatter()),
                   TableColumn(field='Comment', title='Comment', width=150),
                   TableColumn(field='LO', title='Lead Obs. 1', width=75),
                   TableColumn(field='SO_1', title='Supp. Obs. 1', width=75),
                   TableColumn(field='SO_2', title='Supp. Obs. 2', width=75)] #, 

        self.sched_table = DataTable(source=self.sched_source, columns=sched_columns, width=1000, height=500)
        sched_layout = layout([self.title, self.sched_table])
        self.sched_tab = Panel(child=sched_layout, title='Schedule')



    def get_email_layout(self):
        desc = """You can use this page to send emails to individual observers or use the "Semester Start Email" to 
        send an email to each person in the new semester. Note that that auto_ops_tool.py is being run every day
        with a cron job at desiobserver@desi-4. It essentially does what the "Send emails to all in report" button
        does.
        """
        self.email_tab_desc = Div(text = desc)
        self.email_all_btn = Button(label='Send emails to all in report',width=200, css_classes=['change_button'])

        self.semester_start_btn = Button(label="Semester Start Email (emails all)", width=200, css_classes=['next_button'])

        self.one_month_email = TextInput(title='Email: ', placeholder='Serena Williams', width=200)
        self.one_month_title = Div(text='One Month: ', css_classes=['h1-title-style'])
        self.one_month_name = TextInput(title='Name: ', placeholder='Serena Williams', width=200)
        self.one_month_btn = Button(label="Email One Month Info", width=200, css_classes=['next_button'])
        self.one_month_start = TextInput(title='Date Start: ', placeholder='Month DD, YYYY',width=200)

        self.two_weeks_email = TextInput(title='Email: ', placeholder='Lindsay Vonn', width=200)
        self.two_weeks_title = Div(text='Two Weeks: ', css_classes=['h1-title-style'])
        self.two_weeks_name = TextInput(title='Name: ', placeholder='Lindsay Vonn', width=200)
        self.two_weeks_btn = Button(label="Email Two Weeks Info", width=200, css_classes=['next_button'])
        self.two_weeks_start = TextInput(title='Date Start: ', placeholder='Month DD, YYYY', width=200)
        self.two_weeks_select = RadioButtonGroup(labels=['SO','LO'], active=0)

        self.night_before_email = TextInput(title='Email: ', placeholder='Mia Hamm', width=200)
        self.night_before_title = Div(text='Night/Weekend Before : ', css_classes=['h1-title-style'])
        self.night_before_name = TextInput(title='Name: ', placeholder='Mia Hamm', width=200)
        self.night_before_btn = Button(label="Email Night Before Info", width=200, css_classes=['next_button'])
        self.weekend_select = RadioButtonGroup(labels=['Tomorrow','Weekend'], active=0)

        self.follow_up_email = TextInput(title='Email: ', placeholder='Danica Patrick', width=200)
        self.follow_up_name = TextInput(title='Name: ', placeholder='Danica Patrick', width=200)
        self.follow_up_title = Div(text='Follow Up: ', css_classes=['h1-title-style'])
        self.follow_up_btn = Button(label="Email Follow Up", width=200, css_classes=['next_button'])

        email_layout = layout([self.title,
                  self.email_tab_desc, 
                  self.email_all_btn,
                  self.semester_start_btn,
                  [self.one_month_title, self.one_month_name,self.one_month_email, self.one_month_start, self.one_month_btn],
                  [self.two_weeks_title,self.two_weeks_name,self.two_weeks_email, self.two_weeks_select,self.two_weeks_start,self.two_weeks_btn],
                  [self.night_before_title, self.night_before_name, self.weekend_select, self.night_before_email, self.night_before_btn],
                  [self.follow_up_title,self.follow_up_name,self.follow_up_email, self.follow_up_btn]])
        self.email_tab = Panel(child=email_layout, title='Email')

    def update_observer_df(self):
        per_obs_cols = ['Observed','VPN_Requested','VPN_Sent','VPN_Replied','VPN_Activated']
        for tbl in [self.current_table, self.previous_table, self.next_table]:
            new_df = tbl.source.to_df()
            xx = self.per_observer_df[self.per_observer_df.Observer.isin(new_df.Observer)]

            for i, row in xx.iterrows():
                obs = row['Observer']
                x = new_df[new_df.Observer == obs].iloc[0]
                for col in per_obs_cols:
                    try:
                        self.per_observer_df.at[i, col] = str(x[col])
                    except:
                        print('here, didnt work')
                        pass

        self.per_observer_df.to_csv(self.per_observer_filen, index=False)
        now = datetime.datetime.now()
        self.last_save.text = 'Last Saved: {}'.format(str(now))
        
    def run(self):
        self.table_source()
        self.get_main_layout()
        self.get_sched_layout()
        self.get_email_layout()
        self.layout = Tabs(tabs=[self.main_tab, self.email_tab, self.sched_tab])
        #self.current_table.source.on_change('data',self.update_observer_df)
        self.daily_report()
        self.date_btn.on_click(self.new_day)
        #self.update_df_btn.on_click(self.sched_load)
        self.semester_start_btn.on_click(self.email_semester_start)
        self.one_month_btn.on_click(self.email_one_month)
        self.two_weeks_btn.on_click(self.email_two_weeks)
        self.night_before_btn.on_click(self.email_night_before)
        self.follow_up_btn.on_click(self.email_follow_up)
        self.email_all_btn.on_click(self.email_all)
        self.update_observer_df()

Ops = OpsTool()
Ops.run()
curdoc().title = 'Operations Scheduling Tool'
curdoc().add_root(Ops.layout)
curdoc().add_periodic_callback(Ops.update_observer_df, 60000) #twice a day
