"""
Created on April 9, 2020
@author: Satya Gontcho A Gontcho
"""

import os
import glob
import json
import pandas as pd
import numpy as np
from datetime import datetime,timezone

from astropy.time import TimezoneInfo
import astropy.units.si as u


class NightLog(object):
    """
        During a night of observing with the Dark Energy Spectroscopic Instrument (DESI),
            observers are required to provide a detailed account of the events of the night.
        The DESI Night Intake (DNI) provides observers with an interface to write the nightlog
            in the proper formatting (textile for the eLog) while providing a platform to
            follow live the night progress.

            PKL files unique but combination of them is what should be the same for both pages. So all _file
            should be good.
            #write_pkl
            #make combined df
            #then write its file
    """

    def __init__(self, obsday, location):
        """
            Setup the nightlog framework for a given obsday.
        """
        self.obsday = obsday #YYYYMMDD
        self.location = location

        self.root_dir = os.path.join(os.environ['NL_DIR'],self.obsday)
        self.image_dir = os.path.join(self.root_dir,"images")
        self.os_dir = os.path.join(self.root_dir,"OperationsScientist")
        self.dqs_dir = os.path.join(self.root_dir,"DataQualityAssessment")
        self.other_dir = os.path.join(self.root_dir,"OtherInput")

        self.header_file = os.path.join(self.root_dir,'header_{}'.format(self.location))
        self.header_html = os.path.join(self.root_dir,'header_{}.html'.format(self.location))
        self.nightlog_file = os.path.join(self.root_dir,'nightlog_{}'.format(self.location))
        self.nightlog_html = os.path.join(self.root_dir,'nightlog_{}.html'.format(self.location))

        self.os_pb = os.path.join(self.os_dir,'problems_{}.pkl'.format(self.location))
        self.dqs_pb = os.path.join(self.dqs_dir,'problems_{}.pkl'.format(self.location))
        self.other_pb = os.path.join(self.other_dir,'problems_{}.pkl'.format(self.location))
        self.os_pb_file = os.path.join(self.os_dir,'problems_{}'.format(self.location))
        self.dqs_pb_file = os.path.join(self.dqs_dir,'problems_{}'.format(self.location))
        self.other_pb_file = os.path.join(self.other_dir,'problems_{}'.format(self.location))

        self.objectives = os.path.join(self.os_dir,'objectives_{}.pkl'.format(self.location))
        self.objectives_file = os.path.join(self.os_dir,'objectives_{}'.format(self.location))

        self.milestone = os.path.join(self.os_dir,'milestones_{}.pkl'.format(self.location))
        self.milestone_file = os.path.join(self.os_dir,'milestones_{}'.format(self.location))

        self.os_cl = os.path.join(self.os_dir,'checklist_{}.pkl'.format(self.location))
        self.dqs_cl = os.path.join(self.dqs_dir,'checklist_{}.pkl'.format(self.location))
        self.os_cl_file = os.path.join(self.os_dir,'checklist_{}'.format(self.location))
        self.dqs_cl_file = os.path.join(self.dqs_dir,'checklist_{}'.format(self.location))

        self.os_exp = os.path.join(self.os_dir,'exposures_{}.pkl'.format(self.location))
        self.dqs_exp = os.path.join(self.dqs_dir,'exposures_{}.pkl'.format(self.location))
        self.other_exp = os.path.join(self.other_dir,'exposures_{}.pkl'.format(self.location))
        self.exp_file = os.path.join(self.root_dir,'exposures_{}'.format(self.location))

        self.weather = os.path.join(self.os_dir,'weather_{}.pkl'.format(self.location))
        self.weather_file = os.path.join(self.os_dir,'weather_{}'.format(self.location))

        self.meta_json = os.path.join(self.root_dir,'nightlog_meta_{}.json'.format(self.location))
        self.image_file = os.path.join(self.image_dir, 'image_list_{}'.format(self.location))
        self.upload_image_file = os.path.join(self.image_dir, 'upload_image_list_{}'.format(self.location))
        self.contributer_file = os.path.join(self.root_dir, 'contributer_file_{}'.format(self.location))
        self.summary_file = os.path.join(self.root_dir, 'summary_file_{}'.format(self.location))
        self.time_use = os.path.join(self.root_dir, 'time_use_{}.csv'.format(self.location))
        self.explist_file = os.path.join(self.root_dir, 'exposures_{}.csv'.format(self.location))
        self.telem_plots_file = os.path.join(self.root_dir, 'telem_plots_{}.png'.format(self.location))

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

    def write_time(self, time_string, kp_only=False):
        try:
            dt = datetime.strptime(time_string, "%Y%m%dT%H:%M")
            dt_utc = dt.astimezone(tz=timezone.utc)
            if kp_only:
                tt = "{}".format(dt.strftime("%H:%M"))
            else:
                tt = "{} [{}]".format(dt.strftime("%H:%M"), dt_utc.strftime("%H:%M"))
            return tt
        except:
            return time_string

    def get_started_os(self, data): 
        """
            Operations Scientist lists the personal present, ephemerids and weather conditions at sunset.
        """
        items = ['LO_firstname','LO_lastname','OA_firstname','OA_lastname','os_1_firstname','os_1_lastname',
        'os_2_firstname','os_2_lastname','time_sunset','time_sunrise','time_moonrise','time_moonset','illumination',
        'dusk_18_deg','dawn_18_deg','dqs_1','dqs_last']
        meta_dict = {}
        for item in items:
            try:
                meta_dict[item] = data[item]
            except:
                meta_dict[item] = None

        with open(self.meta_json,'w') as fp:
            json.dump(meta_dict, fp)

    def _open_kpno_file_first(self, filen):
        loc = filen.split('_')[-1]
        new_filen = filen.replace(loc, 'kpno')
        if os.path.exists(new_filen):
            return open(new_filen, 'r')
        else:
            try:
                return open(filen, 'r')
            except:
                return None

    def add_dqs_observer(self, dqs_firstname, dqs_lastname):
        f = self._open_kpno_file_first(self.meta_json)
        if f is not None:
            meta_dict = json.load(f)
            meta_dict['dqs_1'] = dqs_firstname
            meta_dict['dqs_last'] = dqs_lastname
            os.remove(self.meta_json)
            with open(self.meta_json, 'w') as ff:
                json.dump(meta_dict, ff)

        self.write_intro()

    def _combine_compare_pkl_files(self, filen):
        loc = os.path.splitext(filen)[0].split('_')[-1]
        df = pd.read_pickle(filen)
        if loc == 'kpno':
            nersc_filen = filen.replace(loc, 'nersc')
            if os.path.exists(nersc_filen):
                df2 = pd.read_pickle(nersc_filen)
                df_ = pd.concat([df,df2])
                df_ = df_.drop_duplicates(by=['Time'],keep='first')
                df_ = df_.sort_values(by=['Time'])
                return df_
            else:
                return df
        elif loc == 'nersc':
            kpno_filen = filen.replace(loc, 'kpno')
            if os.path.exists(kpno_filen):
                df2 = pd.read_pickle(kpno_filen)
                df_ = pd.concat([df2,df])
                df_ = df_.drop_duplicates(by=['Time'],keep='first')
                df_ = df_.sort_values(by=['Time'])
                return df_
            else:
                return df

    def write_pkl(self, data, cols, filen, dqs_exp=False):
        if not os.path.exists(filen):
            init_df = pd.DataFrame(columns=cols)
            init_df.to_pickle(filen)
        data = np.array(data)

        df = pd.read_pickle(filen)
        data_df = pd.DataFrame([data], columns=cols)
        df = df.append(data_df)

        if self.replace:
            if dqs_exp:
                df = df.drop_duplicates(['Exp_Start'], keep='last')
            else:
                df = df.drop_duplicates(['Time'], keep='last')

        df = df.sort_values(by=['Time'])
        df.reset_index(inplace=True, drop=True)
        df.to_pickle(filen)
        df_ = self._combine_compare_pkl_files(filen)
        return df_

    def write_img(self, file, img_data, img_name):
        if img_name is not None and img_data is not None:
            # if img_filen is a bytearray we have received an image in base64 string (from local upload)
            # images are stored in the images directory
            if isinstance(img_data, bytes):
                self._upload_and_save_image(img_data, img_name)
                self._write_image_tag(file, img_name)
            else:
                print('ERROR: invalid format for uploading image')
        return file

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


    def write_problem(self, data, user, img_name=None, img_data=None):
        prob_cols = ['Time', 'Problem', 'alarm_id', 'action', 'name','img_name','img_data']
        if user == 'OS':
            file = self.os_pb
            filen = self.os_pb_file
        if user == 'DQS':
            file = self.dqs_pb
            filen = self.dqs_pb_file
        if user == 'Other':
            file = self.other_pb
            filen = self.other_pb_file
        data = np.hstack([data, img_name, img_data])
        df = self.write_pkl(data, prob_cols, file)


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
                file.write(' ({})'.format(row['name']))
                file.write('_')
            if row['img_name'] is not None:
                self.write_img(file, row['img_data'], row['img_name'])
            file.write('\n')

        #file = self.write_img(file, img_data, img_name)
        file.close()

    def write_other_exp(self, data, img_name = None, img_data = None):
        exp_columns = ['Time','Comment','Exp_Start','Name','img_name','img_data']
        data = np.hstack([data, img_name, img_data])
        df = self.write_pkl(data, exp_columns, self.other_exp)
        self.write_exposure()


    def write_dqs_exp(self, data, img_name = None, img_data = None):


        exp_columns = ['Time','Exp_Start','Quality','Comment','img_name','img_data']
        data = np.hstack([data, img_name, img_data])
        df = self.write_pkl(data, exp_columns, self.dqs_exp,dqs_exp=True)

        self.write_exposure()


    def check_exp_times(self, file):
        if os.path.exists(file):
            df = pd.read_pickle(file)
            if os.path.exists(self.explist_file):
                exp_df = pd.read_csv(self.explist_file)
            for index, row in df.iterrows():
                try:
                    e_ = exp_df[exp_df.id == int(row['Exp_Start'])]
                    time = pd.to_datetime(e_.date_obs).dt.strftime('%Y%m%dT%H:%M').values[0]  
                    df.at[index, 'Time'] = time
                except:
                    pass
            df.to_pickle(file)
            return df
        else:
            return None


    def write_exposure(self):
        if os.path.exists(self.explist_file):
            exp_df = pd.read_csv(self.explist_file)

        file = open(self.exp_file,'w')
        os_df = self.check_exp_times(self.os_exp)
        dqs_df = self.check_exp_times(self.dqs_exp)
        other_df = self.check_exp_times(self.other_exp)
        times = []
        for df in [os_df, dqs_df, other_df]:
            if df is not None:
                tt = list(df.Time)
                for t in tt:
                    if t is not None:
                        times.append(t)
        times = np.unique(times)
        #times = np.unique([x.Time for x in np.hstack([os_df, dqs_df, other_df]) if x is not None])

        for time in times:
            if os_df is not None:
                os_ = os_df[os_df.Time == time]
            else:
                os_ = []
            if dqs_df is not None:
                dqs_ = dqs_df[dqs_df.Time == time]
            else:
                dqs_ = []
            if other_df is not None:
                other_ = other_df[other_df.Time == time]
            else:
                other_ = []

            if len(os_) > 0:
                if os_['Exp_Start'].values[0] is not None:

                    file.write("- {} Exp. {} := {}".format(self.write_time(os_['Time'].values[0]), os_['Exp_Start'].values[0], os_['Comment'].values[0]))
                    try:
                        this_exp = exp_df[exp_df.id == int(os_['Exp_Start'])]
                        file.write("; Tile: {}, Exptime: {}, Airmass: {}, Sequence: {}, Flavor: {}, Program: {}\n".format(
                                   this_exp['tileid'].values[0],this_exp['exptime'].values[0],this_exp['airmass'].values[0],this_exp['sequence'].values[0],
                                   this_exp['flavor'].values[0],this_exp['program'].values[0]))
                    except:
                        file.write("\n") 
                    if len(dqs_) > 0:
                        file.write(f"Data Quality: {dqs_['Quality'].values[0]}; {dqs_['Comment'].values[0]}\n")
                        if dqs_['img_name'].values[0] is not None:
                            self.write_img(file, dqs_['img_data'].values[0], dqs_['img_name'].values[0])
                            file.write('\n')
                    if len(other_) > 0:
                        file.write("Comment: {} ({})\n".format(other_['Comment'].values[0], other_['Name'].values[0]))
                        if other_['img_name'] is not None:
                            self.write_img(file, other_['img_data'].values[0], other_['img_name'].values[0])
                            file.write('\n')

                else:
                    file.write("- {} := {}\n".format(self.write_time(os_['Time'].values[0]), os_['Comment'].values[0]))


                if os_['img_name'].values[0] is not None:
                    self.write_img(file, os_['img_data'].values[0], os_['img_name'].values[0])
                    file.write('\n')

            else:
                if len(dqs_) > 0:
                    file.write("- {} Exp. {} := Data Quality: {}, {}".format(self.write_time(dqs_['Time'].values[0]), dqs_['Exp_Start'].values[0], dqs_['Quality'].values[0],dqs_['Comment'].values[0]))
                    try:
                        this_exp = exp_df[exp_df.id == int(dqs_['Exp_Start'].values[0])]
                        file.write("; Tile: {}, Exptime: {}, Airmass: {}, Sequence: {}, Flavor: {}, Program: {}\n".format(
                                   this_exp['tileid'].values[0],this_exp['exptime'].values[0],this_exp['airmass'].values[0],this_exp['sequence'].values[0],
                                   this_exp['flavor'].values[0],this_exp['program'].values[0]))
                    except:
                        file.write("\n")
                    if dqs_['img_name'].values[0] is not None:
                            self.write_img(file, dqs_['img_data'].values[0], dqs_['img_name'].values[0])
                            file.write('\n')

                    if len(other_) > 0:
                        file.write("Comment: {} ({})\n".format(other_['Comment'].values[0], other_['Name'].values[0]))
                        if other_['img_name'] is not None:
                            self.write_img(file, other_['img_data'].values[0], other_['img_name'].values[0])
                            file.write('\n')
                else:
                    if other_['Exp_Start'].values[0] is not None:
                        file.write("- {} Exp: {}:= {} ({})\n".format(self.write_time(other_['Time'].values[0]), other_['Exp_Start'].values[0], other_['Comment'].values[0], other_['Name'].values[0]))
                    else:
                        file.write("- {} := {} ({})\n".format(self.write_time(other_['Time'].values[0]), other_['Comment'].values[0], other_['Name'].values[0]))
                    if other_['img_name'] is not None:
                        self.write_img(file, other_['img_data'].values[0], other_['img_name'].values[0])
                        file.write('\n')

        file.close()



    def write_os_exp(self, data, img_name=None, img_data=None):     
        

        exp_columns = ['Time','Comment','Exp_Start','img_name','img_data']
        data = np.hstack([data, img_name, img_data])
        df = self.write_pkl(data, exp_columns, self.os_exp)

        self.write_exposure()


    def load_index(self, idx, page):
        if page == 'milestone':
            the_path = self.milestone
        if page == 'plan':
            the_path = self.objectives
        df = self._combine_compare_pkl_files(the_path)
        item = df[df.index == int(idx)]
        if len(item) > 0:
            return True, item
        else:
            return False, item

    def load_exp(self, exp):
        the_path = self.dqs_exp

        df = self._combine_compare_pkl_files(the_path)

        item = df[df.Exp_Start == exp]
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
            _dir = self.other_dir

        if exp_type == 'exposure':
            the_path = os.path.join(_dir, 'exposures.pkl')
        elif exp_type == 'problem':
            the_path = os.path.join(_dir, 'problems.pkl')

        df = self._combine_compare_pkl_files(the_path)
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

    def add_contributer_list(self, contributers):
        file = open(self.contributer_file, 'w')
        file.write(contributers)
        file.write("\n")
        file.close()

    def add_summary(self, data):

        df = pd.DataFrame(data, index=[0])
        df.to_csv(self.time_use,index=False)
        d = df.iloc[0]

        file = open(self.summary_file, 'w')

        if df['summary_1'] is not None:
            file.write(df['summary_1'].values[0])
            file.write("\n")
        if df['summary_2'] is not None:
            file.write(df['summary_2'].values[0])
            file.write("\n")
        file.write("Time Use (hrs):")
        file.write(" Observing: {}, Testing: {}, Loss to Instrument: {}, Loss to Weather: {}, Loss to Telescope: {}, Total: {}, Time between 18 deg. twilight: {}\n".format(d['obs_time'],
            d['test_time'],d['inst_loss'], d['weather_loss'], d['tel_loss'], d['total'], d['18deg']))
        file.write("\n")
        file.close()

    def compile_entries(self, the_path, header, file_nl, kpno_first = True):
        if kpno_first:
            f = self._open_kpno_file_first(the_path)
            if f is not None:
                if header is not None:
                    file_nl.write(header)
                file_nl.write("\n")
                file_nl.write("\n")
                for line in f:
                    file_nl.write(line)
                    file_nl.write("\n") 
            f.close()
        else:
            if os.path.exists(the_path):
                f = open(the_path, 'r')
                if header is not None:
                    file_nl.write(header)
                file_nl.write("\n")
                file_nl.write("\n")
                for line in f:
                    file_nl.write(line)
                    file_nl.write("\n")
                f.close()
        

    def write_intro(self):
        file_intro=open(self.header_file,'w')
        try:
            meta_dict = json.load(self._open_kpno_file_first(self.meta_json))
            file_intro.write("*Observer (OS-1)*: {} {}\n".format(meta_dict['os_1_firstname'],meta_dict['os_1_lastname']))
            file_intro.write("*Observer (OS-2)*: {} {}\n".format(meta_dict['os_2_firstname'],meta_dict['os_2_lastname']))
            file_intro.write("*Observer (DQS)*: {} {}\n".format(meta_dict['dqs_1'],meta_dict['dqs_last']))
            file_intro.write("*Lead Observer*: {} {}\n".format(meta_dict['LO_firstname'],meta_dict['LO_lastname']))
            file_intro.write("*Telescope Operator*: {} {}\n".format(meta_dict['OA_firstname'],meta_dict['OA_lastname']))
            file_intro.write("*Ephemerides in local time [UTC]*:\n")
            file_intro.write("* sunset: {}\n".format(self.write_time(meta_dict['time_sunset'])))
            file_intro.write("* 18(o) twilight ends: {}\n".format(self.write_time(meta_dict['dusk_18_deg'])))
            file_intro.write("* 18(o) twilight starts: {}\n".format(self.write_time(meta_dict['dawn_18_deg'])))
            file_intro.write("* sunrise: {}\n".format(self.write_time(meta_dict['time_sunrise'])))
            file_intro.write("* moonrise: {}\n".format(self.write_time(meta_dict['time_moonrise'])))
            file_intro.write("* moonset: {}\n".format(self.write_time(meta_dict['time_moonset'])))
            file_intro.write("* illumination: {}\n".format(meta_dict['illumination']))

        except Exception as e:
            print('Exception reading meta json file: {}'.format(str(e)))

        file_intro.close()
        cmd = "pandoc --metadata pagetitle=header -s {} -f textile -t html -o {}".format(self.header_file,self.header_html)

        try:
            os.system(cmd)
        except Exception as e:
            print('Exception calling pandoc (header): %s' % str(e))

    def finish_the_night(self):
        """
            Merge together all the different files into one '.txt' file to copy past on the eLog.
        """
        file_nl=open(self.nightlog_file, 'w')

        #Write the meta_html here
        try:
            file_intro = self._open_kpno_file_first(self.header_file)
            lines = file_intro.readlines()
            for line in lines:
                file_nl.write(line)
            file_nl.write("\n")
            file_nl.write("\n")
        except Exception as e:
            print("Exception with nightlog header: {}".format(e))

        #Contributers
        self.compile_entries(self.contributer_file, "h3. Contributers\n", file_nl, kpno_first=False)

        #Night Summary
        self.compile_entries(self.summary_file, "h3. Night Summary\n", file_nl, kpno_first=False)

        #Plan for the night
        file_nl.write("h3. Plan for the night\n")
        file_nl.write("\n")
        file_nl.write("The detailed operations plan for today (obsday "+self.obsday+") can be found at https://desi.lbl.gov/trac/wiki/DESIOperations/ObservingPlans/OpsPlan"+self.obsday+".\n")
        file_nl.write("\n")
        file_nl.write("Main items are listed below:\n")
        self.compile_entries(self.objectives_file, None, file_nl, kpno_first=False)

        #Milestones/Accomplishments
        file_nl.write("\n")
        file_nl.write("\n")
        file_nl.write("h3. Milestones and Major Progress\n")
        file_nl.write("\n")
        file_nl.write("\n")
        self.compile_entries(self.milestone_file, None, file_nl, kpno_first=False)

        #Problems
        file_nl.write("\n")
        file_nl.write("\n")
        file_nl.write("h3. Problems and Operations Issues [OS, *DQS*, _Other_]\n")
        self.compile_entries(self.os_pb_file, None, file_nl, kpno_first=False)
        self.compile_entries(self.dqs_pb_file, None, file_nl, kpno_first=False)
        self.compile_entries(self.other_pb_file, None, file_nl, kpno_first=False)

        #Weather
        file_nl.write("\n")
        file_nl.write("\n")
        file_nl.write("h3. Observing Conditions\n")
        self.compile_entries(self.weather_file, None, file_nl, kpno_first=False)
        file_nl.write("\n")
        file_nl.write("\n")

        #Checklists
        file_nl.write("\n")
        file_nl.write("\n")
        file_nl.write("h3. Checklists\n")
        file_nl.write("\n")
        file_nl.write("\n")
        self.compile_entries(self.os_cl_file, "h5. Observing Scientist", file_nl, kpno_first=False)
        self.compile_entries(self.dqs_cl_file, "h5. Data Quality Scientist", file_nl, kpno_first=False)


        #Nightly Progress
        file_nl.write("h3. Details on the Night Progress\n")
        file_nl.write("\n")
        file_nl.write("\n")
        self.compile_entries(self.exp_file, None, file_nl, kpno_first=False)
        #self.compile_entries(self.dqs_exp_file, "h5. Exposure Quality (DQS)\n", file_nl)
        #self.compile_entries(self.other_exp_file, "h5. Comments (Non-Observers)\n", file_nl)

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
                                                                                                             self.nightlog_file,
                                                                                                             self.nightlog_html)
        try:
            os.system(cmd)
        except Exception as e:
            print('Exception calling pandoc: %s' % str(e))

        #os.system("pandoc --self-contained --metadata pagetitle='report' -s {} -f textile -t html -o {}".format(self.image_dir, os.path.join(self.root_dir,'nightlog'),os.path.join(self.root_dir,'nightlog.html')))
    # merge together all the different files into one .txt file to copy past on the eLog
    # checkout the notebooks at https://github.com/desihub/desilo/tree/master/DESI_Night_Logs/ repository
