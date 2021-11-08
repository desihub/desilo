"""
Created on Juen 9, 2020

@author: Parker Fagrelius

Automatically sends emails to observers rather than using the OpsTool. Uses a hardcopy (csv) of the scheduled.
"""

import os
import smtplib
import ssl
import datetime
import logging
import socket

import pandas as pd
import numpy as np

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials

os.environ['OPSTOOL_DIR'] = '/n/home/desiobserver/parkerf/desilo/ops_tool'

class AutoOpsTool(object):
    def __init__(self, day=None):
        self.test = False 

        logging.basicConfig(filename=os.path.join(os.environ['OPSTOOL_DIR'], 'auto_ops_tool.log'),
                            level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        self.logger = logging.getLogger(__name__)

        hostname = socket.gethostname()
        if 'desi' in hostname:
            self.location = 'kpno'
        else:
            self.location = 'home'

        self.day = day
        self.url = "https://docs.google.com/spreadsheets/d/1nzShIvgfqqeibVcGpHzm7dSpjJ78vDtWz-3N0wV9hu0/edit#gid=0"
        self.credentials = os.path.join(os.environ['OPSTOOL_DIR'],"credentials.json")
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(self.credentials)
        self.client = gspread.authorize(self.creds)
        self.sheet = self.client.open_by_url(self.url).sheet1
        self.df = get_as_dataframe(self.sheet, header=0)
        self.df = self.df[['Date', 'Comment', 'LO', 'SO_1', 'SO_2', 'OA', 'EM']]

        #self.df = pd.read_csv(os.path.join(os.environ['OPSTOOL_DIR'],'obs_schedule_official_2.csv'))
        self.df['Date'] = pd.to_datetime(self.df['Date'], format='%m/%d/%y')
        self.user_info = pd.read_csv(os.path.join(os.environ['OPSTOOL_DIR'],'user_info.csv'))

        if self.day == None:
            self.today = datetime.datetime.now().strftime('%Y-%m-%d')
        else:
            self.today = self.day
        print(self.today)
        self.today_df = self.df[self.df.Date == self.today]
        self.logger.info('Running Ops Tool for {}'.format(self.today))

        self.summary = '<b>Ops Update for {}</b><br><br>'.format(self.today)

    def get_email(self, name):
        """Retrieves email address of observer from user_info.csv. 
        """
        try:
            email = self.user_info[self.user_info['name'] == str(name).strip()]['email'].values[0]
        except:
            self.logger.info("This person doesn't have an email: {}".format(name))
            self.summary += 'Attempted to email {}. No success. No email in user_info.csv<br>'.format(name)
            email = None 
        return email

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
            self.logger.info(e)

        try:
            two_weeks = self.df.iloc[idx[0]+14]
        except Exception as e:
            self.logger.info("issue with 2 weeks: %s",e)
            self.summary += "issue with 2 weeks: %s<br>" % e
            two_weeks = None
        try:
            two_weeks_minus_one = self.df.iloc[idx[0]+13]
        except Exception as e:
            self.logger.info("issue with 2 weeks: %s",e)
            self.summary += "issue with 2 weeks: %s<br>" % e
            two_weeks_minus_one = None
        
        try:
            one_month = self.df.iloc[idx[0]+30]
        except Exception as e:
            self.logger.info('issue with 1 month: %s',e)
            self.summary += 'issue with 1 month: %s<br>' % e
            one_month = None
        try:
            one_month_minus_one =self.df.iloc[idx[0]+29]
        except Exception as e:
            self.logger.info('issue with 1 month: %s',e)
            self.summary += 'issue with 1 month: %s<br>' % e
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
                self.logger.info("Issue with reading tomorrow's shift: %s",e)
                self.summary += "Issue with reading tomorrow's shift: %s<br>" % e

            try:
                if str(two_weeks[col]).strip() == str(two_weeks_minus_one[col]).strip():
                    pass
                else:
                    if str(two_weeks[col]) not in ['nan', '', ' ', 'None']:
                        self.today_emails[two_weeks[col]] = [self.get_email(two_weeks[col]), 'two_weeks', col, two_weeks['Date'].strftime('%Y-%m-%d')]
            except Exception as e:
                self.logger.info("Issue with reading shift 2 weeks from now: %s",e)
                self.summary += "Issue with reading shift 2 weeks from now: %s<br>" % e

            try:
                if str(one_month[col]).strip() == str(one_month_minus_one[col]).strip():
                    pass
                else:
                    if str(one_month[col]) not in ['nan','',' ','None']:
                        self.today_emails[one_month[col]] = [self.get_email(one_month[col]), 'one_month', col, one_month['Date'].strftime('%Y-%m-%d')]
            except Exception as e:
                self.logger.info("Issue with reading shift 1 month from now: %s",e)
                self.summary += "Issue with reading shift 1 month from now: %s<br>" % e

            try:
                if str(today[col]).strip() == str(yesterday[col]).strip():
                    pass
                else:
                    if str(today[col]) not in [np.nan, '', ' ','nan','None']:
                        self.today_emails[yesterday[col]] = [self.get_email(yesterday[col]), 'yesterday', col, None]
            except Exception as e:
                self.logger.info("Issue with reading yesterday's shift: %s",e)
                self.summary += "Issue with reading yesterday's shift: %s<br>" % e

    def email_all(self):
        """Call email_content() for each of the people gathered in the daily report
        """
        self.logger.info('Sending emails to the following people: %s', self.today_emails)
        self.summary += 'Sending emails to the following people: %s<br><br>' % self.today_emails
        for name, values in self.today_emails.items():
            obs_type = values[2].split('_')[0]
            self.email_content(name, values[0], values[1], values[3], obs_type)

    def email_content(self, name, email, email_type, date, obs_type):
        """Based on the email type, selects the content that should be emailed and then calls the send_email() function.

        date = start date
        obs_type = LO or SO
        """
        msg_dir = os.path.join(os.environ['OPSTOOL_DIR'], 'OpsTool', 'static')

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
            msgfile = open(os.path.join(msg_dir, 'one_month_info_msg.html'))
            msg += msgfile.read()
            self.send_email(subject, email, msg)
            msgfile.close()

        else:
            self.logger.info('Incorrect email_type sent')

    def send_email(self, subject, obs_email, message):
        """Sends email to an observer from desioperations1@gmail.com using gmail smtp server
        """
        sender = 'clpoppett@lbl.gov' 
        if obs_email in [None, 'None']:
            pass
        else:
            toaddrs = obs_email.split(';')
            toaddrs = [addr.strip() for addr in toaddrs]
            all_addrs = [x for x in toaddrs]
            self.logger.info('Sending email to %s' % str(toaddrs))
            self.summary += 'Sending email to %s<br>' % str(toaddrs)

            msg = MIMEMultipart('html')
            msg['Subject'] = subject
            msg['From'] = sender
            if self.test:
                msg['To'] = 'parfa30@gmail.com'
                msg['CC'] = 'clpoppett@lbl.gov'
                all_addrs = ['parfa30@gmail.com', 'clpoppett@lbl.gov']
                self.logger.info('test mode, no emails')
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
                    self.logger.info(e)
                    self.summary += 'Issue with emailing: %s<br>' % e

            elif self.location == 'home':
                smtp_server = 'smtp.gmail.com'
                port = 587
                password = os.environ['OPS_PW'] #input("Input password: ")

                context = ssl.create_default_context()
                try:
                    server = smtplib.SMTP(smtp_server, port)
                    server.starttls(context=context) # Secure the connection
                    server.login(sender, password)
                    server.sendmail(sender, all_addrs, text)
                    server.quit()
                except Exception as e:
                    self.logger.info(e)
                    self.summary += 'Issue with emailing: %s<br>' % e
            else:
                self.logger.info('Location not identified')

    def email_summary(self):
        subject = 'DESI Ops Tool Summary - {}'.format(self.today)
        sender = 'desioperations1@gmail.com'
        msg = MIMEMultipart('html')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = 'parker.fagrelius@noirlab.edu'
        all_addrs = ['parker.fagrelius@noirlab.edu']

        msgText = MIMEText(self.summary, 'html')
        msg.attach(msgText)
        text = msg.as_string()

        if self.location == 'kpno':
            smtp_server = 'localhost'
            try:
                server = smtplib.SMTP(smtp_server)
                server.sendmail(sender, all_addrs, text)
                server.quit()
                self.logger.info('Sent email summary to Parker')
            except Exception as e:
                self.logger.info(e)

        elif self.location == 'home':
            smtp_server = 'smtp.gmail.com'
            port = 587
            password = os.environ['OPS_PW'] #input("Input password: ")

            context = ssl.create_default_context()
            try:
                server = smtplib.SMTP(smtp_server, port)
                server.starttls(context=context) # Secure the connection
                server.login(sender, password)
                server.sendmail(sender, all_addrs, text)
                server.quit()
            except Exception as e:
                self.logger.info(e)
        else:
            self.logger.info('Location not identified')
        
    def run(self):
        self.daily_report()
        self.email_all()
        self.email_summary()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', type=str, help='YYYY-MM-DD')
    args = parser.parse_args()

    if args.date:
        AOT = AutoOpsTool(args.date)
    else:
        AOT = AutoOpsTool()
    AOT.run()
