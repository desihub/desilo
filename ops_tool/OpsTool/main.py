"""
Created on May 21, 2020

@author: Parker Fagrelius

Meant to manage the Observing Operations Supervisor Tasks

start server with the following command:
bokeh serve --show OpsTool/ --args
args are all options:
    -l, --local
    -t, --test
    --print_emails
    -s,--semester

view at: http://localhost:5006/OpsTool
"""

import os
import datetime
import socket
import logging
import pandas as pd
import numpy as np

from bokeh.io import curdoc
from bokeh.models import TextInput, Button, ColumnDataSource, RadioButtonGroup, DataTable, DateFormatter, StringFormatter, TableColumn
from bokeh.models.widgets.markups import Div, PreText
from bokeh.layouts import layout
from bokeh.models.widgets import Panel, Tabs

import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials

import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

os.environ['OPSTOOL_DIR'] = '/Users/pfagrelius/Research/DESI/Operations/desilo/ops_tool'

class OpsTool(object):
    def __init__(self, test=False, print_emails=False, semester=None, local=True):
        self.test = test #if testing, use this.
        self.get_all_emails = print_emails #Change this if you want the code to print out all email addresses.
        self.semester = semester #None means all combined. Options are 2021B, 2022A

        #Set up logging
        logging.basicConfig(filename=os.path.join(os.environ['OPSTOOL_DIR'], 'auto_ops_tool.log'), 
                            level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        self.logger = logging.getLogger(__name__)

        self.title = Div(text='Observing Operations Dashboard', css_classes=['h1-title-style'])

        #Get setup for google sheets
        self.credentials = "./credentials.json"
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(self.credentials)
        self.client = gspread.authorize(self.creds)
        self.user_info = pd.read_csv(os.path.join(os.environ['OPSTOOL_DIR'], 'user_info.csv'))

        #Post-observing feedback form
        self.feedback_url = "https://docs.google.com/spreadsheets/d/1rivcM5d5U2_WcVTfNcLFQRkZSE8I55VuEdS3ui2e_VU/edit?resourcekey#gid=1162490958"
        self.feedback_sheet = self.client.open_by_url(self.feedback_url).sheet1
        self.feedback_df = get_as_dataframe(self.feedback_sheet, header=0)

        #Pre-observing checklist
        self.preops_url = 'https://docs.google.com/spreadsheets/d/1HkoRySeJmrU_K39L_jsFLLhXl2mCbzG9OPgacRRN1xU/edit?resourcekey#gid=1462663923'
        self.preops_sheet = self.client.open_by_url(self.preops_url).sheet1
        self.preops_df = get_as_dataframe(self.preops_sheet, header=0)
        for col in ['Timestamp', 'Your Name', 'Start date of your shift']:
            self.preops_df[col] = self.preops_df[col].astype(str)

        #Get observing schedule
        self.url = "https://docs.google.com/spreadsheets/d/1nzShIvgfqqeibVcGpHzm7dSpjJ78vDtWz-3N0wV9hu0/edit#gid=0"
        if local:
            if self.semester == None:
                try:
                    self.df = pd.read_csv(os.path.join(os.environ['OPSTOOL_DIR'], 'obs_schedule.csv'))
                except Exception as e:
                    print(e)
            else:
                try:
                    self.df = pd.read_csv(os.path.join(os.environ['OPSTOOL_DIR'], 'obs_schedule_{}.csv'.format(self.semester)))
                except Exception as e:
                    print(e)
        else:  
            self.sheet = self.client.open_by_url(self.url).sheet1
            self.df = get_as_dataframe(self.sheet, header=0)
            self.df = self.df[['Date', 'Comment', 'LO', 'SO_1', 'SO_2', 'OA', 'EM']]
            self.df.to_csv('obs_schedule.csv', index=False) #save file to disk each time in case want to run locally

        self.df['Date'] = pd.to_datetime(self.df['Date'], format='%m/%d/%y')
        self.today = datetime.datetime.now().strftime('%Y-%m-%d')
        self.today_df = self.df[self.df.Date == self.today]

        #Make per_shift file
        print('start')
        shift_data = []
        
        for ops_type in ['LO','SO_1','SO_2']:
            sd = pd.DataFrame(columns=['Start', 'End', 'Shift', 'Observer'])
            df_ = self.df.copy()
            df_['value_grp'] = (df_[ops_type] != df_[ops_type].shift()).cumsum()
            x_ = df_.groupby(['value_grp',ops_type])
            n = [x[1] for x in x_.count().index]
            sd['Start'] = list(x_.Date.first())
            sd['End'] = list(x_.Date.last())
            sd['Shift'] = ops_type
            sd['Observer'] = n
            shift_data.append(sd)
        self.per_shift_df = pd.concat(shift_data)
        self.per_shift_filen = os.path.join(os.environ['OPSTOOL_DIR'], 'per_shift.csv') 
        self.per_shift_df.to_csv(self.per_shift_filen, index=False)
        print('end')

        #Get per_observer info
        self.per_observer_filen = os.path.join(os.environ['OPSTOOL_DIR'], 'per_observer.csv')
        self.per_observer_df = pd.read_csv(self.per_observer_filen)
        for col in self.per_observer_df.columns:
            self.per_observer_df[col] = self.per_observer_df[col].astype(str)
        
        #For emailing purposes, get location of server
        hostname = socket.gethostname()
        if 'desi' in hostname:
            self.location = 'kpno'
        else:
            self.location = 'home'

        #Get list of all observers and check that we have email addresses for all of them
        all_names = [name.strip() for name in np.hstack([np.unique(self.df.SO_1), np.unique(self.df.SO_2)])]
        self.all_names = np.unique(all_names)
        email_list = []
        print('**These Names Dont have Emails:**')
        for name in self.all_names:
            emails = self.user_info[self.user_info['name'] == name]['email']
            try:
                email = emails.values[0]
                email_list.append(email)
            except:
                print(name)

        # Print all email addresses in case you want to copy and paste into an email
        if self.get_all_emails:
            print(email_list)

    def get_email(self, name):
        """
        Gets email address from user_info.csv
        """
        try:
            email = self.user_info[self.user_info['name'] == str(name).strip()]['email'].values[0]
        except:
            email = None 
        return email

    def gave_feedback(self, shift_df):
        """
        Checks if an observer has filled out the post-observing feedback form.
        Expect columns to be Observer, Shift Type, Start, End
        Returns: None if haven't filled out, Timestamp of last entry into the checklist if they have.
        """
        returns = []
        for i, row in shift_df.iterrows():
            obs = row['Observer']
            these_rows = self.feedback_df[self.feedback_df['Observer Name'] == obs]
            if len(these_rows) > 0:
                last_row = these_rows.iloc[-1]
                try:
                    returns.append(last_row['Timestamp'])
                except:
                    print("Error on feedback")
            else:
                returns.append('None')

    def filled_preops_form(self, shift_df):
        """
        Checks if an observer has filled out the pre-observing checklist.
        Expect columns to be Observer, Shift Type, Start, End
        Returns: None if haven't filled out, Timestamp of last entry into the checklist if they have.
        """
        returns = []
        for i, row in shift_df.iterrows():
            obs = row['Observer']
            these_rows = self.preops_df[self.preops_df['Your Name'] == obs.strip()]
            if len(these_rows) > 0:
                last_row = these_rows.iloc[-1]
                try:
                    returns.append(last_row['Timestamp'])
                except:
                    print("Error on preobs")
            else:
                returns.append('None')
        return returns


    def daily_report(self):
        """Checks who starts their shift tomorrow, two-weeks and in one month. Also 
        checks who completed their shift yesterday. Then compiles a list of people to email
        based on this. This is used predominantly by auto_ops_tool.py but does pritn out 
        in this tool
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
            self.logger.debug("issue with 2 weeks: %s", e)
            two_weeks = None
        try:
            two_weeks_minus_one = self.df.iloc[idx[0]+13]
        except Exception as e:
            self.logger.debug("issue with 2 weeks: %s", e)
            two_weeks_minus_one = None
        
        try:
            one_month = self.df.iloc[idx[0]+30]
        except Exception as e:
            self.logger.debug('issue with 1 month: %s', e)
            one_month = None
        try:
            one_month_minus_one =self.df.iloc[idx[0]+29]
        except Exception as e:
            self.logger.debug('issue with 1 month: %s', e)
            one_month_minus_one = None 

        self.today_emails = {}
        text = ''
        for col in ['LO', 'SO_1', 'SO_2']:
            try:
                if str(today[col]).strip() == str(tomorrow[col]).strip():
                    pass
                else:
                    if str(today[col]) not in [np.nan, '', ' ', 'nan', 'None']:
                        self.today_emails[tomorrow[col]] = [self.get_email(tomorrow[col]), 'tomorrow', col, None]
                        self.timing = 'tomorrow'
            except Exception as e:
                self.logger.debug("Issue with reading tomorrow's shift: %s", e)

            try:
                if str(two_weeks[col]).strip() == str(two_weeks_minus_one[col]).strip():
                    pass
                else:
                    if str(two_weeks[col]) not in ['nan', '', ' ', 'None']:
                        self.today_emails[two_weeks[col]] = [self.get_email(two_weeks[col]), 'two_weeks', col, two_weeks['Date'].strftime('%Y-%m-%d')]
            except Exception as e:
                self.logger.debug("Issue with reading shift 2 weeks from now: %s", e)

            try:
                if str(one_month[col]).strip() == str(one_month_minus_one[col]).strip():
                    pass
                else:
                    if str(one_month[col]) not in ['nan','',' ','None']:
                        self.today_emails[one_month[col]] = [self.get_email(one_month[col]), 'one_month', col, one_month['Date'].strftime('%Y-%m-%d')]
            except Exception as e:
                self.logger.debug("Issue with reading shift 1 month from now: %s", e)

            try:
                if str(today[col]).strip() == str(yesterday[col]).strip():
                    pass
                else:
                    if str(today[col]) not in [np.nan, '', ' ','nan','None']:
                        self.today_emails[yesterday[col]] = [self.get_email(yesterday[col]), 'yesterday', col, None]
            except Exception as e:
                self.logger.debug("Issue with reading yesterday's shift: %s", e)

        for key, values in self.today_emails.items():
            text += key+' '
            for val in values:
                text += str(val)+' '
            text += '\n'

        self.report.text = text

    def email_semester_start(self):
        """
        Emails everyone on a semester schedule to confirm that they are signed up. Do this only once per semester
        """
        df = pd.DataFrame(columns=['Observer', 'Observed', 'VPN_Requested', 'VPN_Sent', 'VPN_Replied', 'VPN_Activated'])
        df['Observer'] = self.all_names

        self.per_observer_df = pd.concat([self.per_observer_df,df])

        self.per_observer_df.drop_duplicates('Observer', keep='first', inplace=True)
        self.per_observer_df.to_csv(self.per_observer_filen, index=False)

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
        """
        Sets up email to remind observers that they are observing in 1 month
        """
        name = self.one_month_name.value
        email = self.one_month_email.value
        t = 'one_month'
        if str(self.one_month_start.value) not in ['nan','None','',' ']:
            date = str(self.one_month_start.value)
        else:
            date = None
        self.email_content(name, email, t, None)

    def email_two_weeks(self):
        """
        Sets up email to remind observers that they are observing in 2 weeks
        """
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
        """
        Sets up email to remind observers that they are observing the following night
        """
        email = self.night_before_email.value
        name = self.night_before_name.value
        t = 'tomorrow'
        if self.weekend_select.active == 0:
            self.timing = 'tomorrow'
        elif self.weekend_select.active == 1:
            self.timing = 'weekend'
        self.email_content(name, email, t, None)


    def email_follow_up(self):
        """
        Sets up email to request observers to complete the post-observing form
        """
        email = self.follow_up_email.value
        name = self.follow_up_name.value
        # get email
        t = 'yesterday'
        self.email_content(name, email, t, None)

    def email_all(self):
        """
        This sends emails to each person in the daily_report. The funcitonality of this button is 
        essentially what the auto_ops_tool does automatically every day.
        """
        print('Sending emails to the following people:', self.today_emails)
        for name, values in self.today_emails.items():
            observer = values[2].split('_')[0]
            self.email_content(name, values[0], values[1], values[3], obs_type=observer)


    def email_content(self, name, email, email_type, date, obs_type=None):
        """Based on the email type, selects the content that should be emailed and then calls the send_email() function.

        date = start date
        obs_type = LO or SO
        """
        msg_dir = os.path.join(os.environ['OPSTOOL_DIR'], 'OpsTool', 'static')
        if email_type == 'semester':
            subject = 'DESI Observing Semester 2021B'
            msg = 'Hello {},<br><br>'.format(name)
            if date is not None:
                msg += '<b> Shift starting {}</b><br><br>'.format(date)
            else:
                print("No start date for {}".format(name))
            msgfile = open(os.path.join(msg_dir, 'semester_start_msg.html'))
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
                msgfile = open(os.path.join(msg_dir, 'weekend_before_msg.html'))
            msg += msgfile.read()
            self.send_email(subject, email, msg)
            msgfile.close()

        elif email_type == 'yesterday':
            subject = 'DESI Observing Feedback'
            msg = 'Hello {},<br>'.format(name)
            msgfile = open(os.path.join(msg_dir, 'follow_up_msg.html'))
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
            msgfile = open(os.path.join(msg_dir, 'one_month_info_msg.html'))
            msg += msgfile.read()
            self.send_email(subject, email, msg)
            msgfile.close()

        else:
            self.logger.debug('Not correct email type')



    def send_email(self, subject, user_email, message):
        """Sends email to an observer from <sender> using gmail smtp server
        """
        sender = "parker.fagrelius@noirlab.edu" 
        if user_email in [None, 'None']:
            pass
        else:
    
            msg = MIMEMultipart('html')
            msg['Subject'] = subject
            msg['From'] = sender
            if self.test:
                msg['To'] = 'parfa30@gmail.com'
                msg['CC'] = 'parker.fagrelius@noirlab.edu'
                all_addrs = ['parfa30@gmail.com', 'parker.fagrelius@noirlab.edu']
                self.logger.debug('test mode, no emails')
            else:
                toaddrs = [addr.strip() for addr in user_email.split(';')]
                all_addrs = [x for x in toaddrs]
                msg['To'] = ", ".join(toaddrs)
                recipients = ['parker.fagrelius@noirlab.edu', 'clpoppett@lbl.gov']
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
        """
        Builds table to show the CUrrent, past and future observing shifts
        """
        #Get info from the per_observer file
        table_df = pd.merge(self.per_observer_df, self.per_shift_df, on=['Observer'], how='outer')

        for col in ['Observed', 'Start', 'End', 'VPN_Requested', 'VPN_Sent', 'VPN_Replied', 'VPN_Activated']:
            table_df[col] = table_df[col].astype(str)

        table_df['Start_index'] = pd.to_datetime(table_df.Start, format='%Y-%m-%d')
        table_df['End_index'] = pd.to_datetime(table_df.End, format='%Y-%m-%d')
        los = table_df[table_df.Shift == 'LO']
        so1 = table_df[table_df.Shift == 'SO_1']
        so2 = table_df[table_df.Shift == 'SO_2']

        today = datetime.datetime.now().strftime('%m/%d/%Y')
        current_df = table_df[(table_df.Start_index<=today)&(table_df.End_index>=today)]

        prev_idx = []
        prev_df = table_df.sort_values(by='End_index') 
        for obs in ['LO', 'SO_1', 'SO_2']:
            prev_idx.append(prev_df[(prev_df.End_index<today)&(prev_df.Shift == obs)].index.values[-1])
        previous_df = prev_df.loc[prev_idx]

        next_idx = []
        next_d = table_df.sort_values(by='Start_index')
        for obs in ['LO', 'SO_1', 'SO_2']:
            next_idx.append(next_d[(next_d.Start_index>today)&(next_d.Shift == obs)].index.values[0])
        next_df = next_d.loc[next_idx]

        current_df['feedback'] = self.gave_feedback(current_df)
        current_df['pre_obs_form'] = self.filled_preops_form(current_df)
        previous_df['feedback'] = self.gave_feedback(previous_df)
        previous_df['pre_obs_form'] = self.filled_preops_form(previous_df)
        next_df['feedback'] = self.gave_feedback(next_df)
        next_df['pre_obs_form'] = self.filled_preops_form(next_df)

        self.current_source = ColumnDataSource(current_df)
        self.previous_source = ColumnDataSource(previous_df)
        self.next_source = ColumnDataSource(next_df)

    def update_observer_df(self):
        """
        Saves changes to the tables to the files
        """
        per_obs_cols = ['Observed', 'VPN_Requested', 'VPN_Sent', 'VPN_Replied', 'VPN_Activated']
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


    def get_main_layout(self):

        table_columns = [
            TableColumn(field="Observer", title='Observer', width=200),
            TableColumn(field='Observed', title='Observed', width=10),
            TableColumn(field='Shift', title='Shift',formatter=StringFormatter(), width=50),
            TableColumn(field='Start', title='Start', formatter=StringFormatter(), width=200),
            TableColumn(field='End', title='End', formatter=StringFormatter(), width=200),
            TableColumn(field='pre_obs_form', title='Pre-Obs Form', formatter=StringFormatter(), width=100),
            TableColumn(field='feedback', title='Post-Obs Feedback', formatter=StringFormatter(), width=100),
            TableColumn(field='VPN_Requested', title='VPN Requested', formatter=StringFormatter(), width=100),
            TableColumn(field='VPN_Sent', title='VPN Email Sent', formatter=StringFormatter(), width=100),
            TableColumn(field='VPN_Replied', title='VPN Replied', formatter=StringFormatter(), width=100),
            TableColumn(field='VPN_Activated', title='VPN Activated', formatter=StringFormatter(), width=100),]


        self.current_table = DataTable(source=self.current_source, columns=table_columns, editable=True, width=1800, height=100, css_classes=['badtable'])
        self.previous_table = DataTable(source=self.previous_source, columns=table_columns, editable=True, width=1800, height=100, css_classes=['badtable'])
        self.next_table = DataTable(source=self.next_source, columns=table_columns, editable=True, width=1800, height=100, css_classes=['badtable'])
        current_title = Div(text='Current Shift', css_classes=['h1-title-style'])
        previous_title = Div(text='Previous Shift', css_classes=['h1-title-style'])
        next_title = Div(text='Next Shift', css_classes=['h1-title-style'])

        self.report = PreText(text=' ', css_classes=['box-style'])
        info = Div(text=' ')
        
        desc = Div(text='Check out the Observing Schedule: https://obsschedule.desi.lbl.gov/OpsViewer ')
        t = "<a href='{}''>Schedule</a><br/><a href='{}''>PreObs Form</a><br/><a href='{}''>Feedback Form</a>".format(self.url, self.preops_url, self.feedback_url)
        today_title = Div(text=t)
        night_report_title = Div(text='Daily Report: ', css_classes=['title-style'])

        self.line1 = Div(text='------------------------------------------------------------------')
        self.enter_date = TextInput(title='Date', placeholder='YYYY-MM-DD', width=200)
        self.last_save = Div(text='Last Saved: {}')
          
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
                            self.report,])
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
        self.email_tab_desc = Div(text=desc)
        self.email_all_btn = Button(label='Send emails to all in report', width=200, css_classes=['change_button'])

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
        self.two_weeks_select = RadioButtonGroup(labels=['SO', 'LO'], active=0)

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

      
    def run(self):
        self.table_source()
        self.get_main_layout()
        self.get_sched_layout()
        self.get_email_layout()
        self.layout = Tabs(tabs=[self.main_tab, self.email_tab, self.sched_tab])
        self.daily_report()
        self.semester_start_btn.on_click(self.email_semester_start)
        self.one_month_btn.on_click(self.email_one_month)
        self.two_weeks_btn.on_click(self.email_two_weeks)
        self.night_before_btn.on_click(self.email_night_before)
        self.follow_up_btn.on_click(self.email_follow_up)
        self.email_all_btn.on_click(self.email_all)
        self.update_observer_df()


import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-l','--local',help='Use locally saved schedule rather than online version. Saves time. Have to run in non-local versions atleast once to get local copy of schedule and should any time theres a change to the schedule', action='store_true', default=False)
parser.add_argument('-t',"--test", help="Test Mode", action='store_true', default=False)
parser.add_argument("--print_emails", help='Prints out a list of emails of all observers', action='store_true',default=False)
parser.add_argument('-s','--semester',help='Identify particular semester. If None, selects all sememsters',choices=[None,'2021B','2022A'],default=None)
args = parser.parse_args()
print(args)
Ops = OpsTool(args.test, args.print_emails, args.semester, args.local)
Ops.run()
curdoc().title = 'Operations Scheduling Tool'
curdoc().add_root(Ops.layout)
curdoc().add_periodic_callback(Ops.update_observer_df, 60000) #twice a day
