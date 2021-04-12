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

        self.os_pb = os.path.join(self.os_dir,'problems_{}.csv'.format(self.location))
        self.dqs_pb = os.path.join(self.dqs_dir,'problems_{}.csv'.format(self.location))
        self.other_pb = os.path.join(self.other_dir,'problems_{}.csv'.format(self.location))

        self.objectives = os.path.join(self.os_dir,'objectives_{}.csv'.format(self.location))

        self.milestone = os.path.join(self.os_dir,'milestones_{}.csv'.format(self.location))

        self.os_cl = os.path.join(self.os_dir,'checklist_{}.csv'.format(self.location))
        self.dqs_cl = os.path.join(self.dqs_dir,'checklist_{}.csv'.format(self.location))

        self.os_exp = os.path.join(self.os_dir,'exposures_{}.csv'.format(self.location))
        self.dqs_exp = os.path.join(self.dqs_dir,'exposures_{}.csv'.format(self.location))
        self.other_exp = os.path.join(self.other_dir,'exposures_{}.csv'.format(self.location))

        self.weather = os.path.join(self.os_dir,'weather_{}.csv'.format(self.location))

        self.meta_json = os.path.join(self.root_dir,'nightlog_meta_{}.json'.format(self.location))
        self.image_file = os.path.join(self.image_dir, 'image_list_{}'.format(self.location))
        self.upload_image_file = os.path.join(self.image_dir, 'upload_image_list_{}'.format(self.location))
        self.contributer_file = os.path.join(self.root_dir, 'contributer_file_{}'.format(self.location))
        self.summary_file = os.path.join(self.root_dir, 'summary_file_{}'.format(self.location))
        self.time_use = os.path.join(self.root_dir, 'time_use_{}.csv'.format(self.location))
        self.explist_file = os.path.join(self.root_dir, 'explist_{}.csv'.format(self.location))
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
        loc = os.path.splitext(filen)[0].split('_')[-1]
        new_filen = filen.replace(loc, 'kpno')
        if os.path.exists(new_filen):
            return new_filen
        else:
            return filen

    def add_dqs_observer(self, dqs_firstname, dqs_lastname):
        filen = self._open_kpno_file_first(self.meta_json)
        if filen is not None:
            with open(filen, 'r') as f:
                meta_dict = json.load(f)
                meta_dict['dqs_1'] = dqs_firstname
                meta_dict['dqs_last'] = dqs_lastname
                os.remove(self.meta_json)
                with open(self.meta_json, 'w') as ff:
                    json.dump(meta_dict, ff)

        self.write_intro()


    def _combine_compare_csv_files(self, filen):
        loc = os.path.splitext(filen)[0].split('_')[-1]
        if loc == 'kpno':
            other_filen = filen.replace(loc, 'nersc')
        elif loc == 'nersc':
            other_filen = filen.replace(loc, 'kpno')
        dfs = []
        if os.path.exists(filen):
            df1 = pd.read_csv(filen)
            dfs.append(df1)
        if os.path.exists(other_filen):
            df2 = pd.read_csv(other_filen)
            dfs.append(df2)
        if len(dfs) > 0:
            df_ = pd.concat(dfs)
            df_ = df_.sort_values(by=['Time'])
            df_.reset_index(inplace=True, drop=True)
            return df_
        else:
            return None

    def write_csv(self, data, cols, filen, dqs_exp=False):

        if not os.path.exists(filen):
            init_df = pd.DataFrame(columns=cols)
            init_df.to_csv(filen, index=False)
        data = np.array(data)

        df = pd.read_csv(filen)
        data_df = pd.DataFrame([data], columns=cols)
        df = df.append(data_df)

        if self.replace:
            if dqs_exp:
                df = df.drop_duplicates(['Exp_Start'], keep='last')
            else:
                df = df.drop_duplicates(['Time'], keep='last')

        df = df.sort_values(by=['Time'])
        df.reset_index(inplace=True, drop=True)
        df.to_csv(filen, index=False)
        return df

    def write_img(self, file, img_data, img_name):
        if str(img_name) not in ['None','nan'] and str(img_data) not in ['None','nan']:
            # if img_filen is a bytearray we have received an image in base64 string (from local upload)
            # images are stored in the images directory
            if isinstance(img_data, bytes):
                self._upload_and_save_image(img_data, img_name)
                self._write_image_tag(file, img_name)
            else:
                print('ERROR: invalid format for uploading image')
        return file

    def add_input(self, data, tab, img_name=None, img_data=None):
        dqs_exp = False
        if tab == 'plan':
            cols =['Time', 'Objective']
            file = self.objectives
        if tab == 'milestone':
            cols = ['Time','Desc','Exp_Start','Exp_Stop','Exp_Excl']
            file = self.milestone
        if tab == 'weather':
            cols = ['Time','desc','temp','wind','humidity','seeing','tput','skylevel']
            file = self.weather
        if tab == 'problem':
            cols = ['user','Time', 'Problem', 'alarm_id', 'action', 'name','img_name']
            pb_files = {'OS':self.os_pb,'DQS':self.dqs_pb,'Other':self.other_pb}
            file = pb_files[data[0]]
            data.append(img_name)
        if tab == 'checklist':
            cols = ['user','Time','Comment']
            cl_files = {'OS':self.os_cl,'DQS':self.dqs_cl}
            file = cl_files[data[0]]
        if tab == 'other_exp':
            cols = ['Time','Comment','Exp_Start','Name','img_name']
            file = self.other_exp
            data.append(img_name)
        if tab == 'dqs_exp':
            cols = ['Time','Exp_Start','Quality','Comment','img_name']
            file = self.dqs_exp
            dqs_exp = True
            data.append(img_name)
        if tab == 'os_exp':
            cols = ['Time','Comment','Exp_Start','img_name']
            file = self.os_exp
            data.append(img_name)

        if str(img_name) not in ['None','nan','',' ',np.nan] and str(img_data) not in ['None','nan','',' ',np.nan]:
            # if img_filen is a bytearray we have received an image in base64 string (from local upload)
            # images are stored in the images directory
            if isinstance(img_data, bytes):
                self._upload_and_save_image(img_data, img_name)
        
        df = self.write_csv(data, cols, file, dqs_exp=dqs_exp)
        

    def write_plan(self, filen):
        df = self._combine_compare_csv_files(self.objectives)
        if df is not None:
            df = df.drop_duplicates(['Time'], keep='first')
            df.reset_index(inplace=True, drop=True)
            for index, row in df.iterrows():
                filen.write("* [{}] {}".format(index, row['Objective']))
                filen.write("\n\n")

    def write_milestone(self, filen):
        df = self._combine_compare_csv_files(self.milestone)
        if df is not None:
            df = df.drop_duplicates(['Time'], keep='first')
            df.reset_index(inplace=True, drop=True)
            for index, row in df.iterrows():
                filen.write("* [{}] {}".format(index, row['Desc']))
                if not pd.isna(row['Exp_Start']): # not in [np.nan, 'nan',None, 'None', " ", ""]:
                    filen.write("; Exposure(s): {}".format(row['Exp_Start']))
                if not pd.isna(row['Exp_Stop']): #not in [np.nan, 'nan',None, 'None', " ", ""]:   
                    filen.write(" - {}".format(row['Exp_Stop']))
                if not pd.isna(row['Exp_Excl']): # not in [np.nan, 'nan',None, 'None', " ", ""]:   
                    filen.write(", excluding {}".format(row['Exp_Excl']))
                filen.write("\n")

    def write_checklist(self, filen):
        df_os = self._combine_compare_csv_files(self.os_cl)
        df_dqs = self._combine_compare_csv_files(self.dqs_cl)
        if df_os is not None:
            filen.write("OS checklist completed at (Local time):")
            filen.write("\n\n")
            for index, row in df_os.iterrows():
                if not pd.isna(row['Comment']):
                    if str(row['Comment']) not in ['',' ','nan','None']:
                        filen.write("* {} - {}\n".format(self.write_time(row['Time'], kp_only=True), row['Comment']))
                else:
                    filen.write("* {}\n".format(self.write_time(row['Time'],kp_only=True)))
            filen.write("\n")
            filen.write("\n")

        if df_dqs is not None:
            filen.write("DQS checklist completed at (Local time):")
            filen.write("\n\n")
            for index, row in df_dqs.iterrows():
                if not pd.isna(row['Comment']):
                    if str(row['Comment']) not in ['',' ','nan','None']:
                       filen.write("* {} - {}\n".format(self.write_time(row['Time'], kp_only=True), row['Comment']))
                else:
                    filen.write("* {}\n".format(self.write_time(row['Time'],kp_only=True)))
            filen.write("\n")
            filen.write("\n")

    def write_weather(self, filen):
        """Operations Scientist adds information regarding the weather.
        """
        df = self._combine_compare_csv_files(self.weather)
        if df is not None:
            for index, row in df.iterrows():
                filen.write("* {} - {}".format(self.write_time(row['Time'], kp_only=True), row['desc']))
                filen.write("; Temp: {:.2f}, Wind Speed: {:.2f}, Humidity: {:.2f}".format(float(row['temp']), float(row['wind']), float(row['humidity'])))
                filen.write(", Seeing: {:.2f}, Tput: {:.2f}, Sky: {:.2f}".format(float(row['seeing']), float(row['tput']), float(row['skylevel'])))
                filen.write("\n")

    def write_problem(self, filen):
        df_os = self._combine_compare_csv_files(self.os_pb)
        df_dqs = self._combine_compare_csv_files(self.dqs_pb)
        df_oth = self._combine_compare_csv_files(self.other_pb)
        dfs = [d for d in [df_os, df_dqs, df_oth] if d is not None]

        if len(dfs) > 0:
            if len(dfs) > 1:
                df = pd.concat(dfs)
            else:
                df = dfs[0]
            df = df.sort_values(by=['Time'])

            for index, row in df.iterrows():  
                filen.write("- {} := ".format(self.write_time(row['Time'])))
                if row['user'] == 'DQS':
                    filen.write('*')
                if row['user'] == 'Other':
                    filen.write('_')
                if not pd.isna(row['Problem']): # not in [np.nan, 'nan',None, 'None', " ", ""]:
                    filen.write("{}".format(row['Problem']))
                if not pd.isna(row['alarm_id']): # not in [float(np.nan), 'nan',None, 'None', " ", ""]:
                    if str(row['alarm_id']) not in ['nan','None','',' ']:
                        filen.write('; AlarmID: {}'.format(int(row['alarm_id'])))
                if not pd.isna(row['action']):
                    if str(row['action']) not in ['nan','None', " ", ""]:
                        filen.write('; Action: {}'.format(row['action']))
                if row['user'] == 'DQS':
                    filen.write('*')
                if row['user'] == 'Other':
                    filen.write(' ({})'.format(row['name']))
                    filen.write('_')
                if str(row['img_name']) not in [None,np.nan,'nan','',' ']:
                    self._write_image_tag(filen, row['img_name'])
                filen.write('\n')

    def check_exp_times(self, file):
        if os.path.exists(file):
            df = pd.read_csv(file)
            if os.path.exists(self.explist_file):
                exp_df = pd.read_csv(self.explist_file)
                for index, row in df.iterrows():
                    try:
                        e_ = exp_df[exp_df.id == int(row['Exp_Start'])]
                        time = pd.to_datetime(e_.date_obs).dt.strftime('%Y%m%dT%H:%M').values[0]  
                        df.at[index, 'Time'] = time
                    except:
                        pass
                df.to_csv(file,index=False)

    def write_exposure(self, file):
        if os.path.exists(self.explist_file):
            exp_df = pd.read_csv(self.explist_file)

        for f in [self.os_exp, self.dqs_exp, self.other_exp]:
            self.check_exp_times(f)

        os_df = self._combine_compare_csv_files(self.os_exp)
        dqs_df = self._combine_compare_csv_files(self.dqs_exp)
        other_df = self._combine_compare_csv_files(self.other_exp)

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
                os_ = os_.iloc[0]
                if str(os_['Exp_Start']) not in [np.nan, None, 'nan', 'None','',' ']:
                    file.write("- {} Exp. {} := {}\n".format(self.write_time(os_['Time']), int(os_['Exp_Start']), os_['Comment']))

                    if str(os_['img_name']) not in [np.nan, None, 'nan', 'None','',' ']:
                        self._write_image_tag(file, os_['img_name'])
                        file.write('\n')

                    if len(dqs_) > 0:
                        dqs_ = dqs_.iloc[0]
                        file.write(f"*Data Quality:* {dqs_['Quality']}; {dqs_['Comment']}\n")
                        if str(dqs_['img_name']) not in ['nan', 'None']:
                            self._write_image_tag(file, dqs_['img_name'])
                            file.write('\n')
                    if len(other_) > 0:
                        other_ = other_.iloc[0]
                        file.write("_Comment:_ {} ({})\n".format(other_['Comment'], other_['Name']))
                        if str(other_['img_name']) not in ['nan', 'None']:
                            self._write_image_tag(file, other_['img_name'])
                            file.write('\n')
                    try:
                        this_exp = exp_df[exp_df.id == int(os_['Exp_Start'])]
                        this_exp = this_exp.fillna(value=np.nan)
                        this_exp = this_exp.iloc[0]
                        try:
                            file.write(f"Tile {int(this_exp['tileid'])}, ")
                        except:
                            pass
                        try:
                            if not pd.isna(float(this_exp['exptime'])):
                                file.write(f"Exptime: {:.2f}, ".format(float(this_exp['exptime'])))
                        except:
                            pass
                        try:
                            if not pd.isna(float(this_exp['airmass'])):
                                file.write(f"Airmass: {:.2f}, ".format(float(this_exp['airmass'])))
                        except:
                            pass
                        file.write(f"Sequence: {this_exp['sequence']}, Flavor: {this_exp['flavor']}, Program {this_exp['program']}\n")

                    except:
                        file.write("\n")

                else:
                    file.write("- {} := {}\n".format(self.write_time(os_['Time']), os_['Comment']))


                

            else:
                if len(dqs_) > 0:
                    dqs_ = dqs_.iloc[0]
                    file.write("- {} Exp. {} := *Data Quality:* {}, {}\n".format(self.write_time(dqs_['Time']), int(dqs_['Exp_Start']), dqs_['Quality'],dqs_['Comment']))

                    if str(dqs_['img_name']) not in [np.nan, None, 'nan', 'None','',' ']:
                            self._write_image_tag(file, dqs_['img_name'])
                            file.write('\n')

                    if len(other_) > 0:
                        other_ = other_.iloc[0]
                        file.write("_Comment:_ {} ({})\n".format(other_['Comment'], other_['Name']))
                        if str(other_['img_name']) not in [np.nan, None, 'nan', 'None','',' ']:
                            self._write_image_tag(file, other_['img_name'])
                            file.write('\n')

                    try:
                        this_exp = exp_df[exp_df.id == dqs_['Exp_Start']]
                        this_exp = this_exp.fillna(value=np.nan)
                        this_exp = this_exp.iloc[0]
                        try:
                            file.write(f"Tile {int(this_exp['tileid'])}, ")
                        except:
                            pass
                        try:
                            if not pd.isna(float(this_exp['exptime'])):
                                file.write(f"Exptime: {:.2f}, ".format(float(this_exp['exptime'])))
                        except:
                            pass
                        try:
                            if not pd.isna(float(this_exp['airmass'])):
                                file.write(f"Airmass: {:.2f}, ".format(float(this_exp['airmass'])))
                        except:
                            pass
                        file.write(f"Sequence: {this_exp['sequence']}, Flavor: {this_exp['flavor']}, Program {this_exp['program']}\n")
                    except:
                        file.write("\n")

                else:
                    if len(other_) > 0:
                        other_ = other_.iloc[0]
                        if str(other_['Exp_Start']) not in [np.nan, None, 'nan', 'None','',' ']:
                            file.write("- {} Exp: {}:= _Comment:_ {} ({})\n".format(self.write_time(other_['Time']), int(other_['Exp_Start']), other_['Comment'], other_['Name']))
                        else:
                            file.write("- {} := _Comment:_ {} ({})\n".format(self.write_time(other_['Time']), other_['Comment'], other_['Name']))
                        if str(other_['img_name']) not in [np.nan, None, 'nan', 'None','',' ']:
                            self._write_image_tag(file, other_['img_name'])
                            file.write('\n')

    def load_index(self, idx, page):
        if page == 'milestone':
            the_path = self.milestone
        if page == 'plan':
            the_path = self.objectives
        df = self._combine_compare_csv_files(the_path)
        try:
            item = df[df.index == int(idx)]
            item = item.iloc[0]
            if len(item) > 0:
                return True, item
            else:
                return False, item
        except Exception as e:
            return False, e

    def load_exp(self, exp):
        the_path = self.dqs_exp

        df = self._combine_compare_csv_files(the_path)
        try:
            item = df[df.Exp_Start == exp]
            item = item.iloc[0]
            if len(item) > 0:
                return True, item
            else:
                return False, item
        except Exception as e:
            return False, e

    def load_timestamp(self, time, user, exp_type):

        if user == 'OS':
            files = {'exposure':self.os_exp, 'problem':self.os_pb}
        elif user == 'DQS':
            _dir = {'exposure':self.dqs_exp, 'problem':self.dqs_pb}
        elif user == 'Other':
            _dir = {'exposure':self.other_exp, 'problem':self.other_pb}

        the_path = files[exp_type]

        df = self._combine_compare_csv_files(the_path)
        try:
            item = df[df.Time == time]
            item = item.iloc[0]

            if len(item) > 0:
                return True, item
            else:
                return False, item
        except Exception as e:
            return False, e

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
        df = df.fillna(value=0)
        d = df.iloc[0]
        obs_time, test_time, inst_loss, weather_loss, tel_loss, total, deg_18 = d['obs_time'], d['test_time'], d['inst_loss'], d['weather_loss'], d['tel_loss'], d['total'], d['18deg']

        file = open(self.summary_file, 'w')

        if d['summary_1'] not in [np.nan, None, 'nan', 'None','',' ']:
            file.write(d['summary_1'])
            file.write("\n")
        if d['summary_2'] not in [np.nan, None, 'nan', 'None','',' ']:
            file.write(d['summary_2'])
            file.write("\n")
        file.write("Time Use (hrs):")
        file.write(" Observing: {:.2f}, Testing: {:.2f}, Loss to Instrument: {:.2f}, Loss to Weather: {:.2f}, Loss to Telescope: {:.2f}, Total: {:.2f}, Time between 18 deg. twilight: {:.2f}\n".format(float(obs_time), float(test_time), float(inst_loss), float(weather_loss), float(tel_loss), float(total), float(deg_18)))

        file.write("\n")
        file.close()

    def write_file(self, the_path, header,file_nl):
        if os.path.exists(the_path):
            with open(the_path, 'r') as f:
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
            f = self._open_kpno_file_first(self.meta_json)
            meta_dict = json.load(open(f,'r'))
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
            hfile = self._open_kpno_file_first(self.header_file)
            if hfile is not None:
                with open(hfile, 'r') as file_intro:
                    lines = file_intro.readlines()
                    for line in lines:
                        file_nl.write(line)
                    file_nl.write("\n")
                    file_nl.write("\n")
        except Exception as e:
            print("Exception with nightlog header: {}".format(e))

        #Contributers
        self.write_file(self._open_kpno_file_first(self.contributer_file), "h3. Contributers\n", file_nl)

        #Night Summary
        self.write_file(self._open_kpno_file_first(self.summary_file), "h3. Night Summary\n", file_nl)

        #Plan for the night
        file_nl.write("\n")
        file_nl.write("\n")
        file_nl.write("h3. Plan for the night\n")
        file_nl.write("\n")
        file_nl.write("The detailed operations plan for today (obsday "+self.obsday+") can be found at https://desi.lbl.gov/trac/wiki/DESIOperations/ObservingPlans/OpsPlan"+self.obsday+".\n")
        file_nl.write("\n")
        file_nl.write("Main items are listed below:\n")
        self.write_plan(file_nl)

        #Milestones/Accomplishments
        file_nl.write("\n")
        file_nl.write("\n")
        file_nl.write("h3. Milestones and Major Progress\n")
        file_nl.write("\n")
        file_nl.write("\n")
        self.write_milestone(file_nl)

        #Problems
        file_nl.write("\n")
        file_nl.write("\n")
        file_nl.write("h3. Problems and Operations Issues [OS, *DQS*, _Other_]\n")
        self.write_problem(file_nl)

        #Weather
        file_nl.write("\n")
        file_nl.write("\n")
        file_nl.write("h3. Observing Conditions\n")
        self.write_weather(file_nl)
        file_nl.write("\n")
        file_nl.write("\n")

        #Checklists
        file_nl.write("\n")
        file_nl.write("\n")
        file_nl.write("h3. Checklists\n")
        file_nl.write("\n")
        file_nl.write("\n")
        self.write_checklist(file_nl)

        #Nightly Progress
        file_nl.write("h3. Details on the Night Progress\n")
        file_nl.write("\n")
        file_nl.write("\n")
        self.write_exposure(file_nl)

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
