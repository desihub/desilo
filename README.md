# desilo

This repository is now largely used by the **Observing Operations** team to develop tools to manage operations. It has been used in the past to develop other tools used by Lead Observers.

* **DESI-Night-Logs**: no longer used. It is kept here to maintain OS/DQS structure of the past. The NightLog code can now be found here: https://github.com/desihub/desinightlog
* **reporting**: Contains code and data used for weekly and monthly reporting of time use during nightly operations
* **obs_stats**: Contains code and data to establish observing metrics
* **ops_tool**: Contains the observing schedule and tools to help communicate with observers
  *  **OpsTool** and **OpsTool/auto_ops_tool.py**: used to send emails to observers and keep track of observer preparation, including VPN access
  *  **OpsViewe**r: app running at NERSC to display the daily observing schedule. App run through Spin Services. Can be accessed here: https://obsschedule.desi.lbl.gov
