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
        self.os_startcal_dir = os.path.join(self.os_dir,'StartCal')
        self.os_obs_dir = os.path.join(self.os_dir,'Observations')
        self.other_obs_dir = os.path.join(self.other_dir,'Observations')
        #self.dqs_exp_dir=self.dqs_dir+'Exposures/'
        self.os_pb_dir = os.path.join(self.os_dir,'Problem')
        self.dqs_pb_dir = os.path.join(self.dqs_dir,'Problem')
        self.other_pb_dir = os.path.join(self.other_dir,'Problem')
        self.nightplan_file = os.path.join(self.os_dir,'objectives.pkl')
        self.milestone_file = os.path.join(self.os_dir,'milestones.pkl')
        self.os_cl = os.path.join(self.os_dir,'checklist')
        self.dqs_cl = os.path.join(self.dqs_dir,'checklist')
        self.exp_file_pkl = os.path.join(self.dqs_dir,'exposures.pkl')
        self.dqs_exp_file = os.path.join(self.dqs_dir,'exposures')
        self.weather_file = os.path.join(self.os_dir,'weather.csv')
        self.meta_json = os.path.join(self.root_dir,'nightlog_meta.json')
        self.image_file = os.path.join(self.image_dir, 'image_list')
        self.contributer_file = os.path.join(self.root_dir, 'contributer_file')
        self.explist_file = os.path.join(self.root_dir, 'exposures.csv')

        # Set this if you want to allow for replacing lines or not
        self.replace = True

        self.utc = TimezoneInfo()
        self.kp_zone = TimezoneInfo(utc_offset=-7*u.hour)


    def initializing(self):
        """
            Creates the folders where all the files used to create the Night Log will be containted.
        """
        for dir_ in [self.os_dir, self.dqs_dir, self.other_dir, self.os_pb_dir, self.dqs_pb_dir, 
                    self.os_startcal_dir,self.other_pb_dir, self.os_obs_dir, self.other_obs_dir, self.image_dir]:
            if not os.path.exists(dir_):
                os.makedirs(dir_)

        return print("Your obsday is "+self.obsday)


    def check_exists(self):

        if not os.path.exists(self.dqs_dir):
            return False
        else:
            #Get data from get_started_os and return that
            return True


    def get_timestamp(self,strtime):
        """
            Generates time stamp for the entry.
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


    def new_entry_or_replace(self,the_path):
        """
            Check whether there is already an entry with the same time stamp, if so file gets replaced, otherwise this is a new entry.
        """

        if os.path.exists(the_path):
            os.remove(the_path)
        return open(the_path,'a')


    def compile_entries(self,the_path,file_nl):
        if not os.path.exists(the_path):
            file_nl.write("\n")
        else :
            entries=sorted(glob.glob(the_path+"/*"))
            if len(entries) > 0:
                for e in entries:
                    tmp_obs_e=open(e,'r')
                    file_nl.write(tmp_obs_e.read())
                    tmp_obs_e.close()
                    file_nl.write("\n")
                    file_nl.write("\n")


    def get_started_os(self,your_firstname,your_lastname,LO_firstname,LO_lastname,OA_firstname,OA_lastname,time_sunset,time_18_deg_twilight_ends,time_18_deg_twilight_starts,
                        time_sunrise,time_moonrise,time_moonset,illumination): #,weather_conditions
        """
            Operations Scientist lists the personal present, ephemerids and weather conditions at sunset.
        """

        meta_dict = {'os_1':your_firstname, 'os_last':your_lastname,'os_lo_1':LO_firstname,'os_lo_last':LO_lastname,'os_oa_1':OA_firstname,'os_oa_last':OA_lastname,
                    'os_sunset':time_sunset,'os_end18':time_18_deg_twilight_ends,'os_start18':time_18_deg_twilight_starts,'os_sunrise':time_sunrise,
                    'os_moonrise':time_moonrise,'os_moonset':time_moonset,'os_illumination':illumination,'dqs_1':None,'dqs_last':None}

        with open(self.meta_json,'w') as fp:
            json.dump(meta_dict, fp)


    def add_dqs_observer(self,dqs_firstname, dqs_lastname):
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

    def add_plan_os(self, data_list):
        """
            Operations Scientist lists the objectives for the night.
        """
        objectives = ['Order', 'Objective']
        if not os.path.exists(self.nightplan_file):
            df = pd.DataFrame(columns=objectives)
            df.to_pickle(self.nightplan_file)
        df = pd.read_pickle(self.nightplan_file)
        data_df = pd.DataFrame([data_list], columns=objectives)

        df = df.append(data_df)
        df.to_pickle(self.nightplan_file)

    def add_milestone_os(self, data_list):
        milestones = ['Desc','Exp_Start','Exp_Stop','Exp_Excl']
        if not os.path.exists(self.milestone_file):
            df = pd.DataFrame(columns=milestones)
            df.to_pickle(self.milestone_file)
        df = pd.read_pickle(self.milestone_file)
        data_df = pd.DataFrame([data_list], columns=milestones)

        df = df.append(data_df)
        df.to_pickle(self.milestone_file)


    def add_weather_os(self, data):
        """Operations Scientist adds information regarding the weather.
        """
        data.to_csv(self.weather_file)

    def obs_new_item_os(self,time,header):
        """
            Operations Scientist adds new item on the Observing section.
        """

        the_path=os.path.join(self.os_obs_dir,"observing_{}".format(self.get_timestamp(time)))
        file=self.new_entry_or_replace(the_path)
        file.write("h5. "+header+"\n")
        file.write("\n")
        file.close()

    def add_progress(self, data_list):
        """
        This function calls the correct functions in nightlog.py and provides an interface with the App
        """
        data_list = np.array(data_list)
        data_list[np.where(data_list == None)] = 'None'
        hdr_type, exp_time, comment, exp_start, exp_finish, exp_type, exp_script, exp_time_end, exp_focus_trim, exp_tile, exp_tile_type = data_list
        if hdr_type in ['Focus', 'Startup', 'Calibration']:
            the_path=os.path.join(self.os_startcal_dir,"startup_calibrations_{}".format(self.get_timestamp(exp_time)))

        elif hdr_type in ['Observation', 'Other Acquisition', 'Comment']:
            the_path=os.path.join(self.os_obs_dir,"observing_{}".format(self.get_timestamp(exp_time)))
        
        self.progress_sequence(the_path, exp_time, comment, exp_start, exp_finish, exp_type, exp_script, exp_time_end, exp_focus_trim, exp_tile, exp_tile_type)

    def progress_sequence(self, the_path, time, comment, exp_start, exp_finish, exp_type, exp_script, exp_time_end, exp_focus_trim, exp_tile, exp_tile_type):
        file=self.new_entry_or_replace(the_path)
        text = "- {} := ".format(self.write_time(time))
        if exp_script not in [None, 'None', " ", ""]:
            text += "script @{}@; ".format(exp_script)
        if exp_start not in [None, 'None', " ", ""]:
            text += 'exposure {}; '.format(exp_start)
        if exp_type not in [None, 'None', " ", ""]:
            text += '{} sequence; '.format(exp_type)
        if exp_tile_type not in [None, 'None', " ", ""]:
            text += '{}; '.format(exp_tile_type)
        if exp_tile not in [None, 'None', " ", ""]:
            text += 'tile {}; '.format(exp_tile)
        if exp_time_end not in [None, 'None', " ", ""]:
            text += '/n'
            text += "- {} := ".format(self.write_time(exp_time_end))
        if exp_finish not in [None, 'None', " ", ""]:
            text += 'last exp. {}; '.format(exp_finish)
        if exp_focus_trim not in [None, 'None', " ", ""]:
            text += 'trim {}; '.format(exp_focus_trim)
        if comment not in [None, 'None', " ", ""]:
            text += '{}'.format(comment)
        text += '\n'
        file.write(text)
        file.close()

    def add_to_checklist(self, time, comment, user):
        """
        Adds time that a checklist was completed. This cannot be edited.
        """
        if user == 'OS':
            the_path = self.os_cl
        elif user == 'DQS':
            the_path = self.dqs_cl

        if not os.path.exists(the_path):
            file = open(the_path,'a')
            file.write("{} checklist completed at (Local time): {} ({})".format(user, self.write_time(time, kp_only=True), comment))
            file.close()
        else:
            file = open(the_path,'a')
            file.write("; {} ({})".format(self.write_time(time, kp_only=True), comment))
            file.close()

    def prob_seq(self, time, problem, alarm_id, action):
        text = "- {} :=".format(self.write_time(time))
        if problem not in [None, 'None', " ", ""]:
            text += '{}'.format(problem)
        if alarm_id not in [None, 'None', " ", ""]:
            text += '; AlarmID: {}'.format(alarm_id)
        if action not in [None, 'None', " ", ""]:
            text += '; Action: {}'.format(action)
        return text

    def add_problem(self, time, problem, alarm_id, action, user, name=None):
        """
            Adds details on a problem encountered.
        """
        if user == 'Other':
            the_path = os.path.join(self.other_pb_dir,"problem_{}".format(self.get_timestamp(time)))
            file = self.new_entry_or_replace(the_path)
            text = self.prob_seq(time,problem,alarm_id,action) + ' ({})\n'.format(name)
            file.write(text)
            file.close()
        else:
            if user == 'OS':
                the_path=os.path.join(self.os_pb_dir,"problem_{}".format(self.get_timestamp(time)))
            elif user == 'DQS':
                the_path=os.path.join(self.dqs_pb_dir,"problem_{}".format(self.get_timestamp(time)))
            file=self.new_entry_or_replace(the_path)

            file.write(self.prob_seq(time,problem,alarm_id,action) + '\n')
            file.close()

    def add_comment_other(self, time, comment, name):
        the_path = os.path.join(self.other_obs_dir,"comment_{}".format(self.get_timestamp(time)))
        file = self.new_entry_or_replace(the_path)
        file.write("- {} := {}({})\n".format(self.write_time(time), comment, name))
        file.close()

    def add_dqs_exposure(self, data):

        self.exp_columns = ['Time','Exp_Start','Exp_Type','Quality','Comm','Obs_Comm','Inst_Comm','Exp_Last']
        if not os.path.exists(self.exp_file_pkl):
            init_df = pd.DataFrame(columns=self.exp_columns)
            init_df.to_pickle(self.exp_file_pkl)

        df = pd.read_pickle(self.exp_file_pkl)
        data_df = pd.DataFrame([data], columns=self.exp_columns)
        df = df.append(data_df)
        if self.replace:
            df = df.drop_duplicates(['Time'],keep='last')
        df = df.sort_values(by=['Time'])
        df.to_pickle(self.exp_file_pkl)
        return df


    def dqs_add_exp(self,data):

        df = self.add_dqs_exposure(data)

        file = open(self.dqs_exp_file,'w')
        for index, row in df.iterrows():

            if row['Exp_Last'] is not None:
                file.write("- {}:{} := Exp. # {} - {}, {}, {}, {}\n".format(row['Time'][0:2], row['Time'][2:4], row['Exp_Start'], row['Exp_Last'], row['Exp_Type'],row['Quality'],row['Comm']))
            else:
                file.write("- {}:{} := Exp. # {}, {}, {}, {}\n".format(row['Time'][0:2], row['Time'][2:4], row['Exp_Start'], row['Exp_Type'],row['Quality'],row['Comm']))
            if row['Obs_Comm'] not in [None, " ", ""]:
                file.write("*observing conditions:* {} \n".format(row['Obs_Comm']))
            if row['Inst_Comm'] not in [None, " ", ""]:
                file.write("*instrument performance:* {} \n".format(row['Inst_Comm']))
        file.close()

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

    def write_intro(self):
        file_intro=open(os.path.join(self.root_dir,'header'),'w')

        meta_dict = json.load(open(self.meta_json,'r'))
        file_intro.write("*Observer (OS)*: {} {}\n".format(meta_dict['os_1'],meta_dict['os_last']))
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
        os.system("pandoc -s {} -f textile -t html -o {}".format(os.path.join(self.root_dir,'header'),os.path.join(self.root_dir,'header.html')))

    def finish_the_night(self):
        """
            Merge together all the different files into one '.txt' file to copy past on the eLog.
        """

        file_nl=open(os.path.join(self.root_dir,'nightlog'),'w')

        meta_dict = json.load(open(self.meta_json,'r'))
        file_nl.write("*Observer (OS)*: {} {}\n".format(meta_dict['os_1'],meta_dict['os_last']))
        file_nl.write("*Observer (DQS)*: {} {}\n".format(meta_dict['dqs_1'],meta_dict['dqs_last']))
        file_nl.write("*Lead Observer*: {} {}\n".format(meta_dict['os_lo_1'],meta_dict['os_lo_last']))
        file_nl.write("*Telescope Operator*: {} {}\n".format(meta_dict['os_oa_1'],meta_dict['os_oa_last']))
        file_nl.write("*Ephemerides in local time [UTC]*:\n")
        file_nl.write("* sunset: {}\n".format(self.write_time(meta_dict['os_sunset'])))
        file_nl.write("* 18(o) twilight ends: {}\n".format(self.write_time(meta_dict['os_end18'])))
        file_nl.write("* 18(o) twilight starts: {}\n".format(self.write_time(meta_dict['os_start18'])))
        file_nl.write("* sunrise: {}\n".format(self.write_time(meta_dict['os_sunrise'])))
        file_nl.write("* moonrise: {}\n".format(self.write_time(meta_dict['os_moonrise'])))
        file_nl.write("* moonset: {}\n".format(self.write_time(meta_dict['os_moonset'])))
        file_nl.write("* illumination: {}\n".format(meta_dict['os_illumination']))
        #file_nl.write("* sunset weather: {} \n".format(meta_dict['os_weather_conditions']))
        file_nl.write("\n")
        file_nl.write("\n")
        if os.path.exists(self.contributer_file):
            file_nl.write("h3. Contributers\n")
            file_nl.write("\n")
            file_nl.write("\n")
            f =  open(self.contributer_file, "r") 
            for line in f:
                file_nl.write(line)
                file_nl.write("\n")
                file_nl.write("\n")
        file_nl.write("h3. Plan for the night\n")
        file_nl.write("\n")
        file_nl.write("The detailed operations plan for today (obsday "+self.obsday+") can be found at https://desi.lbl.gov/trac/wiki/DESIOperations/ObservingPlans/OpsPlan"+self.obsday+".\n")
        file_nl.write("\n")
        file_nl.write("Main items are listed below:\n")
        file_nl.write("\n")
        #self.compile_entries(self.os_dir+"nightplan_",file_nl)
        if os.path.exists(self.nightplan_file):
            m_entries = pd.read_pickle(self.nightplan_file)
            for idx, row in m_entries.iterrows():
                file_nl.write("* {}.\n".format(row['Objective']))
                file_nl.write("\n")
                file_nl.write("\n")
        else:
            file_nl.write("\n")
        file_nl.write("h3. Milestones and Major Progress")
        file_nl.write("\n")
        if os.path.exists(self.milestone_file):
            m_entries = pd.read_pickle(self.milestone_file)
            for idx, row in m_entries.iterrows():
                file_nl.write("* {}; Exposures: [{} - {}], excluding {}.\n".format(row['Desc'],row['Exp_Start'],row['Exp_Stop'],row['Exp_Excl']))
                file_nl.write("\n")
                file_nl.write("\n")
        else:
            file_nl.write("\n")
        file_nl.write("h3. Problems and Operations Issues (local time [UTC])\n")
        file_nl.write("\n")
        file_nl.write("h5. Encountered by the OS\n")
        file_nl.write("\n")
        file_nl.write("\n")
        self.compile_entries(self.os_pb_dir,file_nl)
        file_nl.write("h5. Encountered by the DQS\n")
        file_nl.write("\n")
        file_nl.write("\n")
        self.compile_entries(self.dqs_pb_dir,file_nl)
        file_nl.write("h5. Encountered by Others\n")
        file_nl.write("\n")
        file_nl.write("\n")
        self.compile_entries(self.other_pb_dir,file_nl)
        file_nl.write("h3. Checklists\n")
        file_nl.write("\n")
        if os.path.exists(self.os_cl):
            os_cl_entries=open(self.os_cl,'r')
            for x in os_cl_entries:
                file_nl.write(x)
            os_cl_entries.close()
        file_nl.write("\n")
        if os.path.exists(self.dqs_cl):
            dqs_cl_entries=open(self.dqs_cl,'r')
            for x in dqs_cl_entries:
                file_nl.write(x)
            dqs_cl_entries.close()
        file_nl.write("\n")
        file_nl.write("\n")
        file_nl.write("h3. Weather Summary\n")
        file_nl.write("\n")
        if os.path.exists(self.weather_file):
            data = pd.read_csv(self.weather_file)
            for index, row in data.iterrows():
                if isinstance(row['desc'], str):
                    file_nl.write("- {} := {}; Temp: {}, Wind: {}, Humidity: {}\n".format(str(row['time']),row['desc'],str(row['temp']),str(row['wind']),row['humidity']))
        file_nl.write("\n")
        file_nl.write("\n")
        file_nl.write("h3. Details on the night progress from the OS (local time [UTC])\n")
        file_nl.write("\n")
        file_nl.write("\n")
        file_nl.write("h5. Startup and Calibrations\n")
        file_nl.write("\n")
        file_nl.write("\n")
        self.compile_entries(self.os_startcal_dir,file_nl)
        file_nl.write("h5. Observations\n")
        file_nl.write("\n")
        file_nl.write("\n")
        self.compile_entries(self.os_obs_dir,file_nl)
        file_nl.write("h3. Details on the night progress from the DQS (local time [UTC])\n")
        file_nl.write("\n")
        file_nl.write("\n")
        if os.path.exists(self.dqs_exp_file):
            entries = open(self.dqs_exp_file,'r')
            for x in entries:
                file_nl.write(x)
        file_nl.write("h3. Details from Other Observers\n")
        file_nl.write("\n")
        file_nl.write("\n")
        self.compile_entries(self.other_obs_dir,file_nl)
        #self.compile_entries(self.dqs_exp_dir,file_nl)
        if os.path.exists(self.image_file):
            file_nl.write("h3. Images\n")
            file_nl.write("\n")
            file_nl.write("\n")
            f =  open(self.image_file, "r") 
            for line in f:
                file_nl.write(line)
                file_nl.write("\n")
                file_nl.write("\n")
        file_nl.close()
        os.system("pandoc --self-contained --metadata pagetitle='report' -s {} -f textile -t html -o {}".format(os.path.join(self.root_dir,'nightlog'),os.path.join(self.root_dir,'nightlog.html')))
    # merge together all the different files into one .txt file to copy past on the eLog
    # checkout the notebooks at https://github.com/desihub/desilo/tree/master/DESI_Night_Logs/ repository
