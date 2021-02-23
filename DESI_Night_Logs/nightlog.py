"""
Created on April 9, 2020
@author: Satya Gontcho A Gontcho
"""

import os
import glob
import json
import pandas as pd
import numpy as np
from datetime import datetime

from astropy.time import TimezoneInfo
import astropy.units.si as u


class NightLog(object):
    """
        During a night of observing with the Dark Energy Spectroscopic Instrument (DESI),
            observers are required to provide a detailed account of the events of the night.
        The DESI Night Intake (DNI) provides observers with an interface to write the nightlog
            in the proper formatting (textile for the eLog) while providing a platform to
            follow live the night progress.
    """

    def __init__(self,year,month,day):
        """
            Setup the nightlog framework for a given obsday.
        """
        self.obsday = year+month+day
        self.root_dir = os.path.join(os.environ['NL_DIR'],self.obsday)
        self.image_dir = os.path.join(self.root_dir,"images")
        self.os_dir = os.path.join(self.root_dir,"OperationsScientist")
        self.dqs_dir = os.path.join(self.root_dir,"DataQualityAssessment")
        self.other_dir = os.path.join(self.root_dir,"OtherInput")

        self.os_pb = os.path.join(self.os_dir,'problems.pkl')
        self.dqs_pb = os.path.join(self.dqs_dir,'problems.pkl')
        self.other_pb = os.path.join(self.other_dir,'problems.pkl')
        self.os_pb_file = os.path.join(self.os_dir,'problems')
        self.dqs_pb_file = os.path.join(self.dqs_dir,'problems')
        self.other_pb_file = os.path.join(self.other_dir,'problems')

        self.objectives = os.path.join(self.os_dir,'objectives.pkl')
        self.objectives_file = os.path.join(self.os_dir,'objectives')

        self.milestone = os.path.join(self.os_dir,'milestones.pkl')
        self.milestone_file = os.path.join(self.os_dir,'milestones')

        self.os_cl = os.path.join(self.os_dir,'checklist.pkl')
        self.dqs_cl = os.path.join(self.dqs_dir,'checklist.pkl')
        self.os_cl_file = os.path.join(self.os_dir,'checklist')
        self.dqs_cl_file = os.path.join(self.dqs_dir,'checklist')

        self.os_exp = os.path.join(self.os_dir,'exposures.pkl')
        self.os_exp_file = os.path.join(self.os_dir,'exposures')
        self.exp_file = os.path.join(self.dqs_dir,'exposures.pkl')
        self.dqs_exp_file = os.path.join(self.dqs_dir,'exposures')

        self.weather = os.path.join(self.os_dir,'weather.pkl')
        self.weather_file = os.path.join(self.os_dir,'weather')

        self.meta_json = os.path.join(self.root_dir,'nightlog_meta.json')
        self.image_file = os.path.join(self.image_dir, 'image_list')
        self.upload_image_file = os.path.join(self.image_dir, 'upload_image_list')
        self.contributer_file = os.path.join(self.root_dir, 'contributer_file')
        self.summary_file = os.path.join(self.root_dir, 'summary_file')
        self.explist_file = os.path.join(self.root_dir, 'exposures.csv')
        self.telem_plots_file = os.path.join(self.root_dir, 'telem_plots.png')

        # Set this if you want to allow for replacing lines with a timestamp or not
        self.replace = True

        self.utc = TimezoneInfo()
        self.kp_zone = TimezoneInfo(utc_offset=-7*u.hour)


    def initializing(self):
        """ Creates the folders where all the files used to create the Night Log will be containted.
        """
        for dir_ in [self.os_dir, self.dqs_dir, self.other_dir, self.image_dir]:
            if not os.path.exists(dir_):
                os.makedirs(dir_)

        return print("Your obsday is {}".format(self.obsday))


    def check_exists(self):
        """ Checks that paths have been created and the night has been initiated.
        """
        if not os.path.exists(self.dqs_dir):
            return False
        else:
            #Get data from get_started_os and return that
            return True


    def get_timestamp(self,strtime):
        """ Generates time stamp for the entry.
        """
        time = self.write_time(strtime, kp_only=True)
        time = '{}{}'.format(time[0:2],time[3:])
        if int(time) < 1200 :
            if len(str(int(time) + 1200))==3:
                return "0"+str(int(time) + 1200)
            else:
                return str(int(time) + 1200)
        else :
            if len(str(int(time) - 1200))==3:
                return  "0"+str(int(time) - 1200)
            else:
                return  str(int(time) - 1200)

    def write_time(self, time_string, kp_only=False):
        print('write_time',time_string)
        try:
            t = datetime.strptime(time_string, "%Y%m%dT%H:%M")
            kp_time = datetime(t.year, t.month, t.day, t.hour, t.minute, tzinfo = self.kp_zone)
            utc_time = kp_time.astimezone(self.utc)
            if kp_only:
                tt = "{}:{}".format(str(kp_time.hour).zfill(2), str(kp_time.minute).zfill(2))
            else:
                tt = "{}:{} [{}:{}]".format(str(kp_time.hour).zfill(2), str(kp_time.minute).zfill(2), str(utc_time.hour).zfill(2), str(utc_time.minute).zfill(2))
            return tt
        except:
            return time_string

    def compile_entries(self, the_path, header, file_nl):
        if os.path.exists(the_path):
            if header is not None:
                file_nl.write(header)
            file_nl.write("\n")
            file_nl.write("\n")

            f =  open(the_path, "r") 
            for line in f:
                file_nl.write(line)
                file_nl.write("\n")

            f.close()

    def get_started_os(self,os_1_firstname,os_1_lastname,os_2_firstname,os_2_lastname,LO_firstname,LO_lastname,OA_firstname,OA_lastname,time_sunset,time_18_deg_twilight_ends,time_18_deg_twilight_starts,
                        time_sunrise,time_moonrise,time_moonset,illumination): #,weather_conditions
        """
            Operations Scientist lists the personal present, ephemerids and weather conditions at sunset.
        """

        meta_dict = {'os_1_first':os_1_firstname, 'os_1_last':os_1_lastname,'os_2_first':os_2_firstname, 'os_2_last':os_2_lastname,'os_lo_1':LO_firstname,'os_lo_last':LO_lastname,'os_oa_1':OA_firstname,'os_oa_last':OA_lastname,
                    'os_sunset':time_sunset,'os_end18':time_18_deg_twilight_ends,'os_start18':time_18_deg_twilight_starts,'os_sunrise':time_sunrise,
                    'os_moonrise':time_moonrise,'os_moonset':time_moonset,'os_illumination':illumination,'dqs_1':None,'dqs_last':None}

        with open(self.meta_json,'w') as fp:
            json.dump(meta_dict, fp)


    def add_dqs_observer(self, dqs_firstname, dqs_lastname):
        with open(self.meta_json, 'r') as f:
            meta_dict = json.load(f)
            meta_dict['dqs_1'] = dqs_firstname
            meta_dict['dqs_last'] = dqs_lastname
        os.remove(self.meta_json)
        with open(self.meta_json, 'w') as f:
            json.dump(meta_dict, f)

        self.write_intro()

    def get_meta_data(self):
        meta_dict = json.load(open(self.meta_json,'r'))
        return meta_dict

    def write_checklist(self, data, user):
        check_cols = ['Time','Comment']
        if user == 'OS':
            the_path = self.os_cl
        elif user == 'DQS':
            the_path = self.dqs_cl

        df = self.write_pkl(data, check_cols, the_path)

        if user == 'OS':
            the_path = self.os_cl_file
        elif user == 'DQS':
            the_path = self.dqs_cl_file

        file = open(the_path,'a')
        if not os.path.exists(the_path):
            file.write("{} checklist completed at (Local time):".format(user))
            file.write("\n\n")
        for index, row in df.iterrows():
            file.write("* {} - {}".format(self.write_time(row['Time'], kp_only=True), row['Comment']))
            file.write("\n")
            file.write("\n")
        file.close()


    def write_plan(self, data):
        objectives = ['Time', 'Objective']
        df = self.write_pkl(data, objectives, self.objectives)

        file = open(self.objectives_file, 'w')
        for index, row in df.iterrows():
            file.write("* [{}] {}".format(index, row['Objective']))
            file.write("\n\n")
        file.close()

    def write_milestone(self, data):
        milestones = ['Time','Desc','Exp_Start','Exp_Stop','Exp_Excl']
        df = self.write_pkl(data, milestones, self.milestone)

        file = open(self.milestone_file,'w')
        for index, row in df.iterrows():
            file.write("* [{}] {}".format(index, row['Desc']))
            if row['Exp_Start'] not in [None, 'None', " ", ""]:
                file.write("; Exposure(s): {}".format(row['Exp_Start']))
            if row['Exp_Stop'] not in [None, 'None', " ", ""]:   
                file.write(" - {}".format(row['Exp_Stop']))
            if row['Exp_Excl'] not in [None, 'None', " ", ""]:   
                file.write(", excluding {}".format(row['Exp_Excl']))
            file.write("\n")
        file.close()


    def write_weather(self, data):
        """Operations Scientist adds information regarding the weather.
        """
        obs_cols = ['Time','desc','temp','wind','humidity','seeing','tput','skylevel']
        df = self.write_pkl(data, obs_cols, self.weather)

        file = open(self.weather_file,'w')
        for index, row in df.iterrows():
            file.write("- {} := {}".format(self.write_time(row['Time']), row['desc']))
            file.write(f"; Temp: {row['temp']}, Wind Speed: {row['wind']}, Humidity: {row['humidity']}")
            file.write(f", Seeing: {row['seeing']}, Tput: {row['tput']}, Sky: {row['skylevel']}")
            file.write("\n")
        file.close()

    def write_pkl(self, data, cols, filen):
        # order = time, index
        if not os.path.exists(filen):

            init_df = pd.DataFrame(columns=cols)
            init_df.to_pickle(filen)

        data = np.array(data)
        #data[np.where(data == None)] = 'None'

        df = pd.read_pickle(filen)
        data_df = pd.DataFrame([data], columns=cols)
        df = df.append(data_df)

        if self.replace:
            df = df.drop_duplicates(['Time'], keep='last')

        df = df.sort_values(by=['Time'])
        df.reset_index(inplace=True, drop=True)
        df.to_pickle(filen)
        return df

    def write_img(self, file, img_data, img_name):
        if img_name is not None and img_data is not None:
            # if img_filen is a bytearray we have received an image in base64 string (from local upload)
            # images are stored in the images directory
            if isinstance(img_data, bytes):
                self._upload_and_save_image(img_data, img_name)
                self._write_image_tag(file, img_name)
            else:
                print('ERROR: invalid format for uploading image')

    def add_problem(self, data, user):
        """
            Adds details on a problem encountered.
        """
        prob_cols = ['Time', 'Problem', 'alarm_id', 'action', 'name']

        if user == 'Other':
            file = self.other_pb
        elif user == 'OS':
            file = self.os_pb
        elif user == 'DQS':
            file = self.dqs_pb

        df = self.write_pkl(data, prob_cols, file)
        return df

    def write_problem(self, data, user, img_name = None, img_data = None):
        df = self.add_problem(data, user)
        if user == 'OS':
            filen = self.os_pb_file
        if user == 'DQS':
            filen = self.dqs_pb_file
        if user == 'Other':
            filen = self.other_pb_file

        file = open(filen, 'w')
        for index, row in df.iterrows():  
            file.write("- {} := ".format(self.write_time(row['Time'])))
            if user == 'DQS':
                file.write('*')
            if user == 'Other':
                file.write('_')
            if row['Problem'] not in [None, 'None', " ", ""]:
                file.write("{}".format(row['Problem']))
            if row['alarm_id'] not in [None, 'None', " ", ""]:
                file.write('; AlarmID: {}'.format(row['alarm_id']))
            if row['action'] not in [None, 'None', " ", ""]:
                file.write('; Action: {}'.format(row['action']))
            if user == 'DQS':
                file.write('*')
            if user == 'Other':
                file.write('_')
            file.write('\n')

        self.write_img(file, img_data, img_name)
        file.close()

    def add_comment_other(self, time, comment, name):
        the_path = os.path.join(self.other_obs_dir,"comment_{}".format(self.get_timestamp(time)))
        file = self.new_entry_or_replace(the_path)
        file.write("- {} := _{}({})_\n".format(self.write_time(time), comment, name))
        file.close()

    def write_dqs_exp(self, data, img_name = None, img_data = None):
        exp_columns = ['Time','Exp_Start','Exp_Type','Quality','Comm','Obs_Comm','Inst_Comm','Exp_Last']
        df = self.write_pkl(data, exp_columns, self.dqs_exp)

        file = open(self.dqs_exp_file, 'w')
        for index, row in df.iterrows():
            if row['Exp_Last'] is not None:
                file.write("- {}:{} := Exp. # {} - {}, {}, {}, {}\n".format(row['Time'][0:2], row['Time'][3:], row['Exp_Start'], row['Exp_Last'], row['Exp_Type'],row['Quality'],row['Comm']))
            else:
                file.write("- {}:{} := Exp. # {}, {}, {}, {}\n".format(row['Time'][0:2], row['Time'][3:], row['Exp_Start'], row['Exp_Type'],row['Quality'],row['Comm']))
            if row['Obs_Comm'] not in [None, " ", ""]:
                file.write("*observing conditions:* {} \n".format(row['Obs_Comm']))
            if row['Inst_Comm'] not in [None, " ", ""]:
                file.write("*instrument performance:* {} \n".format(row['Inst_Comm']))

        self.write_img(file, img_data, img_name)
        file.close()


    def write_os_exp(self, data, img_name = None, img_data = None):
        
        if os.path.exists(self.explist_file):
            exp_df = pd.read_csv(self.explist_file)

        exp_columns = ['Time','Comment','Exp_Start','Exp_End']
        df = self.write_pkl(data, exp_columns, self.os_exp)
        file = open(self.os_exp_file,'w')
        for index, row in df.iterrows():
            file.write("- {} := {}".format(self.write_time(row['Time']), row['Comment']))
            if row['Exp_Start'] is not None:
                try:
                    this_exp = exp_df[exp_df.id == int(row['Exp_Start'])]
                    file.write("; Exp: {}, Tile: {}, Exptime: {}, Airmass: {}, Sequence: {}, Flavor: {}, Program: {}\n".format(this_exp['id'].values[0],
                           this_exp['tileid'].values[0],this_exp['exptime'].values[0],this_exp['airmass'].values[0],this_exp['sequence'].values[0],
                           this_exp['flavor'].values[0],this_exp['program'].values[0]))
                except:
                    if row['Exp_End'] is not None:
                        file.write("; Exps: {}-{}\n".format(row['Exp_Start'], row['Exp_End']))
                    else:
                        file.write("; Exp: {}\n".format(row['Exp_Start']))
            else:
                file.write("\n")

        self.write_img(file, img_data, img_name)
        file.close()

    def load_index(self, idx, page):
        if page == 'milestone':
            the_path = self.milestone
        if page == 'plan':
            the_path = self.objectives
        df = pd.read_pickle(the_path)
        item = df[df.index == int(idx)]
        if len(item) > 0:
            return True, item
        else:
            return False, item

    def load_timestamp(self, time, user, exp_type):
        if user == 'OS':
            _dir = self.os_dir
        elif user == 'DQS':
            _dir = self.dqs_dir
        elif user == 'Other':
            _dir == self.other_dir

        if exp_type == 'exposure':
            the_path = os.path.join(_dir, 'exposures.pkl')
        elif exp_type == 'problem':
            the_path = os.path.join(_dir, 'problems.pkl')

        df = pd.read_pickle(the_path)
        item = df[df.Time == time]

        if len(item) > 0:
            return True, item
        else:
            return False, item


    def _upload_and_save_image(self, img_data, img_name):
        import base64
        # create images directory if necessary
        if not os.path.exists(self.image_dir):
            os.makedirs(self.image_dir)
        img_file = os.path.join(self.image_dir, img_name)
        with open(img_file, "wb") as fh:
            fh.write(base64.decodebytes(img_data))

    def _write_image_tag(self, img_file, img_name, comments = None, width=400, height=400):
        # server should be made a class variable
        server = f'http://desi-www.kpno.noao.edu:8090/nightlogs/{self.obsday}/images'
        img_file.write("\n")
        #img_file.write("h5. %s\n" % img_name)
        img_file.write('<img src="%s/%s" width=%s height=%s alt="Uploaded image %s">\n' % (server,img_name,str(width),str(height),img_name))
        if isinstance(comments, str):
            img_file.write("<br>{}\n".format(comments))

    def upload_image_comments(self, img_data, time, comment, your_name, uploaded_file = None):
        # get the file for the Other Report
        the_path = os.path.join(self.other_obs_dir,"comment_{}".format(self.get_timestamp(time)))
        file = self.new_entry_or_replace(the_path)
        file.write("- {} := _{}({})_\n".format(self.write_time(time), comment, your_name))

        # if img_filen is a bytearray we have received an image in base64 string (from local upload)
        # images are stored in the images directory
        name = uploaded_file if uploaded_file is not None else 'uploaded_image.png'
        if isinstance(img_data, bytes):
            self._upload_and_save_image(img_data, name)
            self._write_image_tag(file, name, comment)
        else:
            print('ERROR: invalid format for uploading image')
        file.close()

    def upload_image(self, img_data, comment, uploaded_file = None):
        # if img_filen is a bytearray we have received an image in base64 string (from local upload)
        if isinstance(img_data, bytes):
            import base64
            # create images directory if necessary
            if not os.path.exists(self.image_dir):
                os.makedirs(self.image_dir)
            name = uploaded_file if uploaded_file is not None else 'uploaded_image.png'
            img_file = os.path.join(self.image_dir, name)
            with open(img_file, "wb") as fh:
                fh.write(base64.decodebytes(img_data))
            if os.path.exists(self.upload_image_file):
                file = open(self.upload_image_file, 'a')
            else:
                file = open(self.upload_image_file, 'w')
            self._write_image_tag(file, name, comment)
            file.close()
        else:
            print('ERROR: invalid format for uploading image')

    def add_image(self, img_filen, comment):
        if os.path.exists(self.image_file):
            file = open(self.image_file, 'a')
        else:
            file = open(self.image_file, 'w')
        file.write("\n")
        file.write('<img src="{}" style="width:300px;height:300px;">'.format(img_filen))
        file.write("\n")
        file.write("{}".format(comment))
        file.close()

    def add_contributer_list(self, contributers):
        file = open(self.contributer_file, 'w')
        file.write(contributers)
        file.write("\n")
        file.close()

    def add_summary(self, summary):
        if os.path.exists(self.summary_file):
            file = open(self.summary_file, 'a')
        else:
            file = open(self.summary_file, 'w')
        file.write(summary)
        file.write("\n")
        file.close()

    def write_intro(self):
        file_intro=open(os.path.join(self.root_dir,'header'),'w')

        meta_dict = json.load(open(self.meta_json,'r'))
        file_intro.write("*Observer (OS-1)*: {} {}\n".format(meta_dict['os_1_first'],meta_dict['os_1_last']))
        file_intro.write("*Observer (OS-2)*: {} {}\n".format(meta_dict['os_2_first'],meta_dict['os_2_last']))
        file_intro.write("*Observer (DQS)*: {} {}\n".format(meta_dict['dqs_1'],meta_dict['dqs_last']))
        file_intro.write("*Lead Observer*: {} {}\n".format(meta_dict['os_lo_1'],meta_dict['os_lo_last']))
        file_intro.write("*Telescope Operator*: {} {}\n".format(meta_dict['os_oa_1'],meta_dict['os_oa_last']))
        file_intro.write("*Ephemerides in local time [UTC]*:\n")
        file_intro.write("* sunset: {}\n".format(self.write_time(meta_dict['os_sunset'])))
        file_intro.write("* 18(o) twilight ends: {}\n".format(self.write_time(meta_dict['os_end18'])))
        file_intro.write("* 18(o) twilight starts: {}\n".format(self.write_time(meta_dict['os_start18'])))
        file_intro.write("* sunrise: {}\n".format(self.write_time(meta_dict['os_sunrise'])))
        file_intro.write("* moonrise: {}\n".format(self.write_time(meta_dict['os_moonrise'])))
        file_intro.write("* moonset: {}\n".format(self.write_time(meta_dict['os_moonset'])))
        file_intro.write("* illumination: {}\n".format(meta_dict['os_illumination']))
        #file_intro.write("* sunset weather: {} \n".format(meta_dict['os_weather_conditions']))

        file_intro.close()
        cmd = "pandoc --metadata pagetitle=header -s {} -f textile -t html -o {}".format(os.path.join(self.root_dir,'header'),os.path.join(self.root_dir,'header.html'))
        try:
            os.system(cmd)
        except Exception as e:
            print('Exception calling pandoc (header): %s' % str(e))

    def finish_the_night(self):
        """
            Merge together all the different files into one '.txt' file to copy past on the eLog.
        """
        file_nl=open(os.path.join(self.root_dir,'nightlog'),'w')

        #Write the meta_html here
        file_intro=open(os.path.join(self.root_dir,'header'),'r')

        #meta_dict = json.load(open(self.meta_json,'r'))
        lines = file_intro.readlines()
        for line in lines:
            file_nl.write(line)
        file_nl.write("\n")
        file_nl.write("\n")

        #Contributers
        self.compile_entries(self.contributer_file, "h3. Contributers\n", file_nl)

        #Night Summary
        self.compile_entries(self.summary_file, "h3. Night Summary\n", file_nl)

        #Plan for the night
        file_nl.write("h3. Plan for the night\n")
        file_nl.write("\n")
        file_nl.write("The detailed operations plan for today (obsday "+self.obsday+") can be found at https://desi.lbl.gov/trac/wiki/DESIOperations/ObservingPlans/OpsPlan"+self.obsday+".\n")
        file_nl.write("\n")
        file_nl.write("Main items are listed below:\n")
        self.compile_entries(self.objectives_file, None, file_nl)

        #Milestones/Accomplishments
        file_nl.write("\n")
        file_nl.write("\n")
        file_nl.write("h3. Milestones and Major Progress\n")
        file_nl.write("\n")
        file_nl.write("\n")
        self.compile_entries(self.milestone_file, None, file_nl)

        #Problems
        file_nl.write("\n")
        file_nl.write("\n")
        file_nl.write("h3. Problems and Operations Issues (local time [UTC])\n")
        file_nl.write("\n")
        file_nl.write("\n")
        file_nl.write("h5. [OS, *DQS*, _Other_] \n")
        self.compile_entries(self.os_pb_file, None, file_nl)
        self.compile_entries(self.dqs_pb_file, None, file_nl)
        self.compile_entries(self.other_pb_file, None, file_nl)

        #Checklists
        file_nl.write("\n")
        file_nl.write("\n")
        file_nl.write("h3. Checklists\n")
        file_nl.write("\n")
        file_nl.write("\n")
        self.compile_entries(self.os_cl_file, "h5. Observing Scientist", file_nl)
        self.compile_entries(self.dqs_cl_file, "h5. Data Quality Scientist", file_nl)

        #Weather
        self.compile_entries(self.weather_file, "h3. Observing Conditions\n", file_nl)
        file_nl.write("\n")
        file_nl.write("\n")


        #Nightly Progress
        file_nl.write("h3. Details on the Night Progress (local time [UTC])\n")
        file_nl.write("\n")
        file_nl.write("\n")
        self.compile_entries(self.os_exp_file, "h5. Progress/Exposures (OS))\n", file_nl)
        self.compile_entries(self.dqs_exp_file, "h5. Exposure Quality (DQS)\n", file_nl)

        #Images
        if os.path.exists(self.image_file):
            file_nl.write("h3. Images\n")
            file_nl.write("<br>")
            file_nl.write("<br>")
            f =  open(self.image_file, "r") 
            for line in f:
                file_nl.write(line)
                file_nl.write("<br>")
        # Uploaded images
        if os.path.exists(self.image_dir):
            if os.path.exists(self.upload_image_file):
                file_nl.write("h3. Uploaded Images\n")
                file_nl.write("\n")
                f =  open(self.upload_image_file, "r") 
                for line in f:
                    file_nl.write(line)
                    file_nl.write('\n')
                file_nl.write("<br> ------<br>\n")
            else:
                # this is the code if we want to scan the directory and use every png file
                # will possibly cause in duplication with the Other comments images
                # so it's disabled for now
                """
                server = "http://desi-www.kpno.noao.edu:8090/nightlogs/20210116/images"
                image_files = glob.glob("%s/*.png" % self.image_dir)
                image_files.sort(key=os.path.getmtime)
                if len(image_files) != 0:
                    file_nl.write("h3. Uploaded Images:\n")
                    file_nl.write("\n")
                    for img in image_files:
                        name = os.path.basename(img)
                        file_nl.write("<p><b>%s</b></p>" % name)
                        file_nl.write('<p><img src="%s/%s" alt="Uploaded image %s"></p>' % (server,name,name))
                        file_nl.write("<br>")
                    file_nl.write("<br>")
                """
                pass

        file_nl.close()
        cmd = "pandoc  --resource-path={} --metadata pagetitle=report -s {} -f textile -t html -o {}".format(self.root_dir,
                                                                                                             os.path.join(self.root_dir,'nightlog'),
                                                                                                             os.path.join(self.root_dir,'nightlog.html'))
        try:
            os.system(cmd)
        except Exception as e:
            print('Exception calling pandoc: %s' % str(e))

        #os.system("pandoc --self-contained --metadata pagetitle='report' -s {} -f textile -t html -o {}".format(self.image_dir, os.path.join(self.root_dir,'nightlog'),os.path.join(self.root_dir,'nightlog.html')))
    # merge together all the different files into one .txt file to copy past on the eLog
    # checkout the notebooks at https://github.com/desihub/desilo/tree/master/DESI_Night_Logs/ repository
