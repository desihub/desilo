"""
Created on May 21, 2020
@author: Parker Fagrelius

start server with the following command from folder above this.
bokeh serve --show DQS_Report

view at: http://localhost:5006/DQS_Report
"""

import os, sys
sys.path.append(os.getcwd())
from datetime import datetime

from bokeh.io import curdoc 
from bokeh.models import TextInput, RadioButtonGroup
from bokeh.models.widgets.markups import Div
from bokeh.models.widgets import Tabs

from report import Report


class DQS_Report(Report):
    def __init__(self):
        Report.__init__(self, 'DQS')

        self.title = Div(text="DESI Nightly Intake - Data QA Scientist", css_classes=['h1-title-style'], width=1000)
        inst = """
        The Data Quality Scientist (DQS) is responsible for analyzing all exposures for their quality.
        Submit problems as they arise throughout the night and complete the DQS checklist once an hour. Let the Lead Observer
        know if you encounter any issues. 
        """
        self.instructions = Div(text=inst, css_classes=['inst-style'], width=500)
        self.page_logo = Div(text="<img src='DQS_Report/static/logo.png'>", width=350, height=300)

        self.dqs_checklist = ["Are all images being transferred to Night Watch?", "Did you check the observing conditions?", "Did you check the guiding?"]

        self.quality_list = ['Good','Not Sure','No Data','Bad']
        self.quality_btns = RadioButtonGroup(labels=self.quality_list, active=0)

    def get_layout(self):
        self.get_intro_layout()
        self.get_dqs_exp_layout()
        self.get_prob_layout()
        self.get_checklist_layout()
        self.get_nl_layout()
        self.get_weather_layout()
        self.get_ns_layout()

        self.layout = Tabs(tabs=[self.intro_tab, self.exp_tab, self.prob_tab, self.check_tab, self.weather_tab, self.nl_tab, self.ns_tab])

    def run(self):
        self.get_layout()
        self.time_tabs = [None, None, self.prob_time, None, None, None]
        self.now_btn.on_click(self.time_is_now)
        self.connect_bt.on_click(self.connect_log)
        self.exp_btn.on_click(self.exp_add)
        self.prob_btn.on_click(self.prob_add)
        self.check_btn.on_click(self.check_add)
        self.dqs_load_btn.on_click(self.dqs_load)
        self.prob_load_btn.on_click(self.load_problem)
        self.ns_date_btn.on_click(self.get_nightsum)
        self.all_button.on_click(self.add_all_to_bad_list)
        self.partial_button.on_click(self.add_some_to_bad_list)
        self.bad_add.on_click(self.bad_exp_add)
        self.prob_delete_btn.on_click(self.problem_delete)
        self.exp_select.on_change('value',self.select_exp)
        self.ns_next_date_btn.on_click(self.ns_next_date)
        self.ns_last_date_btn.on_click(self.ns_last_date)



DQS = DQS_Report()
DQS.run()
curdoc().title = 'DESI Night Log - Data QA Scientist'
curdoc().add_root(DQS.layout)
curdoc().add_periodic_callback(DQS.current_nl, 30000)
curdoc().add_periodic_callback(DQS.get_exposure_list, 30000)

