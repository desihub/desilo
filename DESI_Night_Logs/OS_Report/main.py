"""
Created on May 21, 2020

@author: Parker Fagrelius

start server with the following command:

bokeh serve --show OS_Report

view at: http://localhost:5006/OS_Report
"""

import os, sys
import time
import pandas as pd
import subprocess

from bokeh.io import curdoc
from bokeh.plotting import save
from bokeh.models import TextInput, ColumnDataSource, Button, TextAreaInput, Select
from bokeh.models.widgets.markups import Div
from bokeh.models.widgets.tables import DataTable, TableColumn, NumberEditor, StringEditor, PercentEditor
from bokeh.layouts import layout, column, row
from bokeh.models.widgets import Panel, Tabs
from bokeh.themes import built_in_themes
from bokeh.models import CustomJS
from bokeh.plotting import figure

sys.path.append(os.getcwd())
sys.path.append('./ECLAPI-8.0.12/lib')
#os.environ["NL_DIR"] = "/n/home/desiobserver/parkerf/desilo/nightlogs" #"/Users/pfagrelius/Research/DESI/Operations/NightLog/nightlogs"
import nightlog as nl
from report import Report

# sys.stdout = open(os.environ['NL_DIR']+'/out.txt', 'a')
# print('test')

class OS_Report(Report):
    def __init__(self):
        Report.__init__(self, 'OS')

        self.title = Div(text="DESI Nightly Intake - Operating Scientist", css_classes=['h1-title-style'], width=1000)# width=800, style={'font-size':'24pt','font-style':'bold'})
        desc = """
        The Operating Scientist (OS) is responsible for initializing the Night Log. Connect to an existing Night Log using the date or initialize tonight's log.
        Throughout the night, enter information about the exposures, weather, and problems. Complete the OS Checklist at least once every hour.
        """
        self.instructions = Div(text=desc+self.time_note.text, css_classes=['inst-style'], width=500)
        self.line = Div(text='-----------------------------------------------------------------------------------------------------------------------------', width=1000)
        self.line2 = Div(text='-----------------------------------------------------------------------------------------------------------------------------', width=1000)
        self.init_bt = Button(label="Initialize Tonight's Log", css_classes=['init_button'])
        self.LO = Select(title='Lead Observer', value='Choose One', options=self.lo_names)
        self.OA = Select(title='Observing Assistant', value='Choose One', options=self.oa_names)
        self.page_logo = Div(text="<img src='OS_Report/static/logo.png'>", width=350, height=300)

        self.contributer_list = TextAreaInput(placeholder='Contributer names (include all)', rows=2, cols=3, title='Names of all Contributers')
        self.contributer_btn = Button(label='Update Contributer List', css_classes=['add_button'], width=300)

        self.connect_hdr = Div(text="Connect to Existing Night Log", css_classes=['subt-style'], width=800)
        self.init_hdr = Div(text="Initialize Tonight's Night Log", css_classes=['subt-style'], width=800)
        self.check_subtitle = Div(text="OS Checklist", css_classes=['subt-style'])
        self.checklist_inst = Div(text="Every hour, the OS is expected to monitor several things. After completing these tasks, record at what time they were completed. Be honest please!", css_classes=['inst-style'], width=1000)
        self.os_checklist = ["Did you check the weather?", "Did you check the guiding?", "Did you check the positioner temperatures?","Did you check the FXC?", "Did you check the Cryostat?", "Did you do a connectivity aliveness check?","Did you check the Spectrograph Chiller?"]

        self.nl_submit_btn = Button(label='Submit NightLog & Publish Nightsum', width=300, css_classes=['add_button'])
        self.header_options = ['Startup','Calibration (Arcs/Twilight)','Focus','Observation','Other Acquisition','Comment']

    def get_layout(self):
        intro_layout = layout([self.title,
                            [self.page_logo, self.instructions],
                            self.connect_hdr,
                            [self.date_init, self.connect_bt],
                            self.connect_txt,
                            self.line,
                            self.init_hdr,
                            [[self.os_name_1, self.os_name_2], self.LO, self.OA],
                            [self.init_bt],
                            self.line2,
                            self.contributer_list,
                            self.contributer_btn,
                            self.nl_info,
                            self.intro_txt], width=1000)
        intro_tab = Panel(child=intro_layout, title="Initialization")

        self.get_nl_layout()
        self.get_milestone_layout()
        self.get_plan_layout()
        self.get_os_exp_layout()
        self.get_prob_layout()
        self.get_checklist_layout()
        self.get_weather_layout()
        self.check_tab.title = 'OS Checklist'

        self.layout = Tabs(tabs=[intro_tab, self.plan_tab, self.milestone_tab, self.exp_tab, self.prob_tab, self.weather_tab, self.check_tab,  self.nl_tab], css_classes=['tabs-header'], sizing_mode="scale_both")

    def run(self):
        self.get_layout()
        self.time_tabs = [None, None, None, self.exp_time, self.prob_time, None, None, None]
        self.now_btn.on_click(self.time_is_now)
        self.init_bt.on_click(self.initialize_log)
        self.connect_bt.on_click(self.connect_log)
        self.exp_btn.on_click(self.progress_add)
        self.exp_load_btn.on_click(self.load_exposure)
        self.prob_load_btn.on_click(self.load_problem)

        self.weather_btn.on_click(self.weather_add)
        self.prob_btn.on_click(self.prob_add)
        #self.nl_btn.on_click(self.current_nl)
        self.nl_submit_btn.on_click(self.nl_submit)
        self.check_btn.on_click(self.check_add)
        self.milestone_btn.on_click(self.milestone_add)
        self.milestone_new_btn.on_click(self.milestone_add_new)
        self.milestone_load_btn.on_click(self.milestone_load)
        self.plan_btn.on_click(self.plan_add)
        self.plan_new_btn.on_click(self.plan_add_new)
        self.plan_load_btn.on_click(self.plan_load)
        self.img_btn.on_click(self.image_add)
        self.contributer_btn.on_click(self.add_contributer_list)
        self.summary_btn.on_click(self.add_summary)
        
        

    
OS = OS_Report()
OS.run()
curdoc().theme = 'dark_minimal'
curdoc().title = 'DESI Night Log - Observing Scientist'
curdoc().add_root(OS.layout)
curdoc().add_periodic_callback(OS.current_nl, 30000)
