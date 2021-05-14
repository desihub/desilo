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
from collections import OrderedDict

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

        self.header_html = os.path.join(self.root_dir,'header_{}.html'.format(self.location))
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
        self.bad_exp_list = os.path.join(self.root_dir,'bad_exp_list_{}.csv'.format(self.location))

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
        items = ['LO_firstname_1','LO_lastname_1','LO_firstname_2','LO_lastname_2','OA_firstname','OA_lastname',
        'os_1_firstname','os_1_lastname','os_2_firstname','os_2_lastname',
        'dqs_1_firstname','dqs_1_lastname','dqs_2_firstname','dqs_2_lastname',
        'time_sunset','time_sunrise','time_moonrise','time_moonset','illumination',
        'dusk_18_deg','dawn_18_deg','dusk_12_deg','dawn_12_deg','dqs_1','dqs_last']
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

    def _combine_compare_csv_files(self, filen, bad=False):
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
            if bad==False:
                df_ = df_.sort_values(by=['Time'])
                df_.reset_index(inplace=True, drop=True)
            elif bad == True:
                df_ = df_.sort_values(by=['EXPID'])
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

    def delete_item(self, time, tab, user=None):
        if tab == 'plan':
            file = self.objectives
        if tab == 'milestone':
            file = self.milestone
        if tab == 'problem':
            pb_files = {'OS':self.os_pb,'DQS':self.dqs_pb,'Other':self.other_pb}
            file = pb_files[user]
        if tab == 'progress':
            exp_files = {'OS':self.os_exp,'Other':self.other_exp}
            file = exp_files[user]

        df = pd.read_csv(file)
        idx = df[df.Time == time].index[0]
        df = df.drop([idx])
        df.reset_index(inplace=True, drop=True)
        df.to_csv(file, index=False)

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
            filen.write("<ul>")
            for index, row in df.iterrows():
                filen.write("<li> [{}] {}</li>".format(index, row['Objective']))
            filen.write("</ul>")

    def write_milestone(self, filen):
        df = self._combine_compare_csv_files(self.milestone)
        if df is not None:
            df = df.drop_duplicates(['Time'], keep='first')
            df.reset_index(inplace=True, drop=True)
            filen.write("<ul>")
            for index, row in df.iterrows():
                filen.write("<li> [{}] {}".format(index, row['Desc']))
                if not pd.isna(row['Exp_Start']):
                    if str(row['Exp_Start']) not in ['',' ','nan']:
                        filen.write("; Exposure(s): {}".format(row['Exp_Start']))
                if not pd.isna(row['Exp_Stop']):  
                    if str(row['Exp_Stop']) not in ['',' ','nan']:
                        filen.write(" - {}".format(row['Exp_Stop']))
                if not pd.isna(row['Exp_Excl']):
                    if str(row['Exp_Excl']) not in ['',' ','nan']:
                        filen.write(", excluding {}".format(row['Exp_Excl']))
                filen.write("</li>")
            filen.write("</ul>")


    def write_checklist(self, filen):
        df_os = self._combine_compare_csv_files(self.os_cl)
        df_dqs = self._combine_compare_csv_files(self.dqs_cl)
        if df_os is not None:
            filen.write("OS checklist completed at (Local time):")
            filen.write("<br/>")
            filen.write("<ul>")
            for index, row in df_os.iterrows():
                if (not pd.isna(row['Comment'])) & (str(row['Comment']) not in ['',' ','nan','None']):
                       filen.write("<li> {} - {}</li>".format(self.write_time(row['Time'], kp_only=True), row['Comment']))
                else:
                    filen.write("<li> {}</li>".format(self.write_time(row['Time'],kp_only=True)))
            filen.write("</ul>")

        if df_dqs is not None:
            filen.write("DQS checklist completed at (Local time):")
            filen.write("<br/>")
            filen.write("<ul>")
            for index, row in df_dqs.iterrows():
                if (not pd.isna(row['Comment'])) & (str(row['Comment']) not in ['',' ','nan','None']):
                       filen.write("<li> {} - {}</li>".format(self.write_time(row['Time'], kp_only=True), row['Comment']))
                else:
                    filen.write("<li> {}</li>".format(self.write_time(row['Time'],kp_only=True)))
            filen.write("</ul>")

    def write_weather(self, filen):
        """Operations Scientist adds information regarding the weather.
        """
        df = self._combine_compare_csv_files(self.weather)
        if df is not None:
            df = df.rename(columns={'desc':'Description','temp':'Temp.','wind':'Wind Speed (mph)','humidity':'Humidity','seeing':'Seeing','tput':'Transparency','skylevel':'SkyLevel'})
            df_list = df.to_html(index=False, justify='center',float_format='%.2f',na_rep='-',classes='weathertable',max_cols=8)
            for line in df_list:
                filen.write(line)

    def write_problem(self, filen):
        df_os = self._combine_compare_csv_files(self.os_pb)
        df_dqs = self._combine_compare_csv_files(self.dqs_pb)
        df_oth = self._combine_compare_csv_files(self.other_pb)
        dfs = [d for d in [df_os, df_dqs, df_oth] if d is not None]
        self.prob_df = None
        if len(dfs) > 0:
            if len(dfs) > 1:
                df = pd.concat(dfs)
            else:
                df = dfs[0]
            self.prob_df = df.sort_values(by=['Time'])

            for index, row in self.prob_df.iterrows():  
                filen.write("<b>{}</b> ".format(self.write_time(row['Time'])))
                if not pd.isna(row['Problem']): # not in [np.nan, 'nan',None, 'None', " ", ""]:
                    filen.write("{}".format(row['Problem']))
                if not pd.isna(row['alarm_id']): # not in [float(np.nan), 'nan',None, 'None', " ", ""]:
                    if str(row['alarm_id']) not in ['nan','None','',' ']:
                        try:
                            filen.write('; AlarmID: {}'.format(int(row['alarm_id'])))
                        except:
                            filen.write('; AlarmID: {}'.format(str(row['alarm_id'])))
                if not pd.isna(row['action']):
                    if str(row['action']) not in ['nan','None', " ", ""]:
                        filen.write('; Action: {}'.format(row['action']))
                if row['user'] == 'Other':
                    filen.write(' ({})'.format(row['name']))
                if str(row['img_name']) not in [None,np.nan,'nan','',' ']:
                    self._write_image_tag(filen, row['img_name'])
                filen.write('<br/>')
                filen.write('<br/>')

    def check_exp_times(self, file):
        if os.path.exists(file):
            df = pd.read_csv(file)
            if os.path.exists(self.explist_file):
                exp_df = pd.read_csv(self.explist_file)
                for index, row in df.iterrows():
                    try:
                        e_ = exp_df[exp_df.id == int(row['Exp_Start'])]
                        time = pd.to_datetime(e_.date_obs).dt.strftime('%Y%m%dT%H:%M').values[0]  
                        if str(time) == 'nan': # in [np.nan,'nan']:
                            pass
                        else:
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

        df_full = {'os':os_df,'dqs':dqs_df,'other':other_df,'prob':self.prob_df}

        times = []
        for df in df_full.values():
            if df is not None:
                tt = list(df.Time)
                for t in tt:
                    if t is not None:
                        times.append(t)
        times = np.unique(times)

        for time in times:
            df_ = {}
            for x, d in df_full.items():
                if d is not None:
                    df_[x] = d[d.Time == time]
                else:
                    df_[x] = []
            #print(df_)
            got_exp = None
            if len(df_['os']) > 0:
                os_ = df_['os'].iloc[0]
                if str(os_['Exp_Start']) not in [np.nan, None, 'nan', 'None','',' ']:
                    got_exp = str(os_['Exp_Start'])
                    try:
                        file.write("<b>{} Exp. {}</b>  {}<br/>".format(self.write_time(os_['Time']), int(os_['Exp_Start']), os_['Comment']))
                    except:
                        file.write("<b>{} Exp. {}</b>  {}<br/>".format(self.write_time(os_['Time']), str(os_['Exp_Start']), os_['Comment']))
                else:
                    file.write("<b>{}</b> {}<br/>".format(self.write_time(os_['Time']), os_['Comment']))

                    if str(os_['img_name']) not in [np.nan, None, 'nan', 'None','',' ']:
                        self._write_image_tag(file, os_['img_name'])

            if len(df_['dqs']) > 0:
                dqs_ = df_['dqs'].iloc[0]
                if str(dqs_['Comment']) == 'nan':
                    comment = ''
                else
                    comment = str(dqs_['Comment'])
                if got_exp is not None:
                    file.write(f"<b><em>Data Quality:</em></b> {dqs_['Quality']}; {comment}<br/>")
                else:
                    got_exp = str(dqs_['Exp_Start'])
                    try:
                        file.write("<b>{} Exp. {}</b> <b><em>Data Quality:</em></b> {}, {}<br/>".format(self.write_time(dqs_['Time']), int(dqs_['Exp_Start']), dqs_['Quality'],comment))
                    except:
                        file.write("<b>{} Exp. {}</b> <b><em>Data Quality:</em></b> {}, {}<br/>".format(self.write_time(dqs_['Time']), str(dqs_['Exp_Start']), dqs_['Quality'],comment))

                if str(dqs_['img_name']) not in [np.nan, None, 'nan', 'None','',' ']:
                    self._write_image_tag(file, dqs_['img_name'])

            if len(df_['other']) > 0:
                other_ = df_['other'].iloc[0]
                if got_exp is not None:
                    file.write("_Comment:_ {} ({})<br/>".format(other_['Comment'], other_['Name']))
                else:
                    if str(other_['Exp_Start']) not in [np.nan, None, 'nan', 'None','',' ']:
                        got_exp = str(other_['Exp_Start'])
                        try:
                            file.write("<b>{} Exp. {}</b> _Comment:_ {} ({})<br/>".format(self.write_time(other_['Time']), int(other_['Exp_Start']), other_['Comment'], other_['Name']))
                        except:
                            file.write("<b>{} Exp. {}</b> _Comment:_ {} ({})<br/>".format(self.write_time(other_['Time']), str(other_['Exp_Start']), other_['Comment'], other_['Name']))
                    else:
                        file.write("<b> {} </b> _Comment:_ {} ({})<br/>".format(self.write_time(other_['Time']), other_['Comment'], other_['Name']))

                if str(other_['img_name']) not in [np.nan, None, 'nan', 'None','',' ']:
                    self._write_image_tag(file, other_['img_name'])

            if len(df_['prob']) > 0:
                prob_ = df_['prob'].iloc[0]
                file.write("<b> {} </b> ".format(self.write_time(prob_['Time'])))
                if not pd.isna(prob_['Problem']): # not in [np.nan, 'nan',None, 'None', " ", ""]:
                    file.write("{}".format(prob_['Problem']))
                if not pd.isna(prob_['alarm_id']): # not in [float(np.nan), 'nan',None, 'None', " ", ""]:
                    if str(prob_['alarm_id']) not in ['nan','None','',' ']:
                        try:
                            file.write('; AlarmID: {}'.format(int(prob_['alarm_id'])))
                        except:
                            file.write('; AlarmID: {}'.format(str(prob_['alarm_id'])))
                if not pd.isna(prob_['action']):
                    if str(prob_['action']) not in ['nan','None', " ", ""]:
                        file.write('; Action: {}'.format(prob_['action']))
                if prob_['user'] == 'Other':
                    file.write(' ({})'.format(prob_['name']))
                if str(prob_['img_name']) not in [None,np.nan,'nan','',' ']:
                    self._write_image_tag(file, prob_['img_name'])
                file.write('<br/>')

            if got_exp is not None:
                got_exp = float(got_exp)
                try:
                    got_exp = int(got_exp)
                    this_exp = exp_df[exp_df.id == int(got_exp)]
                    this_exp = this_exp.fillna(value=np.nan)
                    this_exp = this_exp.iloc[0]
                    try:
                        file.write(f"Tile {int(this_exp['tileid'])}, ")
                    except:
                        pass
                    try:
                        if not pd.isna(float(this_exp['exptime'])):
                            file.write("Exptime: {:.2f}, ".format(float(this_exp['exptime'])))
                    except:
                        pass
                    try:
                        if not pd.isna(float(this_exp['airmass'])):
                            file.write("Airmass: {:.2f}, ".format(float(this_exp['airmass'])))
                    except:
                        pass
                    file.write(f"Sequence: {this_exp['sequence']}, Flavor: {this_exp['flavor']}, Program: {this_exp['program']}<br/>")

                except:
                    pass
            file.write('<br/>')

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
            files = {'exposure':self.dqs_exp, 'problem':self.dqs_pb}
        elif user == 'Other':
            files = {'exposure':self.other_exp, 'problem':self.other_pb}

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
        img_file.write("<br/>")
        #img_file.write("h5. %s<br/>" % img_name)
        img_file.write('<img src="%s/%s" width=%s height=%s alt="Uploaded image %s"><br/>' % (server,img_name,str(width),str(height),img_name))
        if isinstance(comments, str):
            img_file.write("<br>{}<br/>".format(comments))

    def add_contributer_list(self, contributers):
        file = open(self.contributer_file, 'w')
        file.write(contributers)
        file.write("<br/>")
        file.close()

    def add_summary(self, data):

        df = pd.DataFrame(data, index=[0])
        df.to_csv(self.time_use,index=False)
        df = df.fillna(value=0)
        d = df.iloc[0]

        obs_items  = OrderedDict({'Observing':d['obs_time'],'Testing':d['test_time'],'Loss to Instrument':d['inst_loss'],
            'Loss to Weather':d['weather_loss'],'Loss to Telescope':d['tel_loss'],'Total Recorded':d['total'],'Time between 18 deg. twilight':d['18deg']})
        file = open(self.summary_file, 'w')
        file.write("Time Use (hrs):<br/>")
        file.write("<ul>")
        for name, item in obs_items.items():
            if name == 'Time between 18 deg. twilight':
                try:
                    file.write("<li> {}: {:.3f}</li>".format(name, float(item)))
                except Exception as e:
                    print(e)
            else:
                if not pd.isna(item):
                    try:
                        file.write("<li> {}: {:.2f}</li>".format(name, float(item)))
                    except Exception as e:
                        print(e)
                else:
                    file.write("<li> {}: 0.0</li>".format(name))
        file.write("</ul>")
        if d['summary_1'] not in [np.nan, None, 'nan', 'None','',' ']:
            file.write(d['summary_1'])
            file.write("<br/>")
        if d['summary_2'] not in [np.nan, None, 'nan', 'None','',' ']:
            file.write(d['summary_2'])
            file.write("<br/>")

        
        file.close()

    def add_bad_exp(self, data):
        if not os.path.exists(self.bad_exp_list):
            df = pd.DataFrame(columns=['EXPID','BAD','BADCAMS','COMMENT'])
            df.to_csv(self.bad_exp_list, index=False)
        else:
            df = pd.read_csv(self.bad_exp_list)

        this_df = pd.DataFrame.from_dict(data)

        df = pd.concat([df, this_df])
        df = df.drop_duplicates(subset=['EXPID'], keep='last')
        df.to_csv(self.bad_exp_list, index=False)

    def write_bad_exp(self, file_nl):
        df = self._combine_compare_csv_files(self.bad_exp_list, bad=True)
        try:
            if len(df) > 0:
                file_nl.write("<h3> Bad Exposures</h3>")
                df_html = df.to_html(index=False, justify='center',float_format='%.2f',na_rep='-',classes='badtable',max_cols=4)
            for line in df_html:
                file_nl.write(line)
        except Exception as e:
            print(e)

    def write_intro(self):
        file_intro=open(self.header_html,'w')
        try:
            f = self._open_kpno_file_first(self.meta_json)
            meta_dict = json.load(open(f,'r'))

            if (meta_dict['LO_lastname_2'] == meta_dict['LO_lastname_1']) | (meta_dict['LO_firstname_2'] == 'None'):
                file_intro.write("<b>Lead Observer</b>: {} {}<br/>".format(meta_dict['LO_firstname_1'],meta_dict['LO_lastname_1']))
            else:
                file_intro.write("<b>Lead Observer 1</b>: {} {}<br/>".format(meta_dict['LO_firstname_1'],meta_dict['LO_lastname_1']))
                file_intro.write("<b>Lead Observer 2</b>: {} {}<br/>".format(meta_dict['LO_firstname_2'],meta_dict['LO_lastname_2']))
            if (meta_dict['os_2_lastname'] == meta_dict['os_1_lastname']) | (meta_dict['os_2_firstname'] == None):
                file_intro.write("<b>Observing Scientist (OS)</b>: {} {}<br/>".format(meta_dict['os_1_firstname'],meta_dict['os_1_lastname']))
            else:
                file_intro.write("<b>Observer (OS-1)</b>: {} {}<br/>".format(meta_dict['os_1_firstname'],meta_dict['os_1_lastname']))
                file_intro.write("<b>Observer (OS-2)</b>: {} {}<br/>".format(meta_dict['os_2_firstname'],meta_dict['os_2_lastname']))
            if (meta_dict['dqs_2_lastname'] == meta_dict['dqs_1_lastname']) | (meta_dict['dqs_2_firstname'] == None) | (meta_dict['dqs_2_firstname'] == ''):
                file_intro.write("<b>Data Quality Scientist (DQS)</b>: {} {}<br/>".format(meta_dict['dqs_1_firstname'],meta_dict['dqs_1_lastname']))
            else:
                file_intro.write("<b>Observer (DQS-1)</b>: {} {}<br/>".format(meta_dict['dqs_1_firstname'],meta_dict['dqs_1_lastname']))
                file_intro.write("<b>Observer (DQS-2)</b>: {} {}<br/>".format(meta_dict['dqs_2_firstname'],meta_dict['dqs_2_lastname']))

            file_intro.write("<b>Telescope Operator</b>: {} {}<br/>".format(meta_dict['OA_firstname'],meta_dict['OA_lastname']))
            file_intro.write("<b>Ephemerides in local time [UTC]</b>:")
            file_intro.write("<ul>")
            file_intro.write("<li> sunset: {}</li>".format(self.write_time(meta_dict['time_sunset'])))
            file_intro.write("<li> 12(o) twilight ends: {}</li>".format(self.write_time(meta_dict['dusk_12_deg'])))
            file_intro.write("<li> 18(o) twilight ends: {}</li>".format(self.write_time(meta_dict['dusk_18_deg'])))
            file_intro.write("<li> 18(o) twilight starts: {}</li>".format(self.write_time(meta_dict['dawn_18_deg'])))
            file_intro.write("<li> 12(o) twilight starts: {}</li>".format(self.write_time(meta_dict['dawn_12_deg'])))
            file_intro.write("<li> sunrise: {}</li>".format(self.write_time(meta_dict['time_sunrise'])))
            file_intro.write("<li> moonrise: {}</li>".format(self.write_time(meta_dict['time_moonrise'])))
            file_intro.write("<li> moonset: {}</li>".format(self.write_time(meta_dict['time_moonset'])))
            file_intro.write("<li> illumination: {}</li>".format(meta_dict['illumination']))
            file_intro.write("</ul>")

        except Exception as e:
            print('Exception reading meta json file: {}'.format(str(e)))

        file_intro.close()


    def finish_the_night(self):
        """
            Merge together all the different files into one '.txt' file to copy past on the eLog.
        """
        file_nl=open(self.nightlog_html, 'w')
        file_nl.write("<h1>DESI Night Summary %s</h1>" % str(self.obsday))

        #Write the meta_html here
        try:
            hfile = self._open_kpno_file_first(self.header_html)
            if hfile is not None:
                with open(hfile, 'r') as file_intro:
                    lines = file_intro.read()
                    for line in lines:
                        file_nl.write(line)
        except Exception as e:
            print("Nightlog Header has not been created: {}".format(e))

        #Contributers
        try:
            cfile = self._open_kpno_file_first(self.contributer_file)
            if cfile is not None:
                file_nl.write("<h3>Contributers</h3>")
                with open(cfile, 'r') as file_cont:
                    lines = file_cont.read()
                    for line in lines:
                        file_nl.write(line)
                file_nl.write("<br/>")
        except:
            pass

        #Night Summary
        try:
            cfile = self._open_kpno_file_first(self.summary_file)
            if cfile is not None:
                file_nl.write("<h3>Night Summary</h3>")
                with open(cfile, 'r') as file_cont:
                    lines = file_cont.read()
                    for line in lines:
                        file_nl.write(line)
                file_nl.write("<br/>")
        except:
            pass

        #Plan for the night
        file_nl.write("<h3>Plan for the night</h3>")
        file_nl.write("The detailed operations plan for today (obsday {}) can be found at https://desi.lbl.gov/trac/wiki/DESIOperations/ObservingPlans/OpsPlan{}.<br/>".format(self.obsday, self.obsday))
        file_nl.write("Main items are listed below:<br/>")
        self.write_plan(file_nl)

        #Milestones/Accomplishments
        file_nl.write("<h3>Milestones and Major Progress</h3>")
        self.write_milestone(file_nl)

        #Problems
        file_nl.write("<h3>Problems and Operations Issues</h3>")
        self.write_problem(file_nl)
        file_nl.write("<br/>")

        #Weather
        file_nl.write("<h3>Observing Conditions</h3>")
        self.write_weather(file_nl)
        file_nl.write("<br/>")

        #Checklists
        file_nl.write("<h3>Checklists</h3>")
        self.write_checklist(file_nl)
        file_nl.write("<br/>")

        #Nightly Progress
        file_nl.write("<h3> Details on the Night Progress</h3>")
        self.write_exposure(file_nl)
        file_nl.write("<br/>")

        self.write_bad_exp(file_nl)
        file_nl.write("<br/>")

        file_nl.close()

