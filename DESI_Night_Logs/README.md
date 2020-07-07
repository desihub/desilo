To run both All Night Log apps, run the following code:

* Local Machine: bokeh serve --show OS_Report/ DQS_Report/ Other_Report/
* DESI server: bokeh serve OS_Report DQS_Report Other_Report --allow-websocket-origin=desi-2.kpno.noao.edu:5006
