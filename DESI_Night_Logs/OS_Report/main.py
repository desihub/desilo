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

sys.path.append(os.getcwd())
sys.path.append('./ECLAPI-8.0.12/lib')
#os.environ["NL_DIR"] = "/Users/pfagrelius/Research/DESI/Operations/NightLog/nightlogs"
import nightlog as nl
from report import Report

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
        self.checklist.labels = ["Did you check the weather?", "Did you check the guiding?", "Did you check the positioner temperatures?","Did you check the FXC?", "Did you check the Cryostat?", "Did you do a connectivity aliveness check?","Did you check the Spectrograph Chiller?"]

        self.nl_submit_btn = Button(label='Submit NightLog & Publish Nightsum', width=300, css_classes=['add_button'])
        self.header_options = ['Startup','Calibration (Arcs/Twilight)','Focus','Observation','Other Acquisition','Comment']

        self.summary = TextAreaInput(rows=4, cols=4, title='End of Night Summary')
        self.summary_btn = Button(label='Add Summary', css_classes=['add_button'])

    def plan_tab(self):
        self.plan_subtitle = Div(text="Night Plan", css_classes=['subt-style'])
        self.plan_inst = Div(text="Input the major elements of the Night Plan found at the link below in the order expected for their completion.", css_classes=['inst-style'], width=1000)
        self.plan_txt = Div(text='<a href="https://desi.lbl.gov/trac/wiki/DESIOperations/ObservingPlans/">Tonights Plan Here</a>', css_classes=['inst-style'], width=500)
        self.plan_order = TextInput(title ='Expected Order:', placeholder='1', value=None)
        self.plan_input = TextAreaInput(placeholder="description", rows=8, cols=3, title="Describe item of the night plan:")
        self.plan_btn = Button(label='Add', css_classes=['add_button'])
        self.plan_alert = Div(text=' ', css_classes=['alert-style'])

    def milestone_tab(self):
        self.milestone_subtitle = Div(text="Milestones & Major Accomplishments", css_classes=['subt-style'])
        self.milestone_inst = Div(text="Record any major milestones or accomplishments that occur throughout a night and the exposure numbers that correspond to it. If applicable, indicate the ID of exposures to ignore in a series.", css_classes=['inst-style'],width=1000)
        self.milestone_input = TextAreaInput(placeholder="Description", rows=10, cols=3)
        self.milestone_exp_start = TextInput(title ='Exposure Start', placeholder='12345', value=None)
        self.milestone_exp_end = TextInput(title='Exposure End', placeholder='12345', value=None)
        self.milestone_exp_excl = TextInput(title='Excluded Exposures', placeholder='12346', value=None)
        self.milestone_btn = Button(label='Add', css_classes=['add_button'])
        self.milestone_alert = Div(text=' ', css_classes=['alert-style'])

    def weather_tab(self):
        data = pd.DataFrame(columns = ['time','desc','temp','wind','humidity'])
        self.weather_source = ColumnDataSource(data)

        self.weather_subtitle = Div(text="Weather", css_classes=['subt-style'])

        columns = [TableColumn(field='time', title='Time (local)', width=75),
                   TableColumn(field='desc', title='Description', width=200, editor=StringEditor()),
                   TableColumn(field='temp', title='Temperature (C)', width=100, editor=NumberEditor()),
                   TableColumn(field='wind', title='Wind Speed (mph)', width=120, editor=NumberEditor()),
                   TableColumn(field='humidity', title='Humidity (%)', width=100, editor=PercentEditor())]
        self.weather_inst = Div(text="Every hour include a description of the weather and any other relevant information, as well as fill in all the fields below.  Click the Update Night Log button after every hour's entry. To update a cell: double click in it, record the information, click out of the cell.", width=1000, css_classes=['inst-style'])
        self.weather_time = TextInput(placeholder='17:00', value=None, width=100) #title='Time in Kitt Peak local time', 
        self.weather_desc = TextInput(title='Description', placeholder='description', value=None)
        self.weather_temp = TextInput(title='Temperature (C)', placeholder='50', value=None)
        self.weather_wind = TextInput(title='Wind Speed (mph)', placeholder='10', value=None)
        self.weather_humidity = TextInput(title='Humidity (%)', placeholder='5', value=None)
        self.weather_table = DataTable(source=self.weather_source, columns=columns)
        self.weather_btn = Button(label='Add Weather', css_classes=['add_button'])

    def exp_tab(self):
        self.exp_subtitle = Div(text="Nightly Progress", css_classes=['subt-style'])
        self.exp_inst = Div(text="Throughout the night record the progress, including comments on Calibrations and Exposures. All exposures are recorded in the eLog, so only enter information that can provide additional information.", width=800, css_classes=['inst-style'])
        self.hdr_type = Select(title="Observation Type", value='Observation', options=self.header_options)
        self.hdr_btn = Button(label='Select', css_classes=['add_button'])

        self.add_image = TextInput(title="Add Image", placeholder='Pictures/image.png', value=None)

        self.exp_script = TextInput(title='Script Name', placeholder='dithering.json', value=None)
        self.exp_time_end = TextInput(title='Time End', placeholder='20:07', value=None)
        self.exp_focus_trim = TextInput(title='Trim from Focus', placeholder='54', value=None)
        self.exp_tile = TextInput(title='Tile Number', placeholder='68001', value=None)
        self.exp_tile_type = Select(title="Tile Type", value=None, options=['QSO','LRG','ELG','BGS','MW'])
        self.exp_input_layout = layout([])

    def choose_exposure(self):
        if self.hdr_type.value == 'Focus':
            self.exp_input_layout = layout([
                     [self.time_title, self.exp_time, self.now_btn],
                     [self.exp_exposure_start, self.exp_exposure_finish],
                     [self.exp_comment],
                     [self.exp_script],
                     [self.exp_focus_trim],
                     [self.exp_btn]])
        elif self.hdr_type.value in ['Startup','Comment']:
            self.exp_input_layout = layout([
                     [self.time_title, self.exp_time, self.now_btn],
                     [self.exp_comment],
                     [self.exp_btn]])
        elif self.hdr_type.value == 'Calibration (Arcs/Twilight)':
            self.exp_input_layout = layout([
                     [self.time_title, self.exp_time, self.now_btn],
                     [self.exp_exposure_start, self.exp_exposure_finish],
                     [self.exp_comment],
                     [self.exp_type],
                     [self.exp_script],
                     [self.exp_btn]])
        elif self.hdr_type.value in ['Observation', 'Other Acquisition']:
            self.exp_input_layout = layout([
                     [self.time_title, self.exp_time, self.now_btn],
                     [self.exp_exposure_start, self.exp_exposure_finish],
                     [self.exp_comment],
                     [self.exp_tile_type],
                     [self.exp_tile],
                     [self.exp_script],
                     [self.exp_btn]])
        self.exp_layout.children[6] = self.exp_input_layout

    def get_layout(self):
        intro_layout = layout([self.title,
                            [self.page_logo, self.instructions],
                            self.connect_hdr,
                            [self.date_init, self.connect_bt],
                            self.connect_txt,
                            self.line,
                            self.init_hdr,
                            [self.your_name, self.LO, self.OA],
                            [self.init_bt],
                            self.line2,
                            self.contributer_list,
                            self.contributer_btn,
                            self.nl_info,
                            self.intro_txt], width=1000)
        intro_tab = Panel(child=intro_layout, title="Initialization")

        plan_layout = layout([self.title,
                            self.plan_subtitle,
                            self.plan_inst,
                            self.plan_txt,
                            [self.plan_order, self.plan_input],
                            [self.plan_btn],
                            self.plan_alert], width=1000)
        plan_tab = Panel(child=plan_layout, title="Night Plan")

        milestone_layout = layout([self.title,
                                self.milestone_subtitle,
                                self.milestone_inst,
                                self.milestone_input,
                                [self.milestone_exp_start,self.milestone_exp_end, self.milestone_exp_excl],
                                [self.milestone_btn],
                                self.summary,
                                self.summary_btn,
                                self.milestone_alert], width=1000)
        milestone_tab = Panel(child=milestone_layout, title='Milestones')

        self.exp_layout = layout(children=[self.title,
                                self.exp_subtitle,
                                self.exp_inst,
                                self.time_note,
                                self.exp_info,
                                [self.hdr_type, self.hdr_btn],
                                self.exp_input_layout,
                                self.exp_alert], width=1000)
        exp_tab = Panel(child=self.exp_layout, title="Nightly Progress")

        weather_layout = layout([self.title,
                                self.weather_subtitle,
                                self.weather_inst,
                                self.time_note,
                                [self.time_title, self.weather_time, self.now_btn], 
                                [self.weather_desc, self.weather_temp],
                                [self.weather_wind, self.weather_humidity, self.weather_btn],
                                self.weather_table], width=1000)
        weather_tab = Panel(child=weather_layout, title="Weather")

        self.get_nl_layout()
        nl_layout = layout([self.title,
                self.nl_subtitle,
                self.nl_alert,
                self.nl_text,
                self.exptable_alert,
                self.exp_table,
                self.nl_submit_btn], width=1000)
        nl_tab = Panel(child=nl_layout, title="Current DESI Night Log")

        self.get_prob_layout()
        self.get_checklist_layout()
        self.get_img_layout()
        self.check_tab.title = 'OS Checklist'

        self.layout = Tabs(tabs=[intro_tab, plan_tab, milestone_tab, exp_tab, weather_tab, self.prob_tab, self.check_tab, self.img_tab, nl_tab], css_classes=['tabs-header'], sizing_mode="scale_both")

    def run(self):
        self.plan_tab()
        self.milestone_tab()
        self.exp_tab()
        self.weather_tab()
        self.time_tabs = [None, None, None, self.exp_time, self.weather_time, self.prob_time, None, None]
        self.now_btn.on_click(self.time_is_now)
        self.init_bt.on_click(self.initialize_log)
        self.connect_bt.on_click(self.connect_log)
        self.exp_btn.on_click(self.progress_add)
        self.hdr_btn.on_click(self.choose_exposure)
        self.weather_btn.on_click(self.weather_add)
        self.prob_btn.on_click(self.prob_add)
        #self.nl_btn.on_click(self.current_nl)
        self.nl_submit_btn.on_click(self.nl_submit)
        self.check_btn.on_click(self.check_add)
        self.milestone_btn.on_click(self.milestone_add)
        self.plan_btn.on_click(self.plan_add)
        self.img_btn.on_click(self.image_add)
        self.contributer_btn.on_click(self.add_contributer_list)
        self.summary_btn.on_click(self.add_summary)
        
        self.get_layout()

    
OS = OS_Report()
OS.run()
curdoc().theme = 'dark_minimal'
curdoc().title = 'DESI Night Log - Observing Scientist'
curdoc().add_root(OS.layout)
curdoc().add_periodic_callback(OS.current_nl, 30000)
