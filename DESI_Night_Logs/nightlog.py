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

    def supcal_add_com_os(time,remark):
        """
            Operations Scientist comment/remark on Start Up & Calibrations procedures.
        """
        file = open(self.os_dir+'startup_calibrations','a')
        file.write("- "+time[0;2]+":"+time[2;4]+" := "remark+"\n")
        file.closed

    def supcal_add_seq_os(time,exp_num,exp_type,comment):
        """
            Operations Scientist adds new sequence.
        """
        file = open(self.os_dir+'startup_calibrations','a')
        file.write("- "+time[0;2]+":"+time[2;4]+" := exposure "exp_num+", "+exp_type+", "+comment+"\n")
        file.closed

    def supcal_add_script_os(time_start,exp_first,script,time_stop,exp_last,comment):
        """
            Operations Scientist adds new sequence.
        """
        file = open(self.os_dir+'startup_calibrations','a')
        if (time_stop == "") or (time_stop == " ") :
            file.write("- "+time_start[0;2]+":"+time_start[2;4]+" := script @"+script+"@, first exposure "exp_first+", last exposure "+exp_last+"\n")
        else:
            file.write("- "+time_start[0;2]+":"+time_start[2;4]+" := script @"+script+"@, first exposure "exp_first+"\n")
            file.write("- "+time_stop[0;2]+":"+time_stop[2;4]+" := "comment+"\n")
        file.closed

#    def finish_the_night(self):
    # merge together all the different files into one .txt file to copy past on the set_cosmology
    # checkout the notebooks at https://github.com/desihub/desilo/tree/master/DESI_Night_Logs/ repository
