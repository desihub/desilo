"""
Created on May 21, 2020

@author: Parker Fagrelius

start server with the following command from folder above this.
bokeh serve --show DQS_Report

view at: http://localhost:5006/DQS_Report
"""

import os, sys

from bokeh.io import curdoc  # , output_file, save
from bokeh.models import TextInput, Button, RadioGroup, Select
from bokeh.models.widgets.markups import Div
from bokeh.layouts import layout
from bokeh.models.widgets import Panel, Tabs

sys.path.append(os.getcwd())
import nightlog as nl
from report import Report


class DQS_Report(Report):
    def __init__(self):
        Report.__init__(self, 'DQS')

        self.title = Div(text="DESI Nightly Intake - Data QA Scientist", css_classes=['h1-title-style'], width=1000)
        self.instructions = Div(text="The Data Quality Scientist (DQS) is responsible for analyzing all exposures for their quality. You can connect to an existing Night Log that was created by the Observing Scientist. ", css_classes=['inst-style'], width=1000)
        self.page_logo = Div(text="<img src='DQS_Report/static/logo.png'>", width=350, height=300)

        self.check_subtitle = Div(text="DQS Checklist", css_classes=['subt-style'])
        self.checklist_inst = Div(text="Every hour, the DQS is expected to monitor several things. After completing tasks fill out this form and add any interesting observations.", css_classes=['inst-style'] ,width=1000)
        self.checklist.labels = ["Are all images being transferred to Night Watch?", "Did you check the observing conditions?", "Did you check the guiding?"]

        self.quality_list = ['Bad','OK','Good','Great']
        self.quality_btns = RadioGroup(labels=self.quality_list, active=2)

        # if self.location is in ['desi','nersc']:
        #     self.exp_list = 
        # else:
        #     self.exp_list = []
        # self.exp_option = Div(text='(1) Enter exposure number OR (2) Select from list')
        # self.exp_enter = TextInput(title='(1) Exposure Number', placeholder='12345', value=None)
        # self.exp_select = Select(title='(2) Select Exposures', value='Choose One', options=self.exp_list)

    def exp_tab(self):
        self.exp_subtitle = Div(text="Exposures", css_classes=['subt-style'])
        self.exp_inst = Div(text="For each exposure, collect information about what you observe on Night Watch (quality) and observing conditions using other tools", css_classes=['inst-style'], width=1000)

        self.quality_title = Div(text='Data Quality: ', css_classes=['inst-style'])
        
        self.obs_cond_comment = TextInput(title='Observing Conditions Comment/Remark', placeholder='Seeing stable at 0.8arcsec', value=None)
        self.inst_perf_comment = TextInput(title='Instrument Performance Comment/Remark', placeholder='Positioner Accuracy less than 10um', value=None)
        
        self.exp_select = Select(title='(1) Select Exposure')
        self.exp_enter = TextInput(title='(2) Enter Exposure', placeholder='12345', value=None))
        self.exp_update = Button(label='Update Selection List', button_type='primary')
        self.exp+option = RadioButton(options=['Select','Enter'], active=0)

        if self.location == 'other':
            self.exp_layout = layout([self.exp_time],
                                    [self.exp_exposure_start, self.exp_exposure_finish],
                                    [self.exp_type],
                                    [self.quality_title,self.quality_btns],
                                    [self.exp_comment],
                                    [self.obs_cond_comment],
                                    [self.inst_perf_comment],
                                    [self.exp_btn],
                                    [self.exp_alert])

        else:
            self.get_exposure_list()
            self.exp_layout = layout([self.exp_option, self.exp_select, self.exp_enter, self.exp_update],
                                    [self.exp_type],
                                    [self.quality_title, self.quality_btns],
                                    [self.exp_comment],
                                    [self.obs_cond_comment],
                                    [self.inst_perf_comment],
                                    [self.exp_btn],
                                    [self.exp_alert])

    def get_exposure_list(self):
        dir_ = self.nw_dir+'/'+self.date_init.value
        if not os.path.exists(dir_):
            print(dir_)
        else:
            exposures = []
            for path, subdirs, files in os.walk(dir_): 
                for s in subdirs: 
                    exposures.append(s)  
            self.exp_select.options = list(exposures)
            self.exp_select.value = exposures[0] 

    def exp_add(self):
        quality = self.quality_list[self.quality_btns.active]
        self.DESI_Log.dqs_add_exp([self.get_time(self.exp_time.value), self.exp_exposure_start.value, self.exp_type.value, quality, self.exp_comment.value, self.obs_cond_comment.value, self.inst_perf_comment.value, self.exp_exposure_finish.value])
        self.exp_alert.text = 'Last Exposure input {} at {}'.format(self.exp_exposure_start.value, self.exp_time.value)
        self.clear_input([self.exp_time, self.exp_exposure_start, self.exp_type, self.exp_comment, self.obs_cond_comment, self.inst_perf_comment, self.exp_exposure_finish])

    def get_layout(self):

        exp_layout = layout([self.title,
                            self.exp_subtitle,
                            self.exp_inst,
                            self.exp_info,
                            self.exp_layout], width=1000)
        exp_tab = Panel(child=exp_layout, title="Exposures") 

        self.get_intro_layout()
        self.get_prob_layout()
        self.get_checklist_layout()
        self.get_nl_layout()

        tabs = Tabs(tabs=[self.intro_tab, exp_tab, self.prob_tab, self.check_tab, self.nl_tab])

        self.layout = tabs

    def run(self):
        self.exp_tab()
        self.connect_bt.on_click(self.connect_log)
        self.exp_btn.on_click(self.exp_add)
        self.exp_update.on_click(self.get_exposure_list)
        self.prob_btn.on_click(self.prob_add)
        self.check_btn.on_click(self.check_add)
        self.nl_btn.on_click(self.current_nl) 
        self.get_layout()


DQS = DQS_Report()
DQS.run()
curdoc().title = 'DESI Night Log - Data QA Scientist'
curdoc().add_root(DQS.layout)

