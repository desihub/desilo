"""
Created on July 21, 2021

@author: Parker Fagrelius

Updated DESI_Night_Log/OS_Report for single observer platform

"""

import os, sys
sys.path.append(os.getcwd())
sys.path.append('./ECLAPI-8.0.12/lib')

from bokeh.io import curdoc
from bokeh.models import TextInput, Button, TextAreaInput, Select
from bokeh.models.widgets.markups import Div
from bokeh.layouts import layout, column, row
from bokeh.models.widgets import Panel, Tabs

import nightlog as nl
from report import Report


class Obs_Report(Report):
    def __init__(self):
        Report.__init__(self, 'Obs')

        self.title = Div(text="DESI Nightly Intake - Observers", css_classes=['h1-title-style'], width=1000)

        desc = """
        To begin, connect to the observing night Night Log using the list of Existing Night Logs. Add information about the Observers and press the 
        Update Tonight's Log. 
        Throughout the night, enter information about the exposures, problems that occur, and observing conditions. Complete the 
        Checklist at least once every hour. NOTE: If inputs are being made into a DNI at both KPNO and NERSC, the inputs
        made at KPNO for certain things (meta data, plan, milestones), will be prioritized over those made at NERSC.
        """
        self.instructions = Div(text=desc, css_classes=['inst-style'], width=500)
        
        self.page_logo = Div(text="<img src='ObserverReport/static/logo.png'>", width=350, height=300)
        
        self.os_checklist = ["Did you check the weather?", "Did you check the guiding?", "Did you check the positioner temperatures?","Did you check the FXC?", "Did you check the Spectrograph Cryostat?","Did you check the FP Chiller?"]

    def get_layout(self):
        self.contributer_list = TextAreaInput(placeholder='Contributer names (include all)', rows=2, cols=3, title='Names of all Contributers')
        self.contributer_btn = Button(label='Update Contributer List', css_classes=['add_button'], width=300)

        self.connect_hdr = Div(text="Connect to Existing Night Log", css_classes=['subt-style'], width=800)
        self.init_hdr = Div(text="Update Tonight's Night Log", css_classes=['subt-style'], width=800)

        self.init_btn = Button(label="Update Tonight's Log", css_classes=['init_button'], width=200)
        self.so_name_1 = TextInput(title ='Support Observing Scientist 1', placeholder = 'Sally Ride')
        self.so_name_2 = TextInput(title ='Support Observing Scientist 2', placeholder = "Mae Jemison")

        self.LO_1 = Select(title='Lead Observer 1', value='None', options=self.lo_names)
        self.LO_2 = Select(title='Lead Observer 2', value='None', options=self.lo_names)
        self.lo_names = ['None ','Liz Buckley-Geer','Ann Elliott','Parker Fagrelius','Satya Gontcho A Gontcho','James Lasker','Martin Landriau','Claire Poppett','Michael Schubnell','Luke Tyas','Other ']

        self.OA = Select(title='Observing Assistant', value='Choose One', options=self.oa_names)
        self.oa_names = ['None ','Karen Butler','Amy Robertson','Anthony Paat','Thaxton Smith','Dave Summers','Doug Williams','Other ']

        self.get_intro_layout()
        self.get_nl_layout()
        self.get_milestone_layout()
        self.get_plan_layout()
        self.get_exp_layout()
        self.get_prob_layout()
        self.get_checklist_layout()
        self.get_weather_layout()
        self.get_ns_layout()
        

        intro_layout = layout([self.buffer,
                            self.title,
                            [self.page_logo, self.instructions],
                            self.connect_hdr,
                            [self.date_init, self.connect_bt],
                            self.connect_txt,
                            self.line,
                            self.init_hdr,
                            [[self.so_name_1, self.so_name_2], [self.LO_1, self.LO_2], self.OA],
                            self.init_btn,
                            self.line2,
                            self.contributer_list,
                            self.contributer_btn,
                            self.nl_info,
                            self.intro_txt], width=1000)
        intro_tab = Panel(child=intro_layout, title="Initialization")

        self.layout = Tabs(tabs=[intro_tab, self.plan_tab, self.milestone_tab, self.exp_tab, self.prob_tab, self.weather_tab, self.check_tab,  self.nl_tab, self.ns_tab], css_classes=['tabs-header'], sizing_mode="scale_both")

    def run(self):
        self.get_layout()
        self.time_tabs = [None, None, None, self.exp_time, self.prob_time, None, None, None]

        self.now_btn.on_click(self.time_is_now)
        self.init_btn.on_click(self.add_observer_info)
        self.connect_bt.on_click(self.connect_log)
        self.exp_btn.on_click(self.progress_add)
        self.exp_load_btn.on_click(self.exposure_load)
        self.prob_load_btn.on_click(self.problem_load)
        self.weather_btn.on_click(self.weather_add)
        self.prob_btn.on_click(self.prob_add)
        self.nl_submit_btn.on_click(self.nl_submit)
        self.check_btn.on_click(self.check_add)
        self.milestone_btn.on_click(self.milestone_add)
        self.milestone_new_btn.on_click(self.milestone_add_new)
        self.milestone_load_btn.on_click(self.milestone_load)
        self.plan_btn.on_click(self.plan_add)
        self.plan_new_btn.on_click(self.plan_add_new)
        self.plan_load_btn.on_click(self.plan_load)
        self.plan_delete_btn.on_click(self.plan_delete)
        self.milestone_delete_btn.on_click(self.milestone_delete)
        self.exp_delete_btn.on_click(self.progress_delete)
        self.prob_delete_btn.on_click(self.problem_delete)
        #self.img_btn.on_click(self.image_add)
        self.contributer_btn.on_click(self.add_contributer_list)
        self.exp_select.on_change('value',self.select_exp)
        self.summary_btn.on_click(self.summary_add)
        self.time_btn.on_click(self.add_time)
        self.summary_load_btn.on_click(self.summary_load)
        self.ns_date_btn.on_click(self.get_nightsum)
        self.ns_next_date_btn.on_click(self.ns_next_date)
        self.ns_last_date_btn.on_click(self.ns_last_date)
        
OBS = OS_Report()
OBS.run()
curdoc().title = 'DESI Night Log - Observers'
curdoc().add_root(OBS.layout)
curdoc().add_periodic_callback(OBS.current_nl, 30000)
curdoc().add_periodic_callback(OBS.get_exposure_list, 30000)
