"""
Created on April 9, 2020

@author: Satya Gontcho A Gontcho
"""

import os
import glob
import pandas as pd
import json


class NightLog(object):
    """
        During a night of observing with the Dark Energy Spectroscopic Instrument (DESI),
        observers are required to provide a detailed account of the events of the night.
        This tool provides observers with an interface to write the nightlog in the proper formatting (textile for the eLog).
    """

    def __init__(self,year,month,day):
        """
            Setup the nightlog framework for a given obsday.
        """
        self.obsday=year+month+day
        self.root_dir="nightlogs/"+self.obsday+"/"
        self.os_dir="nightlogs/"+self.obsday+"/OperationsScientist/"
        self.qa_dir="nightlogs/"+self.obsday+"/DataQualityAssessment/"
        self.tmp_obs_dir=self.os_dir+'observing_'
        self.exp_file_pkl = self.qa_dir+'/exposures.pkl'
        self.dqs_exp_file = self.qa_dir+'/exposures'


    def initializing(self):
        """
            Creates the folders where all the .txt files used to create the Night Log will be containted.
        """
        
        if not os.path.exists(self.os_dir):
            os.makedirs(self.os_dir)
        if not os.path.exists(self.qa_dir):
            os.makedirs(self.qa_dir)
        return print("Your obsday is "+self.obsday)



    def check_exists(self):
        
        if not os.path.exists(self.qa_dir):
            return 'Night Log has not yet been initialized'
        else:
            #Get data from get_started_os and return that
            return 'Night Log has been initialized'


    def get_started_os(self,your_firstname,your_lastname,LO_firstname,LO_lastname,OA_firstname,OA_lastname,time_sunset,time_18_deg_twilight_ends,time_18_deg_twilight_starts,
        time_sunrise,time_moonrise,time_moonset,illumination,weather_conditions):
        """
            Operations Scientist lists the personal present, ephemerids and weather conditions at sunset.
        """
        meta_dict = {'os_1':your_firstname, 'os_last':your_lastname,'os_lo_1':LO_firstname,'os_lo_last':LO_lastname,'os_oa_1':OA_firstname,'os_oa_last':OA_lastname,
                    'os_sunset':time_sunset,'os_end18':time_18_deg_twilight_ends,'os_start18':time_18_deg_twilight_starts,'os_sunrise':time_sunrise,
                    'os_moonrise':time_moonrise,'os_moonset':time_moonset,'os_illumination':illumination,'os_weather_conditions':weather_conditions,'dqs_1':None,'dqs_last':None}

        with open('nightlog_meta.json','w') as fp:
            json.dump(meta_dict, fp)

    def add_dqs_observer(self,dqs_firstname, dqs_lastname):

        meta_dict = json.load(open('nightlog_meta.json','r'))
        meta_dict['dqs_1'] = dqs_firstname
        meta_dict['dqs_last'] = dqs_lastname
        json.dump(meta_dict,open('nightlog_meta.json','w'))
        #file = open(self.root_dir+'startup_section','a')
        #file.write("*Observers (DQS)*: {} {}\n".format(self.dqs_1,self.dqs_last))
        #file.closed


    def supcal_add_com_os(self,time,remark):
        """
            Operations Scientist comment/remark on Start Up & Calibrations procedures.
        """
        file = open(self.os_dir+'startup_calibrations','a')
        file.write("- "+time[0:2]+":"+time[2:4]+" := "+remark+"\n")
        file.close()

    def supcal_add_seq_os(self,time,exp_num,exp_type,comment):
        """
            Operations Scientist adds new sequence in Start Up & Calibrations.
        """
        file = open(self.os_dir+'startup_calibrations','a')
        file.write("- "+time[0:2]+":"+time[2:4]+" := exposure "+exp_num+", "+exp_type+", "+comment+"\n")
        file.close()

    def supcal_add_spec_script_os(self,time_start,exp_first,script,time_stop,exp_last,comment):
        """
            Operations Scientist adds new script (spectrograph) in Start Up & Calibrations.
        """
        file = open(self.os_dir+'startup_calibrations','a')
        if (time_stop == "") or (time_stop == " ") :
            file.write("- "+time_start[0:2]+":"+time_start[2:4]+" := script @"+script+"@, first exposure "+exp_first+", last exposure "+exp_last+", "+comments+"\n")
        else:
            file.write("- "+time_start[0:2]+":"+time_start[2:4]+" := script @"+script+"@, first exposure "+exp_first+"\n")
            file.write("- "+time_stop[0:2]+":"+time_stop[2:4]+" := last exposure "+exp_last+", "+comment+"\n")
        file.close()

    def supcal_add_focus_script_os(self,time_start,exp_first,script,time_stop,exp_last,comment,trim):
        """
            Operations Scientist adds new script (focus) in Start Up & Calibrations.
        """
        file = open(self.os_dir+'startup_calibrations','a')
        if (time_stop == "") or (time_stop == " ") :
            file.write("- "+time_start[0:2]+":"+time_start[2:4]+" := script @"+script+"@, first exposure "+exp_first+", last exposure "+exp_last+", trim = "+trim+", "+comments+"\n")
        else:
            file.write("- "+time_start[0:2]+":"+time_start[2:4]+" := script @"+script+"@, first exposure "+exp_first+"\n")
            file.write("- "+time_stop[0:2]+":"+time_stop[2:4]+" := last exposure "+exp_last+", "+comment+"\n")
        file.close()

    def obs_new_item_os(self,time,header):
        """
            Operations Scientist adds new item on the Observing section.
        """
        

        if int(time) < 1200 :
            if len(str(int(time) + 1200))==3:
                new_obsitem_time_stamp = "0"+str(int(time) + 1200)
            else:
                new_obsitem_time_stamp = str(int(time) + 1200)
        else :
            if len(str(int(time) - 1200))==3:
                new_obsitem_time_stamp = "0"+str(int(time) - 1200)
            else:
                new_obsitem_time_stamp = str(int(time) - 1200)

        file = open(self.tmp_obs_dir+new_obsitem_time_stamp,'a')
        file.write("h5. "+header+"\n")
        file.write("\n")
        file.close()

    def obs_add_seq_os(self,time,exp_num,exp_type,tile_number,tile_type,comment):
        """
            Operations Scientist adds new sequence in Observing.
        """

        if int(time) < 1200 :
            if len(str(int(time) + 1200))==3:
                new_obsitem_time_stamp = "0"+str(int(time) + 1200)
            else:
                new_obsitem_time_stamp = str(int(time) + 1200)
        else :
            if len(str(int(time) - 1200))==3:
                new_obsitem_time_stamp = "0"+str(int(time) - 1200)
            else:
                new_obsitem_time_stamp = str(int(time) - 1200)

        file = open(self.tmp_obs_dir+new_obsitem_time_stamp,'a')

        if (tile_number == "") or (tile_number == " ") :
            file.write("- "+time[0:2]+":"+time[2:4]+" := exposure "+exp_num+", "+exp_type+" sequence, "+comment+"\n")
        else :
            file.write("- "+time[0:2]+":"+time[2:4]+" := exposure "+exp_num+", "+exp_type+" sequence, "+tile_type+" tile "+tile_number+", "+comment+"\n")
        file.close()

    def obs_add_com_os(self,time,remark):
        """
            Operations Scientist comment/remark in the Observing section.
        """
        if int(time) < 1200 :
            if len(str(int(time) + 1200))==3:
                new_obsitem_time_stamp = "0"+str(int(time) + 1200)
            else:
                new_obsitem_time_stamp = str(int(time) + 1200)
        else :
            if len(str(int(time) - 1200))==3:
                new_obsitem_time_stamp = "0"+str(int(time) - 1200)
            else:
                new_obsitem_time_stamp = str(int(time) - 1200)

        file = open(self.tmp_obs_dir+new_obsitem_time_stamp,'a')
        file.write("- "+time[0:2]+":"+time[2:4]+" := "+remark+"\n")
        file.close()

    def obs_add_script_os(self,time_start,exp_first,script,time_stop,exp_last,comment):
        """
            Operations Scientist adds new script in the Observing section.
        """
        if int(time_start) < 1200 :
            if len(str(int(time_start) + 1200))==3:
                new_obsitem_time_stamp = "0"+str(int(time_start) + 1200)
            else:
                new_obsitem_time_stamp = str(int(time_start) + 1200)
        else :
            if len(str(int(time_start) - 1200))==3:
                new_obsitem_time_stamp = "0"+str(int(time_start) - 1200)
            else:
                new_obsitem_time_stamp = str(int(time_start) - 1200)

        file = open(self.tmp_obs_dir+new_obsitem_time_stamp,'a')
        if (time_stop == "") or (time_stop == " ") :
            file.write("- "+time_start[0:2]+":"+time_start[2:4]+" := script @"+script+"@, first exposure "+exp_first+", last exposure "+exp_last+", trim = "+trim+", "+comments+"\n")
        else:
            file.write("- "+time_start[0:2]+":"+time_start[2:4]+" := script @"+script+"@, first exposure "+exp_first+"\n")
            file.write("- "+time_stop[0:2]+":"+time_stop[2:4]+" := last exposure "+exp_last+", "+comment+"\n")
        file.close()

    def add_exposure(self, data):
        self.exp_columns = ['Time','Exp_Start','Exp_Type','Quality','Comm','Obs_Comm','Inst_Comm','Exp_Last']
        if not os.path.exists(self.exp_file_pkl):
            init_df = pd.DataFrame(columns=self.exp_columns)
            init_df.to_pickle(self.exp_file_pkl)

        df = pd.read_pickle(self.exp_file_pkl)
        data_df = pd.DataFrame([data], columns=self.exp_columns)
        df = df.append(data_df)

        df = df.drop_duplicates(['Time'],keep='last')
        df = df.sort_values(by=['Time'])
        df.to_pickle(self.exp_file_pkl)
        return df
        

    def dqs_add_exp(self,time_start, exp_start, exp_type, quality, comment, obs_cond_comm = None, inst_perf_comm = None, exp_last = None):

        data = [time_start, exp_start, exp_type, quality, comment, obs_cond_comm, inst_perf_comm, exp_last]
        df = self.add_exposure(data)
        print(df.head())

        file = open(self.dqs_exp_file,'w')
        file.write("h3. DQA Exposures \n")
        file.write("\n")
        for index, row in df.iterrows():
        
            if row['Exp_Last'] is not None:
                file.write("- {}:{} := Exp. # {} - {}, {}, {}, {}\n".format(row['Time'][0:2], row['Time'][2:4], row['Exp_Start'], row['Exp_Last'], row['Exp_Type'],row['Quality'],row['Comm']))
            else:
                file.write("- {}:{} := Exp. # {}, {}, {}, {}\n".format(row['Time'][0:2], row['Time'][2:4], row['Exp_Start'], row['Exp_Type'],row['Quality'],row['Comm']))
            if row['Obs_Comm'] not in [None, " ", ""]:
                file.write("*observing conditions:* {} \n".format(row['Obs_Comm']))
            if row['Inst_Comm'] not in [None, " ", ""]:
                file.write("*instrument performance:* {} \n".format(row['Inst_Comm']))
        file.closed

    def finish_the_night(self):
        """
            Merge together all the different files into one '.txt' file to copy past on the eLog.

        """
        #print("hello!")
        file_nl=open(self.root_dir+'nightlog','w')
        meta_dict = json.load(open('nightlog_meta.json','r'))
        file_nl.write("*Observer (OS)*: {} {}\n".format(meta_dict['os_1'],meta_dict['os_last']))
        file_nl.write("*Lead Observer*: {} {}\n".format(meta_dict['os_lo_1'],meta_dict['os_lo_last']))
        file_nl.write("*Telescope Operator*: {} {}\n".format(meta_dict['os_oa_1'],meta_dict['os_oa_last']))
        file_nl.write("*Ephemerides in local time*:\n")
        file_nl.write("          sunset: {}\n".format(meta_dict['os_sunset']))
        file_nl.write("          18(o) twilight ends: {}\n".format(meta_dict['os_end18']))
        file_nl.write("          18(o) twilight starts: {}\n".format(meta_dict['os_start18']))
        file_nl.write("          sunrise: {}\n".format(meta_dict['os_sunrise']))
        file_nl.write("          moonrise: {}\n".format(meta_dict['os_moonrise']))
        file_nl.write("          moonset: {}\n".format(meta_dict['os_moonset']))
        file_nl.write("           illumination: {}\n".format(meta_dict['os_illumination']))
        file_nl.write("*Weather conditions summary*:{} \n".format(meta_dict['os_weather_conditions']))
        file_nl.write("\n")
        file_nl.write("\n")
        file_nl.write("h3. Plans for the night\n")
        file_nl.write("\n")
        #file_nl.write()#add night plan here
        file_nl.write("\n")
        file_nl.write("\n")
        file_nl.write("h3. Problems and Operations Issues\n")
        file_nl.write("\n")
        #file_nl.write()#add night plan here
        file_nl.write("\n")
        file_nl.write("\n")
        file_nl.write("h3. Weather Summary\n")
        file_nl.write("\n")
        #file_nl.write()#add weather summary here
        file_nl.write("\n")
        file_nl.write("\n")
        file_nl.write("h3. Details on the night progress from the OS (local time)\n")
        file_nl.write("\n")
        file_nl.write("\n")
        if os.path.exists(self.os_dir+'startup_calibrations'):
            supcal_file=open(self.os_dir+'startup_calibrations','r')
            for x in supcal_file:
                file_nl.write(x)
            supcal_file.close()
            file_nl.write("\n")
            file_nl.write("\n")

        os_entries=glob.glob(self.tmp_obs_dir+"*")
        if len(os_entries) > 0:
            for e in os_entries:
                tmp_obs_e=open(e,'r')
                file_nl.write(tmp_obs_e.read())
                tmp_obs_e.close()
            file_nl.write("\n")
            file_nl.write("\n")
            file_nl.write("h3. Details on the night progress from the DQS (local time)\n")
            file_nl.write("\n")
        if os.path.exists(self.qa_dir+'exposures'):
            dqs_entries=open(self.qa_dir+'exposures','r')
            for x in dqs_entries:
                file_nl.write(x)
            dqs_entries.close()
        file_nl.close()
    # merge together all the different files into one .txt file to copy past on the eLog
    # checkout the notebooks at https://github.com/desihub/desilo/tree/master/DESI_Night_Logs/ repository
