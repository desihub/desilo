"""
Created on May 21, 2020
@author: Parker Fagrelius

Night Log for non-observers. They can monitor ongoing Night Log and make comments as needed.

start server with the following command:
bokeh serve --show Other_Report.py

view at: http://localhost:5006/Other_Report
"""

import os, sys
sys.path.append(os.getcwd())

from bokeh.io import curdoc
from bokeh.models.widgets.markups import Div
from bokeh.models.widgets import Tabs

from report import Report


class Other_Report(Report):
    def __init__(self):
        Report.__init__(self, 'Other')

        self.title = Div(text="DESI Nightly Intake Form - Non Observer",css_classes=['h1-title-style'], width=1000)
        desc = """This Night Log is for Non-Observers. It should mainly be used for observing the ongoing Night Log.
        In special circumstances, if a non-observer has an important comment about an exposure or problem, it can be added here.
        Before doing so, make sure to communicate with the Observing Scientist.
        """
        self.instructions = Div(text=desc+self.time_note.text, css_classes=['inst_style'], width=500)
        self.page_logo = Div(text="<img src='Other_Report/static/logo.png'>", width=350, height=300)

    def get_layout(self):
        self.get_intro_layout()
        self.get_os_exp_layout()
        self.get_prob_layout()
        self.get_weather_layout()
        self.get_nl_layout()
        self.get_ns_layout()

        self.layout = Tabs(tabs=[self.intro_tab, self.exp_tab, self.prob_tab, self.weather_tab, self.nl_tab, self.ns_tab]) #comment_tab, self.prob_tab, 

    def run(self):
        self.get_layout()
        self.time_tabs = [None, self.exp_time, self.prob_time, None, None]
        self.now_btn.on_click(self.time_is_now)
        self.connect_bt.on_click(self.connect_log)
        self.exp_load_btn.on_click(self.load_exposure)
        self.exp_btn.on_click(self.comment_add)
        self.prob_btn.on_click(self.prob_add)
        self.prob_load_btn.on_click(self.load_problem)
        self.ns_date_btn.on_click(self.get_nightsum)
        self.exp_delete_btn.on_click(self.progress_delete)
        self.prob_delete_btn.on_click(self.problem_delete)


Other = Other_Report()
Other.run()
curdoc().title = 'DESI Night Log - Non Observer'
curdoc().add_root(Other.layout)
curdoc().add_periodic_callback(Other.current_nl, 30000)
curdoc().add_periodic_callback(Other.get_exposure_list, 30000)
