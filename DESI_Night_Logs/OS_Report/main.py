"""
Created on May 21, 2020

@author: Parker Fagrelius

start server with the following command:

bokeh serve --show OS_Report

view at: http://localhost:5006/OS_Report
"""

import os, sys
import pandas as pd

from bokeh.io import curdoc
from bokeh.models import TextInput, ColumnDataSource, Button, TextAreaInput, Select
from bokeh.models.widgets.markups import Div
from bokeh.models.widgets.tables import DataTable, TableColumn, NumberEditor, StringEditor, PercentEditor
from bokeh.layouts import layout
from bokeh.models.widgets import Panel, Tabs

sys.path.append(os.getcwd())
import nightlog as nl
from report import Report

class OS_Report(Report):
    def __init__(self):
        Report.__init__(self, 'OS')

        self.title = Div(text="DESI Nightly Intake - Operating Scientist", width=800, style=self.title_style)
        self.instructions = Div(text="The Operating Scientist (OS) is responsible for initializing the Night Log. Do so below or connect to an existing Night Log using the date. Throughout the night, enter information about the exposures, weather, and problems. Complete the OS Checklist at least once every hour.", width=500, style=self.inst_style)

        self.init_bt = Button(label="Initialize Tonight's Log", button_type='primary')
        self.LO = Select(title='Lead Observer', value='Choose One', options=self.lo_names) 
        self.OA = Select(title='Observing Assistant', value='Choose One', options=self.oa_names) 

        self.check_subtitle = Div(text="OS Checklist", width=500, style=self.subt_style)
        self.checklist_inst = Div(text="Every hour, the OS is expected to monitor several things. After completing these tasks, record at what time they were completed. Be honest please!", width=800, style=self.inst_style)
        self.checklist.labels = ["Did you check the weather?", "Did you check the guiding?", "Did you check the focal plane?","Did you check the spectrographs?"]

        self.header_options = ['Startup','Calibration','Focus','Observation','Other']

    def plan_tab(self):
        self.plan_subtitle = Div(text="Night Plan", width=500, style=self.subt_style)
        self.plan_inst = Div(text="Input the major elements of the Night Plan found at the link below in the order expected for their completion.", width=800, style=self.inst_style)
        self.plan_txt = Div(text='<a href="https://desi.lbl.gov/trac/wiki/DESIOperations/ObservingPlans/">Tonights Plan Here</a>', style=self.inst_style)
        self.plan_order = TextInput(title ='Expected Order:', placeholder='1', value=None)
        self.plan_input = TextAreaInput(placeholder="description", rows=6, title="Describe item of the night plan:")
        self.plan_btn = Button(label='Add', button_type='primary')
        self.plan_alert = Div(text=' ', width=600, style=self.alert_style)

    def milestone_tab(self):
        self.milestone_subtitle = Div(text="Milestones & Major Accomplishments", width=500, style=self.subt_style)
        self.milestone_inst = Div(text="Record any major milestones or accomplishments that occur throughout a night and the exposure numbers that correspond to it. If applicable, indicate the ID of exposures to ignore in a series.", width=800, style=self.inst_style)
        self.milestone_input = TextAreaInput(placeholder="Description", rows=6)
        self.milestone_exp_start = TextInput(title ='Exposure Start', placeholder='12345', value=None)
        self.milestone_exp_end = TextInput(title='Exposure End', placeholder='12345', value=None)
        self.milestone_exp_excl = TextInput(title='Excluded Exposures', placeholder='12346', value=None)
        self.milestone_btn = Button(label='Add', button_type='primary')
        self.milestone_alert = Div(text=' ', width=600, style=self.alert_style)
        
    def weather_tab(self):
        data = pd.DataFrame(columns = ['time','desc','temp','wind','humidity'])
        self.weather_source = ColumnDataSource(data)

        self.weather_subtitle = Div(text="Weather", width=500, style=self.subt_style)

        columns = [TableColumn(field='time', title='Time (local)', width=100),
                   TableColumn(field='desc', title='Description', width=200, editor=StringEditor()),
                   TableColumn(field='temp', title='Temperature (C)', width=100, editor=NumberEditor()),
                   TableColumn(field='wind', title='Wind Speed (mph)', width=100, editor=NumberEditor()),
                   TableColumn(field='humidity', title='Humidity (%)', width=100, editor=PercentEditor())]
        self.weather_inst = Div(text="Every hour include a description of the weather and othe relevant information. Click the Update Night Log button after every hour's entry. To update a cell: double click in it, record the information, click out of the cell.", width=800, style=self.inst_style)
        self.weather_time = TextInput(title='Time', placeholder='17:00', value=None)
        self.weather_desc = TextInput(title='Description', placeholder='description', value=None)
        self.weather_temp = TextInput(title='Temperature (C)', placeholder='50', value=None)
        self.weather_wind = TextInput(title='Wind Speed (mph)', placeholder='10', value=None)
        self.weather_humidity = TextInput(title='Humidity (%)', placeholder='5', value=None)
        self.weather_table = DataTable(source=self.weather_source, columns=columns)
        self.weather_btn = Button(label='Add Weather', button_type='primary')

    def exp_tab(self):
        self.exp_subtitle = Div(text="Nightly Progress", width=500, style=self.subt_style)
        self.exp_inst = Div(text="Throughout the night record the progress, including comments on Calibrations and Exposures. All exposures are recorded in the eLog, so only enter information that can provide additional information.", width=800, style=self.inst_style)
        self.hdr_type = Select(title="Observation Type", value='Observation', options=self.header_options)
        self.hdr_btn = Button(label='Select', button_type='primary')

        self.add_image = TextInput(title="Add Image", placeholder='Pictures/image.png', value=None)

        self.exp_script = TextInput(title='Script Name', placeholder='dithering.json', value=None)
        self.exp_time_end = TextInput(title='Time End', placeholder='2007', value=None)
        self.exp_focus_trim = TextInput(title='Trim from Focus', placeholder='54', value=None)
        self.exp_tile = TextInput(title='Tile Number', placeholder='68001', value=None)
        self.exp_tile_type = Select(title="Tile Type", value='QSO', options=['QSO','LRG','ELG','BGS','MW'])
        self.exp_input_layout = layout([])

    def choose_exposure(self):
        if self.hdr_type.value == 'Focus':
            self.exp_input_layout = layout([
                     [self.exp_time],
                     [self.exp_exposure_start, self.exp_exposure_finish],
                     [self.exp_comment],
                     [self.exp_script],
                     [self.exp_focus_trim],
                     [self.exp_btn]])
        elif self.hdr_type.value == 'Startup':
            self.exp_input_layout = layout([
                     [self.exp_time],
                     [self.exp_comment],
                     [self.exp_btn]])
        elif self.hdr_type.value == 'Calibration':
            self.exp_input_layout = layout([
                     [self.exp_time],
                     [self.exp_exposure_start, self.exp_exposure_finish],
                     [self.exp_comment],
                     [self.exp_type],
                     [self.exp_script],
                     [self.exp_btn]])
        elif self.hdr_type.value in ['Observation', 'Other']:
            self.exp_input_layout = layout([
                     [self.exp_time],
                     [self.exp_exposure_start, self.exp_exposure_finish],
                     [self.exp_comment],
                     [self.exp_tile_type],
                     [self.exp_tile],
                     [self.exp_script],
                     [self.exp_btn]])       
        self.exp_layout.children[5] = self.exp_input_layout

    def get_layout(self):
        intro_layout = layout([[self.title],
                            [self.page_logo, self.instructions],
                            [self.intro_subtitle],
                            [self.intro_info],
                            [self.date_init, self.connect_bt],
                            [self.connect_txt],
                            [self.your_name, self.LO, self.OA],
                            [self.init_bt],
                            [self.nl_info],
                            [self.intro_txt]])
        intro_tab = Panel(child=intro_layout, title="Initialization")

        plan_layout = layout([[self.title],
                            [self.plan_subtitle],
                            [self.plan_inst],
                            [self.plan_txt],
                            [self.plan_order, self.plan_input],
                            [self.plan_btn],
                            [self.plan_alert]])
        plan_tab = Panel(child=plan_layout, title="Night Plan")

        milestone_layout = layout([[self.title],
                                [self.milestone_subtitle],
                                [self.milestone_inst],
                                [self.milestone_input],
                                [self.milestone_exp_start,self.milestone_exp_end, self.milestone_exp_excl],
                                [self.milestone_btn],
                                [self.milestone_alert]])
        milestone_tab = Panel(child=milestone_layout, title='Milestones')

        self.exp_layout = layout(children=[[self.title],
                                [self.exp_subtitle],
                                [self.exp_inst],
                                [self.exp_info],
                                [self.hdr_type, self.hdr_btn],
                                [self.exp_input_layout],
                                [self.exp_alert]])
        exp_tab = Panel(child=self.exp_layout, title="Nightly Progress")

        weather_layout = layout([[self.title],
                                [self.weather_subtitle],
                                [self.weather_inst],
                                [self.weather_time, self.weather_desc, self.weather_temp],
                                [self.weather_wind, self.weather_humidity, self.weather_btn],
                                [self.weather_table],])
        weather_tab = Panel(child=weather_layout, title="Weather")

        self.get_prob_layout()
        self.get_checklist_layout()
        self.get_nl_layout()

        self.layout = Tabs(tabs=[intro_tab, plan_tab, milestone_tab, exp_tab, weather_tab, self.prob_tab, self.check_tab, self.nl_tab])

    def run(self):
        self.plan_tab()
        self.milestone_tab()
        self.exp_tab()
        self.weather_tab()
        self.init_bt.on_click(self.initialize_log) 
        self.connect_bt.on_click(self.connect_log) 
        self.exp_btn.on_click(self.progress_add) 
        self.hdr_btn.on_click(self.choose_exposure)
        self.weather_btn.on_click(self.weather_add)
        self.prob_btn.on_click(self.prob_add)
        self.nl_btn.on_click(self.current_nl)
        self.check_btn.on_click(self.check_add)
        self.milestone_btn.on_click(self.milestone_add)
        self.plan_btn.on_click(self.plan_add)
        self.get_layout()

OS = OS_Report()
OS.run()
curdoc().title = 'DESI Night Log - OS Scientist'
curdoc().add_root(OS.layout)
