To run All Night Log apps, run the following code:

* Local Machine: bokeh serve --show OS_Report/ DQS_Report/ Other_Report/
* DESI server: bokeh serve OS_Report DQS_Report Other_Report --allow-websocket-origin=desi-16.kpno.noao.edu:5006
** to have the log saved to a file, add the following option: --log-file error.log
To report any problem, file a ticket on https://github.com/desihub/desilo/issues.

For help, contact Parker Fagrelius and Satya Gontcho A Gontcho. 
