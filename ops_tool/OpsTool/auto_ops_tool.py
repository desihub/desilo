"""
Created on Juen 9, 2020

@author: Parker Fagrelius

Automatically sends emails to observers rather than using the OpsTool
"""

import os, sys
import pandas as pd
import numpy as np
import datetime
import logging

import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials

import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

os.environ['OPSTOOL_DIR'] = '/Users/pfagrelius/Research/DESI/Operations/desilo/ops_tool'

class AutoOpsTool(object):
    def __init__(self):
        self.test = False

        logging.basicConfig(filename='auto_ops_tool.log',  level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        self.logger = logging.getLogger(__name__)

        self.url = "https://docs.google.com/spreadsheets/d/1vSPSRnhkG7lLRn74pKBqHwSKsVEKMLFnX1nT-ofKWQE/edit#gid=0"
        self.credentials = os.path.join(os.environ['OPSTOOL_DIR'],"google_access_account.json")
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(self.credentials)
        self.client = gspread.authorize(self.creds)
        self.df = pd.read_csv(os.path.join(os.environ['OPSTOOL_DIR'],'obs_schedule_official.csv'))
        self.df['Date'] = pd.to_datetime(self.df['Date'], format='%m/%d/%y')
        self.user_info = pd.read_csv(os.path.join(os.environ['OPSTOOL_DIR'],'user_info.csv'))
        self.today = datetime.datetime.now().strftime('%Y-%m-%d')
        self.logger.info('Running Ops Tool for {}'.format(self.today))
        self.today_df = self.df[self.df.Date == self.today]

    def get_email(self, name):
        try:
            email = self.user_info[self.user_info['name'] == str(name).strip()]['email'].values[0]
        except:
            self.logger.info("This person doesn't have an email: {}".format(name))
            email = None 
        return email


    def daily_report(self):
        idx = self.df[self.df.Date == self.today].index
        try:
            yesterday = self.df.iloc[idx[0]-1]
            tomorrow = self.df.iloc[idx[0]+1]
            today = self.today_df.iloc[0]
        except Exception as e:
            self.logger.debug(e)

        try:
            two_weeks_plus_one = self.df.iloc[idx[0]+15]
            two_weeks = self.df.iloc[idx[0]+14]
            two_weeks_minus_one = self.df.iloc[idx[0]+13]
        except Exception as e:
            self.logger.debug("issue with 2 weeks: {}".format(e))
            two_weeks_plus_one = None
        try:
            two_weeks = self.df.iloc[idx[0]+14]
        except Exception as e:
            self.logger.debug("issue with 2 weeks: {}".format(e))
            two_weeks = None
        try:
            two_weeks_minus_one = self.df.iloc[idx[0]+13]
        except Exception as e:
            self.logger.debug("issue with 2 weeks: {}".format(e))
            two_weeks_minus_one = None
        

        try:
            one_month_plus_one =self.df.iloc[idx[0]+31]
        except Exception as e:
            self.logger.debug('issue with 1 month: {}'.format(e))
            one_month_plus_one = None 
        try:
            one_month = self.df.iloc[idx[0]+30]
        except Exception as e:
            self.logger.debug('issue with 1 month: {}'.format(e))
            one_month = None
        try:
            one_month_minus_one =self.df.iloc[idx[0]+29]
        except Exception as e:
            self.logger.debug('issue with 1 month: {}'.format(e))
            one_month_minus_one = None 

        self.today_emails = {}
        text = ''
        for col in ['LO_1','LO_2','OS_1','OS_2','DQS_1']:
            try:
                if str(today[col]).strip() == str(tomorrow[col]).strip():
                    pass
                else:
                    if str(today[col]) not in [np.nan, '', ' ','nan','None']:
                        self.today_emails[tomorrow[col]] = [self.get_email(tomorrow[col]), 'tomorrow',col,None]
                        self.timing = 'tomorrow'
            except Exception as e:
                self.logger.debug("Issue with reading tomorrow's shift: {}".format(e))

            try:
                if str(two_weeks[col]).strip() == str(two_weeks_minus_one[col]).strip():
                    pass
                else:
                    if str(two_weeks[col]) not in ['nan','',' ','None']:
                        self.today_emails[two_weeks[col]] = [self.get_email(two_weeks[col]), 'two_weeks',col,two_weeks['Date'].strftime('%Y-%m-%d')]
            except Exception as e:
                self.logger.debug("Issue with reading shift 2 weeks from now: {}".format(e))

            try:
                if str(one_month[col]).strip() == str(one_month_minus_one[col]).strip():
                    pass
                else:
                    if str(one_month[col]) not in ['nan','',' ','None']:
                        self.today_emails[one_month[col]] = [self.get_email(one_month[col]), 'one_month',col,one_month['Date'].strftime('%Y-%m-%d')]
            except Exception as e:
                self.logger.debug("Issue with reading shift 1 month from now: {}".format(e))

            try:
                if str(today[col]).strip() == str(yesterday[col]).strip():
                    pass
                else:
                    if str(today[col]) not in [np.nan, '', ' ','nan','None']:
                        self.today_emails[yesterday[col]] = [self.get_email(yesterday[col]), 'yesterday',col,None]
            except Exception as e:
                self.logger.debug("Issue with reading yesterday's shift: {}".format(e))

    def email_all(self):
        self.logger.info('Sending emails to the following people: {}'.format(self.today_emails))
        for name, values in self.today_emails.items():
            self.observer = values[2].split('_')[0]
            if self.observer == 'LO':
                pass
            else:
                self.email_stuff(name, values[0], values[1], values[3])


    def email_stuff(self, name, email, type,date):
        msg_dir = os.path.join(os.environ['OPSTOOL_DIR'],'OpsTool','static')
        if type == 'tomorrow':
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
        elif type == 'yesterday':
            subject = 'DESI Observing Feedback'
            msg = 'Hello {},<br>'.format(name)
            msgfile = open(os.path.join(msg_dir,'follow_up_msg.html'))
            msg += msgfile.read()
            self.send_email(subject, email, msg)

            msgfile.close()
        elif type == 'two_weeks':
            subject = 'Preparation for DESI Observing'
            msg = 'Hello {},<br><br>'.format(name)
            if date is not None:
                msg += '<b> Shift starting {}</b><br><br>'.format(date)
            else:
                msg += '<b> Shift starting {}</b><br><br>'.format(self.two_weeks_start.value)
            if self.observer == 'OS':
                msgfile = open(os.path.join(msg_dir,'two_week_info_msg_os.html'))
            elif self.observer == 'DQS':
                msgfile = open(os.path.join(msg_dir,'two_week_info_msg_dqs.html'))
            msg += msgfile.read()
            self.send_email(subject, email, msg)

            msgfile.close()
        elif type == 'one_month':
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
            self.logger.debug('Not correct type')



    def send_email(self, subject, user_email, message):

        sender = "desioperations1@gmail.com" 
        if user_email in [None,'None']:
            pass
        else:
            toaddrs = user_email.split(';')
            toaddrs = [addr.strip() for addr in toaddrs]
            all_addrs = []
            for x in toaddrs:
                all_addrs.append(x)
            self.logger.debug(toaddrs)

            # Create message container - the correct MIME type is multipart/alternative.
            msg = MIMEMultipart('html')
            msg['Subject'] = subject
            msg['From'] = sender
            if self.test:
                # msg['To'] = 'parfa30@gmail.com'
                # msg['CC'] = 'parker.fagrelius@noirlab.edu'
                # all_addrs.append('parker.fagrelius@noirlab.edu')
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

                smtp_server = "smtp.gmail.com"
                port = 587
                password = os.environ['OPS_PW'] #input("Input password: ")

                context = ssl.create_default_context()
                try:
                    server = smtplib.SMTP(smtp_server,port)
                    server.ehlo() # Can be omitted
                    server.starttls(context=context) # Secure the connection
                    server.ehlo() # Can be omitted
                    server.login(sender, password)
                    server.sendmail(sender, all_addrs, text)
                except Exception as e:
                    # Print any error messages to stdout
                    self.logger.debug(e)

        
    def run(self):
        self.daily_report()
        self.email_all()

if __name__ == "__main__":
    AOT = AutoOpsTool()
    AOT.run()