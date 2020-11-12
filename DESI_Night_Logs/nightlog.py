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
        self.obsday=year+month+day
        self.root_dir=os.environ['NL_DIR']+'/'+self.obsday+"/"
        self.os_dir=self.root_dir+"OperationsScientist/"
        self.dqs_dir=self.root_dir+"DataQualityAssessment/"
        self.os_startcal_dir=self.os_dir+'StartCal/'
        self.os_obs_dir=self.os_dir+'Observations/'
        #self.dqs_exp_dir=self.dqs_dir+'Exposures/'
        self.os_pb_dir=self.os_dir+'Problem/'
        self.dqs_pb_dir=self.dqs_dir+'Problem/'
        self.nightplan_file = self.os_dir + 'objectives.pkl'
        self.milestone_file = self.os_dir + 'milestones.pkl'
        self.os_cl=self.os_dir+'checklist'
        self.dqs_cl=self.dqs_dir+'checklist'
        self.exp_file_pkl = self.dqs_dir+'exposures.pkl'
        self.dqs_exp_file = self.dqs_dir+'exposures'
        self.weather_file = self.os_dir+'weather.csv'
        self.meta_json = self.root_dir+'nightlog_meta.json'

        # Set this if you want to allow for replacing lines or not
        self.replace = True

        self.utc = TimezoneInfo()
        self.kp_zone = TimezoneInfo(utc_offset=-7*u.hour)


    def initializing(self):
        """
            Creates the folders where all the files used to create the Night Log will be containted.
        """

        if not os.path.exists(self.os_dir):
            os.makedirs(self.os_dir)
        if not os.path.exists(self.dqs_dir):
            os.makedirs(self.dqs_dir)
        if not os.path.exists(self.os_pb_dir):
            os.makedirs(self.os_pb_dir)
        if not os.path.exists(self.dqs_pb_dir):
            os.makedirs(self.dqs_pb_dir)
        if not os.path.exists(self.os_startcal_dir):
            os.makedirs(self.os_startcal_dir)
        if not os.path.exists(self.os_obs_dir):
            os.makedirs(self.os_obs_dir)
        #if not os.path.exists(self.dqs_exp_dir):
        #    os.makedirs(self.dqs_exp_dir)
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
        else:
            return open(the_path,'a')


    def compile_entries(self,the_path,file_nl):
        if not os.path.exists(the_path):
            file_nl.write("\n")
        else :
            entries=sorted(glob.glob(the_path+"*"))
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
                    'os_moonrise':time_moonrise,'os_moonset':time_moonset,'os_illumination':illumination,'dqs_1':None,'dqs_last':None}#'os_weather_conditions':weather_conditions,

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
        objectives = ['Order','Objective']
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



    def supcal_add_com_os(self,time,remark):
        """
            Operations Scientist comment/remark on Start Up & Calibrations procedures.
        """

        the_path=self.os_startcal_dir+"startup_calibrations_"+self.get_timestamp(time)
        file=self.new_entry_or_replace(the_path)
        file.write("- "+self.write_time(time)+" := "+remark+"\n")
        file.close()

    def supcal_add_seq_os(self,time,exp_num,exp_type,comment):
        """
            Operations Scientist adds new sequence in Start Up & Calibrations.
        """

        the_path=self.os_startcal_dir+"startup_calibrations_"+self.get_timestamp(time)
        file=self.new_entry_or_replace(the_path)
        file.write("- "+self.write_time(time)+" := exposure "+exp_num+", "+exp_type+", "+comment+"\n")
        file.close()

    def supcal_add_spec_script_os(self,time_start,exp_first,script,time_stop,exp_last,comment):
        """
            Operations Scientist adds new script (spectrograph cals) in Start Up & Calibrations.
        """

        the_path=self.os_startcal_dir+"startup_calibrations_"+self.get_timestamp(time_start)
        file=self.new_entry_or_replace(the_path)
        if time_stop in [None, "", " "]:
            file.write("- "+self.write_time(time_start)+" := script @"+script+"@, first exposure "+exp_first+", last exposure "+exp_last+", "+comment+"\n")
        else:
            file.write("- "+self.write_time(time_start)+" := script @"+script+"@, first exposure "+exp_first+"\n")
            file.write("- "+self.write_time(time_stop)+" := last exposure "+exp_last+", "+comment+"\n")
        file.close()

    def supcal_add_focus_script_os(self,time_start,exp_first,script,time_stop,exp_last,comment,trim):
        """
            Operations Scientist adds new script (focus) in Start Up & Calibrations.
        """

        the_path=self.os_startcal_dir+"startup_calibrations_"+self.get_timestamp(time_start)
        file=self.new_entry_or_replace(the_path)
        if time_stop in [None, "", " "]:
            file.write("- "+self.write_time(time_start)+" := script @"+script+"@, first exposure "+exp_first+", last exposure "+exp_last+", trim = "+trim+", "+comment+"\n")
        else:
            file.write("- "+self.write_time(time_start)+" := script @"+script+"@, first exposure "+exp_first+"\n")
            file.write("- "+self.write_time(time_stop)+" := last exposure "+exp_last+", "+comment+"\n")
        file.close()

    def obs_new_item_os(self,time,header):
        """
            Operations Scientist adds new item on the Observing section.
        """

        the_path=self.os_obs_dir+"observing_"+self.get_timestamp(time)
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
        hdr_type, exp_time, exp_comment, exp_exposure_start, exp_exposure_finish, exp_type, exp_script, exp_time_end, exp_focus_trim, exp_tile, exp_tile_type = data_list
        if hdr_type == 'Focus':
            self.supcal_add_focus_script_os(exp_time,exp_exposure_start,exp_script,exp_time_end,exp_exposure_finish,exp_comment,exp_focus_trim)
        elif hdr_type == 'Startup':
            self.supcal_add_com_os(exp_time,exp_comment)
        elif hdr_type == 'Calibration':
            if exp_script not in [None, 'None'," ", ""]:
                self.supcal_add_spec_script_os(exp_time,exp_exposure_start,exp_script,exp_time_end,exp_exposure_finish,exp_comment)
            else:
                self.supcal_add_seq_os(exp_time,exp_exposure_start,exp_type,exp_comment)
        elif (hdr_type == 'Observation') | (hdr_type == 'Other'):
            if exp_script not in [None,'None', " ", ""]:
                self.obs_add_script_os(exp_time,exp_exposure_start,exp_script,exp_time_end,exp_exposure_finish,exp_comment)
            else:
                if exp_exposure_start not in [None,'None', " ", ""]:
                    self.obs_add_seq_os(exp_time, exp_tile, exp_type, exp_exposure_start, exp_type, exp_comment)
                else:
                    self.obs_add_com_os(exp_time,exp_comment)


    def obs_add_seq_os(self,time, tile_number, tile_type, exp_num, exp_type, comment):
        """
            NEED TO UPDATE THIS
        """

        the_path=self.os_obs_dir+"observing_"+self.get_timestamp(time)
        file=self.new_entry_or_replace(the_path)

        if tile_number in [None, "", " "]:
            file.write("- "+self.write_time(time)+" := exposure "+exp_num+", "+exp_type+" sequence, "+comment+"\n")
        else :
            file.write("- "+self.write_time(time)+" := exposure "+exp_num+", "+exp_type+" sequence, "+tile_type+" tile "+tile_number+", "+comment+"\n")
        file.close()

    def obs_add_com_os(self,time,remark):
        """
            Operations Scientist comment/remark in the Observing section.
        """

        the_path=self.os_obs_dir+"observing_"+self.get_timestamp(time)
        file=self.new_entry_or_replace(the_path)
        file.write("- "+self.write_time(time)+" := "+remark+"\n")
        file.close()

    def obs_add_script_os(self,time_start,exp_first,script,time_stop,exp_last,comment):
        """
            Operations Scientist adds new script in the Observing section.
        """

        the_path=self.os_obs_dir+"observing_"+self.get_timestamp(time_start)
        file=self.new_entry_or_replace(the_path)
        if (time_stop == "") or (time_stop == " ") :
            file.write("- "+self.write_time(time_start)+" := script @"+script+"@, first exposure "+exp_first+", last exposure "+exp_last+", trim = "+trim+", "+comment+"\n")
        else:
            file.write("- "+self.write_time(time_start)+" := script @"+script+"@, first exposure "+exp_first+"\n")
            file.write("- "+self.write_time(time_stop)+" := last exposure "+exp_last+", "+comment+"\n")
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

    def add_problem(self,time,problem,alarm_id,action,user):
        """
            Adds details on a problem encountered.
        """
        if user == 'Other':
            pass
        else:
            if user == 'OS':
                the_path=self.os_pb_dir+"problem_"+self.get_timestamp(time)
            elif user == 'DQS':
                the_path=self.dqs_pb_dir+"problem_"+self.get_timestamp(time)
            file=self.new_entry_or_replace(the_path)

            file.write("- "+self.write_time(time)+" := "+str(problem)+";  AlarmID: "+str(alarm_id)+";  Action: "+str(action)+"\n")
            file.close()

    # def add_exp_dqs(self,data_list):
    #     """
    #         Data Quality Scientist adds assessement of a given exposure processed by NightWatch.
    #     """
    #     exp_time, exp_exposure_start, exp_type, quality, exp_comment, obs_cond_comment, inst_perf_comment, exp_exposure_finish = data_list
    #     the_path=self.dqs_dir+self.get_timestamp(time_start)
    #     file=self.new_entry_or_replace(the_path)
    #     file.write(self.write_time(time)+" := "+remark+"\n")
    #     file.close()

    def add_comment_other(self, time, comment, name):
        ## Not sure how we want to implement this currently
        pass

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

    def write_intro(self):
        file_intro=open(self.root_dir+'header','w')

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
        os.system("pandoc -s {} -f textile -t html -o {}".format(self.root_dir+'header',self.root_dir+'header.html'))

    def finish_the_night(self):
        """
            Merge together all the different files into one '.txt' file to copy past on the eLog.
        """

        file_nl=open(self.root_dir+'nightlog','w')
        
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
        #self.compile_entries(self.dqs_exp_dir,file_nl)
        file_nl.close()
        os.system("pandoc -s {} -f textile -t html -o {}".format(self.root_dir+'nightlog',self.root_dir+'nightlog.html'))
    # merge together all the different files into one .txt file to copy past on the eLog
    # checkout the notebooks at https://github.com/desihub/desilo/tree/master/DESI_Night_Logs/ repository
