# ops_tool
There are two main tools in this folder. They are both used for communicating with observers about the schedule and preparing of upcoming observing shifts.
## **OpsTool**
* **auto_ops_tool.py**: Send emails automatically to observers each day for 1 month, 2 week, night before and day after an observing shift. This is being run as a cronjob on desiobserver@desi-4.kpno.noao.edu each day at 8am MST. 
* **main.py**: Bokeh GUI that is meant to be run on a local machine (not NERSC)
  * Dashboard for past, present and future shifts. Helps keep track of VPN access and whether observers have completed forms
  * Email entry, for manual sending of emails to observer when auto_ops_tool doesn't work 
  * Schedule
* **static**: content of emails sent by auto_ops_tool and the main GUI  This Bokeh GUI is meant to be used by the DESI Operation managers and facilitate communication with observers. At this point, in order to send emails with the GUI, you need access it via KPNO.
* To run OpsTool:
  * on local machine
    * `cd <your directory>/desilo/ops_tool/`
    * `bokeh serve --show OpsTool/`
    * access in browser as http://localhost:5006/OpsTool
  * on desi cluster: 
    * ssh desiobserver@desi-4.kpno.noao.edu
    * `cd ~/obsops/desilo/ops_tool1
    * `bokeh serve OpsTool/ --allow-websocket-origin=desi-4.kpno.noao.edu:5006`
    * access in browser at http://desi-4.kpno.noao.edu:5006/OpsTool
  * There are several arguments (all optional) you can add to the bokeh serve. To your call, add `--args` followed by the following
    *  -l, --local: Use locally saved schedule rather than online version.
    * -t, --test: Test Mode
    * --print_emails: Prints out a list of emails of all observers
    * -s,--semester: Identify particular semester.
    
## **OpsViewer**
* This is run at NERSC on Rancher2. 
* **main.py**: Bokeh GUI code
* **templates**: css styles, etc

## Other Files: these are all used by one of the tools above.
* **Dockerfile**: used by OpsViewer on the spin services site
* **google_access_account.json**: used to access the google sheets used in the tools
  * Note: you will also need a credentials.json file to access the google sheets. This cannot be saved on github.  
* **obs_schedule_`*`.csv**: hard copies of the schedules downloaded from google. These are used mostly at the beginning of a semester. They should be updated periodically if changes are made to the google sheets
* **user_info.csv**: contains the names, email addresses, and institutions of all observers
* **per_observer.csv**: file used to track VPN status of observers and whether they have filled out the pre and post observing questionaires
* **per_shift.csv**: copy of most recent version. This file is updated each time OpsTool/main.py is run to ensure all schedule changes are reflected. This file keeps track of what shifts are upcoming, etc. 

