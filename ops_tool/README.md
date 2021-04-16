This Bokeh GUI is meant to be used by the DESI Operation managers and facilitate communication with observers. At this point, in order to send emails with the GUI, you need access it via KPNO.

To use:

ssh -XY desiobserver@desi-4.kpno.noao.edu

cd ~/parkerf/desilo/ops_tool

bokeh serve OpsTool/ --allow-websocket-origin=desi-4.kpno.noao.edu:5006

In a browser: http://desi-4.kpno.noao.edu:5006/OpsTool
