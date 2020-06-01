"""
Created on April 9, 2020

@author: Satya Gontcho A Gontcho
"""

import os


class NightLog(object):
    """
        During a night of observing with the Dark Energy Spectroscopic Instrument (DESI),
        observers are required to provide a detailed account of the events of the night.
        This tool provides observers with an interface to write the nightlog in the proper formatting.
    """

    def __init__(self,year,month,day):
        """
            Setup the nightlog framework for a given obsday.
        """
        self.obsday=year+month+day

    def initializing(self):
        """
            Creates the folders where all the .txt files used to create the Night Log will be containted.
        """
        self.os_dir="nightlogs/"+self.obsday+"/OperationsScientist/"
        self.qa_dir="nightlogs/"+self.obsday+"/DataQualityAssessment/"
        if not os.path.exists(self.os_dir):
            os.makedirs(self.os_dir)
        if not os.path.exists(self.qa_dir):
            os.makedirs(self.qa_dir)
        return print("Your obsday is "+self.obsday)

    def check_exists(self):
        self.os_dir="nightlogs/"+self.obsday+"/OperationsScientist/"
        self.qa_dir="nightlogs/"+self.obsday+"/DataQualityAssessment/"
        if not os.path.exists(self.qa_dir):
            return 'Night Log has not yet been initialized'
        else:
            #Get data from get_started_os and return that
            return 'Night Log has been initialized'


    def get_started_os(self,your_firstname,your_lastname,LO_firstname,LO_lastname,OA_firstname,OA_lastname,time_sunset,time_18_deg_twilight_ends,time_18_deg_twilight_starts,time_sunrise,time_moonrise,time_moonset,illumination,weather_conditions):
        """
            Operations Scientist lists the personal present, ephemerids and weather conditions at sunset.
        """
        self.os_1 = your_firstname
        self.os_last = your_lastname
        self.os_lo_1 = LO_firstname
        self.os_lo_last = LO_lastname
        self.os_oa_1 = OA_firstname
        self.os_oa_last = OA_lastname
        self.os_sunset = time_sunset
        self.os_sunrise = time_sunrise
        self.os_moonset = time_moonset
        self.os_moonrise = time_moonrise
        self.os_end18 = time_18_deg_twilight_ends
        self.os_start18 = time_18_deg_twilight_starts
        self.os_illumination = illumination
        self.os_weather_conditions = weather_conditions

    def add_dqs_observer(self,dqs_firstname, dqs_lastname):
        self.dqs_firstname = dqs_firstname
        self.dqs_lastname = dqs_lastname

    def supcal_add_com_os(self,time,remark):
        """
            Operations Scientist comment/remark on Start Up & Calibrations procedures.
        """
        file = open(self.os_dir+'startup_calibrations','a')
        file.write("- "+time[0:2]+":"+time[2:4]+" := "+remark+"\n")
        file.closed

    def supcal_add_seq_os(self,time,exp_num,exp_type,comment):
        """
            Operations Scientist adds new sequence in Start Up & Calibrations.
        """
        file = open(self.os_dir+'startup_calibrations','a')
        file.write("- "+time[0:2]+":"+time[2:4]+" := exposure "+exp_num+", "+exp_type+", "+comment+"\n")
        file.closed

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
        file.closed

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
        file.closed

    def obs_new_item_os(self,time,header):
        """
            Operations Scientist adds new item on the Observing section.
        """
        self.tmp_obs_dir=self.os_dir+'observing_'

        if int(time) < 1200 :
            new_obsitem_time_stamp = str(int(time) + 1200) #fix the number of charater in string (4)
        else :
            new_obsitem_time_stamp = str(int(time) - 1200) #fix the number of charater in string (4)

        file = open(self.tmp_obs_dir+new_obsitem_time_stamp,'a')
        file.write("h5. "+header+"\n")
        file.write("\n")
        file.closed

    def obs_add_seq_os(self,time,exp_num,exp_type,tile_number,tile_type,comment):
        """
            Operations Scientist adds new sequence in Observing.
        """

        if int(time) < 1200 :
            new_obsitem_time_stamp = str(int(time) + 1200) #fix the number of charater in string (4)
        else :
            new_obsitem_time_stamp = str(int(time) - 1200) #fix the number of charater in string (4)

        file = open(self.tmp_obs_dir+new_obsitem_time_stamp,'a')

        if (tile_number == "") or (tile_number == " ") :
            file.write("- "+time[0:2]+":"+time[2:4]+" := exposure "+exp_num+", "+exp_type+" sequence, "+comment+"\n")
        else :
            file.write("- "+time[0:2]+":"+time[2:4]+" := exposure "+exp_num+", "+exp_type+" sequence, "+tile_type+" tile "+tile_number+", "+comment+"\n")
        file.closed

    def obs_add_com_os(self,time,remark):
        """
            Operations Scientist comment/remark in the Observing section.
        """
        if int(time) < 1200 :
            new_obsitem_time_stamp = str(int(time) + 1200) #fix the number of charater in string (4)
        else :
            new_obsitem_time_stamp = str(int(time) - 1200) #fix the number of charater in string (4)

        file = open(self.tmp_obs_dir+new_obsitem_time_stamp,'a')
        file.write("- "+time[0:2]+":"+time[2:4]+" := "+remark+"\n")
        file.closed

    def obs_add_script_os(self,time_start,exp_first,script,time_stop,exp_last,comment):
        """
            Operations Scientist adds new script in the Observing section.
        """
        if int(time) < 1200 :
            new_obsitem_time_stamp = str(int(time_start) + 1200) #fix the number of charater in string (4)
        else :
            new_obsitem_time_stamp = str(int(time_start) - 1200) #fix the number of charater in string (4)

        file = open(self.tmp_obs_dir+new_obsitem_time_stamp,'a')
        if (time_stop == "") or (time_stop == " ") :
            file.write("- "+time_start[0:2]+":"+time_start[2:4]+" := script @"+script+"@, first exposure "+exp_first+", last exposure "+exp_last+", trim = "+trim+", "+comments+"\n")
        else:
            file.write("- "+time_start[0:2]+":"+time_start[2:4]+" := script @"+script+"@, first exposure "+exp_first+"\n")
            file.write("- "+time_stop[0:2]+":"+time_stop[2:4]+" := last exposure "+exp_last+", "+comment+"\n")
        file.closed

    def create_dqs_files(self):
        file = open(self.dqs_exp_file,'a')
        file.write("h3. DQA Exposures \n")
        file.write("\n")
        file.closed

    def dqs_add_exp(self,time_start, exp_start, exp_type, quality, comment, obs_cond_comm = None, inst_perf_comm = None, exp_last = None):
        self.dqs_exp_file = self.qa_dir+'/exposures'
        if not os.path.exists(self.dqs_exp_file):
            self.create_dqs_files()

        file = open(self.dqs_exp_file,'a')
        if exp_last is not None:
            file.write("- {}:{} := Exp. # {} - {}, {}, {}, {}\n".format(time_start[0:2], time_start[2:4], exp_start, exp_last, exp_type, quality, comment))
        else:
            file.write("- {}:{} := Exp. # {}, {}, {}, {}\n".format(time_start[0:2], time_start[2:4], exp_start, exp_type, quality, comment))
        if obs_cond_comm is not None:
            file.write("*observing conditions:* {} \n".format(obs_cond_comm))
        if inst_perf_comm is not None:
            file.write("*instrument performance:* {} \n".format(inst_perf_comm))
        file.closed

    # def new_entry(self,time_start,exp_first,script,time_stop,exp_last,comment,header,trim,entry_number,entry_type):
    #         """
    #             time_start: time where the events described in the entry start
    #             exp_first: exposure number of the first exposure
    #             script: yes/no
    #             if script, time_stop : time where the script finished
    #             if script, exp_last : exposure number of the last exposure
    #             comment : add comment if needed (exposure time, count, problem,..)
    #             header : when starting a new test, add a new header (Start Up and Calibrations, ELG, LRG+QSO, BSG, other)
    #             if focus scan, trim : value of the Trim
    #             if replace entry, entry_number
    #
    #         """

#    def finish_the_night(self):
    # merge together all the different files into one .txt file to copy past on the set_cosmology
    # checkout the notebooks at https://github.com/desihub/desilo/tree/master/DESI_Night_Logs/ repository
