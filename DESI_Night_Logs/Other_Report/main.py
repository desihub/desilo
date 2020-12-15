"""
Created on May 21, 2020

@author: Parker Fagrelius

Other Observer to see Ongoing Night Log

start server with the following command:
bokeh serve --show Other_Report.py

view at: http://localhost:5006/Other_Report
"""

import os, sys

from bokeh.io import curdoc
from bokeh.models.widgets.markups import Div
from bokeh.layouts import layout
from bokeh.models.widgets import Panel, Tabs

sys.path.append(os.getcwd())
import nightlog as nl
from report import Report


class Other_Report(Report):
    def __init__(self):
        Report.__init__(self, 'Other')

        self.title = Div(text="DESI Nightly Intake Form - Non Observer",css_classes=['h1-title-style'], width=1000)
        desc = """This Night Log is for Non-Observers. It should mainly be used for observing the ongoing Night Log.
        In special circumstances, if a non-observer has an important comment about an exposure or problem, it can be added here.
        Before doing so, make sure to communicate with the Observing Scientist.
        """
        self.instructions = Div(text=desc+self.time_note.text, css_classes=['inst_style'], width=800)
        self.page_logo = Div(text="<img src='Other_Report/static/logo.png'>", width=400, height=400)

        self.comment_subtitle = Div(text="Comments", css_classes=['subt-style'])
        self.comment_alert = Div(text=' ',  css_classes=['alert-style'])

    def get_layout(self):

        intro_layout = layout([self.title,
                        [self.page_logo],
                        [self.instructions],                 
                        self.intro_subtitle,

                        [self.date_init, self.your_name],
                        [self.connect_bt],
                        self.connect_txt,
                        self.nl_info,
                        self.intro_txt], width=1000)
        intro_tab = Panel(child=intro_layout, title="Initialization") #                        self.intro_info,

        comment_layout = layout([self.title,
                            self.comment_subtitle,
                            self.time_note,
                            [self.time_title, self.exp_time, self.now_btn],
                            self.exp_comment,
                            self.exp_btn,
                            self.comment_alert], width=1000)
        comment_tab = Panel(child=comment_layout, title="Comments")

        #self.get_intro_layout()
        self.get_prob_layout()
        self.get_img_layout()
        self.get_nl_layout()
        self.get_plots_layout()

        self.layout = Tabs(tabs=[intro_tab, comment_tab, self.prob_tab, self.img_tab, self.plot_tab, self.nl_tab]) #comment_tab, self.prob_tab, 


    def run(self):
        self.time_tabs = [None, self.exp_time, self.prob_time, None, None]
        self.now_btn.on_click(self.time_is_now)
        self.connect_bt.on_click(self.connect_log)
        self.exp_btn.on_click(self.comment_add)
        self.prob_btn.on_click(self.prob_add)
        self.get_layout()


Other = Other_Report()
Other.run()
curdoc().title = 'DESI Night Log - Non Observer'
curdoc().add_root(Other.layout)
curdoc().add_periodic_callback(Other.current_nl, 30000)
