"""
Created on April 9, 2020

@author: Satya Gontcho A Gontcho
"""

import os
import glob
import numpy as np
import pandas as pd
import json
from datetime import datetime

from astropy.time import Time, TimezoneInfo
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
        self.root_dir="nightlogs/"+self.obsday+"/"
        self.os_dir="nightlogs/"+self.obsday+"/OperationsScientist/"
        self.dqs_dir="nightlogs/"+self.obsday+"/DataQualityAssessment/"
        self.os_startcal_dir=self.os_dir+'startup_calibrations_'
        self.os_obs_dir=self.os_dir+'observing_'
        self.dqs_exp_dir=self.dqs_dir+'exposure_'
        self.os_pb_dir=self.os_dir+'problem_'
        self.dqs_pb_dir=self.dqs_dir+'problem_'
        self.os_cl=self.os_dir+'checklist'
        self.dqs_cl=self.dqs_dir+'checklist'
        #self.exp_file_pkl = self.dqa_dir+'/exposures.pkl'
        #self.dqs_exp_file = self.dqa_dir+'/exposures'
        self.weather_file = self.os_dir+'/weather.csv'
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
        return print("Your obsday is "+self.obsday)


    def check_exists(self):

        if not os.path.exists(self.dqs_dir):
            return 'Night Log has not yet been initialized'
        else:
            #Get data from get_started_os and return that
            return 'Night Log has been initialized'


    def get_timestamp(self,strtime):
        """
            Generates time stamp for the entry.
        """
        time = self.write_time(strtime, kp_only=True)
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

    def write_time(self, utc_string, kp_only=False):
        try:
            t = datetime.strptime(utc_string, "%Y%m%dT%H:%M")
            utc_time = datetime(t.year, t.month, t.day, t.hour, t.minute, tzinfo = self.utc)
            kp_time = utc_time.astimezone(self.kp_zone)
            if kp_only:
                time_string = "{}{}".format(kp_time.hour, kp_time.minute)
                return time_string
            else:
                time_string = " - {}:{} ({}:{})".format(kp_time.hour, kp_time.minute, utc_time.hour, utc_time.minute)
                return time_string
        except:
            return utc_string


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
        entries=glob.glob(the_path+"*")
        if len(entries) > 0:
            for e in entries:
                tmp_obs_e=open(e,'r')
                file_nl.write(tmp_obs_e.read())
                tmp_obs_e.close()
            file_nl.write("\n")
            file_nl.write("\n")


    def get_started_os(self,your_firstname,your_lastname,LO_firstname,LO_lastname,OA_firstname,OA_lastname,time_sunset,time_18_deg_twilight_ends,time_18_deg_twilight_starts,
time_sunrise,time_moonrise,time_moonset,illumination,weather_conditions):
        """
            Operations Scientist lists the personal present, ephemerids and weather conditions at sunset.
        """

        meta_dict = {'os_1':your_firstname, 'os_last':your_lastname,'os_lo_1':LO_firstname,'os_lo_last':LO_lastname,'os_oa_1':OA_firstname,'os_oa_last':OA_lastname,
                    'os_sunset':time_sunset,'os_end18':time_18_deg_twilight_ends,'os_start18':time_18_deg_twilight_starts,'os_sunrise':time_sunrise,
                    'os_moonrise':time_moonrise,'os_moonset':time_moonset,'os_illumination':illumination,'os_weather_conditions':weather_conditions,'dqs_1':None,'dqs_last':None}

        with open(self.meta_json,'w') as fp:
            json.dump(meta_dict, fp)


    def add_dqs_observer(self,dqs_firstname, dqs_lastname):

        meta_dict = json.load(open(self.meta_json,'r'))
        meta_dict['dqs_1'] = dqs_firstname
        meta_dict['dqs_last'] = dqs_lastname
        json.dump(meta_dict,open('nightlog_meta.json','w'))


    def get_meta_data(self):
        meta_dict = json.load(open(self.meta_json,'r'))
        return meta_dict


    def add_plan_os(self):
        """
            Operations Scientist lists the objectives for the night.
        """

    def add_weather_os(self, data):
        """Operations Scientist adds information regarding the weather.
        """
        data.to_csv(self.weather_file)



    def supcal_add_com_os(self,time,remark):
        """
            Operations Scientist comment/remark on Start Up & Calibrations procedures.
        """

        the_path=self.os_startcal_dir+self.get_timestamp(time_start)
        file=self.new_entry_or_replace(the_path)
        file.write(self.write_time(time)+" := "+remark+"\n")
        file.close()

    def supcal_add_seq_os(self,time,exp_num,exp_type,comment):
        """
            Operations Scientist adds new sequence in Start Up & Calibrations.
        """

        the_path=self.os_startcal_dir+self.get_timestamp(time_start)
        file=self.new_entry_or_replace(the_path)
        file.write(self.write_time(time)+" := exposure "+exp_num+", "+exp_type+", "+comment+"\n")
        file.close()

    def supcal_add_spec_script_os(self,time_start,exp_first,script,time_stop,exp_last,comment):
        """
            Operations Scientist adds new script (spectrograph cals) in Start Up & Calibrations.
        """

        the_path=self.os_startcal_dir+self.get_timestamp(time_start)
        file=self.new_entry_or_replace(the_path)
        if (time_stop == "") or (time_stop == " ") :
            file.write(self.write_time(time)+" := script @"+script+"@, first exposure "+exp_first+", last exposure "+exp_last+", "+comments+"\n")
        else:
            file.write(self.write_time(time)+" := script @"+script+"@, first exposure "+exp_first+"\n")
            file.write(self.write_time(time)+" := last exposure "+exp_last+", "+comment+"\n")
        file.close()

    def supcal_add_focus_script_os(self,time_start,exp_first,script,time_stop,exp_last,comment,trim):
        """
            Operations Scientist adds new script (focus) in Start Up & Calibrations.
        """

        the_path=self.os_startcal_dir+self.get_timestamp(time_start)
        file=self.new_entry_or_replace(the_path)
        if (time_stop == "") or (time_stop == " ") :
            file.write(self.write_time(time)+" := script @"+script+"@, first exposure "+exp_first+", last exposure "+exp_last+", trim = "+trim+", "+comments+"\n")
        else:
            file.write(self.write_time(time)+" := script @"+script+"@, first exposure "+exp_first+"\n")
            file.write(self.write_time(time)+" := last exposure "+exp_last+", "+comment+"\n")
        file.close()

    def obs_new_item_os(self,time,header):
        """
            Operations Scientist adds new item on the Observing section.
        """

        the_path=self.os_obs_dir+self.get_timestamp(time)
        file=self.new_entry_or_replace(the_path)
        file.write("h5. "+header+"\n")
        file.write("\n")
        file.close()

    def obs_add_seq_os(self,time,exp_num,exp_type,tile_number,tile_type,comment):
        """
            Operations Scientist adds new sequence in Observing.
        """

        the_path=self.os_obs_dir+self.get_timestamp(time)
        file=self.new_entry_or_replace(the_path)

        if (tile_number == "") or (tile_number == " ") :
            file.write(self.write_time(time)+" := exposure "+exp_num+", "+exp_type+" sequence, "+comment+"\n")
        else :
            file.write(self.write_time(time)+" := exposure "+exp_num+", "+exp_type+" sequence, "+tile_type+" tile "+tile_number+", "+comment+"\n")
        file.close()

    def obs_add_com_os(self,time,remark):
        """
            Operations Scientist comment/remark in the Observing section.
        """

        the_path=self.os_obs_dir+self.get_timestamp(time)
        file=self.new_entry_or_replace(the_path)
        file.write(self.write_time(time)+" := "+remark+"\n")
        file.close()

    def obs_add_script_os(self,time_start,exp_first,script,time_stop,exp_last,comment):
        """
            Operations Scientist adds new script in the Observing section.
        """

        the_path=self.os_obs_dir+self.get_timestamp(time_start)
        file=self.new_entry_or_replace(the_path)
        if (time_stop == "") or (time_stop == " ") :
            file.write(self.write_time(time)+" := script @"+script+"@, first exposure "+exp_first+", last exposure "+exp_last+", trim = "+trim+", "+comments+"\n")
        else:
            file.write(self.write_time(time)+" := script @"+script+"@, first exposure "+exp_first+"\n")
            file.write(self.write_time(time)+" := last exposure "+exp_last+", "+comment+"\n")
        file.close()

    def add_to_checklist(self,time,user):
        if user == 'OS':
            the_path = self.os_cl
        elif user == 'DQS':
            the_path = self.dqs_cl

        if not os.path.exists(the_path):
            file = open(the_path,'a')
            file.write("{} checklist completed at (Local time): {}".format(user, self.write_time(time, kp_only=True)))
            file.close()
        else:
            file = open(the_path,'a')
            file.write(", "+self.write_time(time, kp_only=True))
            file.close()

    def add_problem(self,time,problem,user):
        """
            Adds details on a problem encountered.
        """
        if user == 'OS':
            the_path=self.os_pb_dir+self.get_timestamp(time)
        elif user == 'DQS':
            the_path=self.dqs_pb_dir+self.get_timestamp(time)

        file=self.new_entry_or_replace(the_path)
        file.write(self.write_time(time)+" := "+problem+"\n")
        file.close()

    def add_exp_dqs(self,time,remark):
        """
            Data Quality Scientist adds assessement of a given exposure processed by NightWatch.
        """

        the_path=self.os_startcal_dir+self.get_timestamp(time_start)
        file=self.new_entry_or_replace(the_path)
        file.write(self.write_time(time)+" := "+remark+"\n")
        file.close()



    # def add_exposure(self, data):
    #
    #     self.exp_columns = ['Time','Exp_Start','Exp_Type','Quality','Comm','Obs_Comm','Inst_Comm','Exp_Last']
    #     if not os.path.exists(self.exp_file_pkl):
    #         init_df = pd.DataFrame(columns=self.exp_columns)
    #         init_df.to_pickle(self.exp_file_pkl)
    #
    #     df = pd.read_pickle(self.exp_file_pkl)
    #     data_df = pd.DataFrame([data], columns=self.exp_columns)
    #     df = df.append(data_df)
    #
    #     df = df.drop_duplicates(['Time'],keep='last')
    #     df = df.sort_values(by=['Time'])
    #     df.to_pickle(self.exp_file_pkl)
    #     return df
    #
    #
    # def dqs_add_exp(self,time_start, exp_start, exp_type, quality, comment, obs_cond_comm = None, inst_perf_comm = None, exp_last = None):
    #
    #     data = [time_start, exp_start, exp_type, quality, comment, obs_cond_comm, inst_perf_comm, exp_last]
    #     df = self.add_exposure(data)
    #     print(df.head())
    #
    #     file = open(self.dqs_exp_file,'w')
    #     file.write("h3. DQA Exposures \n")
    #     file.write("\n")
    #     for index, row in df.iterrows():
    #
    #         if row['Exp_Last'] is not None:
    #             file.write("- {}:{} := Exp. # {} - {}, {}, {}, {}\n".format(row['Time'][0:2], row['Time'][2:4], row['Exp_Start'], row['Exp_Last'], row['Exp_Type'],row['Quality'],row['Comm']))
    #         else:
    #             file.write("- {}:{} := Exp. # {}, {}, {}, {}\n".format(row['Time'][0:2], row['Time'][2:4], row['Exp_Start'], row['Exp_Type'],row['Quality'],row['Comm']))
    #         if row['Obs_Comm'] not in [None, " ", ""]:
    #             file.write("*observing conditions:* {} \n".format(row['Obs_Comm']))
    #         if row['Inst_Comm'] not in [None, " ", ""]:
    #             file.write("*instrument performance:* {} \n".format(row['Inst_Comm']))
    #     file.closed


    def finish_the_night(self):
        """
            Merge together all the different files into one '.txt' file to copy past on the eLog.
            (we'll want to add UTC times as well)

        """

        file_nl=open(self.root_dir+'nightlog','w')
        meta_dict = json.load(open(self.meta_json,'r'))
        file_nl.write("*Observer (OS)*: {} {}\n".format(meta_dict['os_1'],meta_dict['os_last']))
        file_nl.write("*Observer (DQS)*: {} {}\n".format(meta_dict['dqs_1'],meta_dict['dqs_last'])) # DQS
        file_nl.write("*Lead Observer*: {} {}\n".format(meta_dict['os_lo_1'],meta_dict['os_lo_last']))
        file_nl.write("*Telescope Operator*: {} {}\n".format(meta_dict['os_oa_1'],meta_dict['os_oa_last']))
        file_nl.write("*Ephemerides in local time*:\n")
        file_nl.write("* sunset: {}\n".format(self.write_time(meta_dict['os_sunset'])))
        file_nl.write("* 18(o) twilight ends: {}\n".format(self.write_time(meta_dict['os_end18'])))
        file_nl.write("* 18(o) twilight starts: {}\n".format(self.write_time(meta_dict['os_start18'])))
        file_nl.write("* sunrise: {}\n".format(self.write_time(meta_dict['os_sunrise'])))
        file_nl.write("* moonrise: {}\n".format(self.write_time(meta_dict['os_moonrise'])))
        file_nl.write("* moonset: {}\n".format(self.write_time(meta_dict['os_moonset'])))
        file_nl.write("* illumination: {}\n".format(meta_dict['os_illumination']))
        file_nl.write("* sunset weather: {} \n".format(meta_dict['os_weather_conditions']))
        file_nl.write("\n")
        file_nl.write("\n")
        file_nl.write("h3. Plans for the night\n")
        file_nl.write("\n")
        #file_nl.write()#add night plan here
        file_nl.write("\n")
        file_nl.write("\n")
        file_nl.write("h3. Problems and Operations Issues\n")
        file_nl.write("\n")
        file_nl.write("h5. Encountered by the OS\n")
        file_nl.write("\n")
        file_nl.write("\n")
        self.compile_entries(self.os_pb_dir,file_nl)
        file_nl.write("h5. Encountered by the DQS\n")
        file_nl.write("\n")
        file_nl.write("\n")
        self.compile_entries(self.dqs_pb_dir,file_nl)
        file_nl.write("h5. Checklists\n")
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
                    file_nl.write("- {}:{} := {}; Temp: {}, Wind: {}, Humidity: {}\n".format(row['time'][0:2],row['time'][3:],row['desc'],str(row['temp']),str(row['wind']),row['humidity']))
        file_nl.write("\n")
        file_nl.write("\n")
        file_nl.write("h3. Details on the night progress from the OS (local time)\n")
        file_nl.write("\n")
        file_nl.write("\n")
        self.compile_entries(self.os_startcal_dir,file_nl)
        self.compile_entries(self.os_obs_dir,file_nl)
        file_nl.write("h3. Details on the night progress from the DQS (local time)\n")
        file_nl.write("\n")
        file_nl.write("\n")
        self.compile_entries(self.dqs_exp_dir,file_nl)
        file_nl.close()
        os.system("pandoc -s {} -f textile -t html -o {}".format(self.root_dir+'nightlog',self.root_dir+'nightlog.html'))
    # merge together all the different files into one .txt file to copy past on the eLog
    # checkout the notebooks at https://github.com/desihub/desilo/tree/master/DESI_Night_Logs/ repository
