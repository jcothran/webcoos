This is a tool which extends and generalizes to a degree the earlier work [NWLON_WebCOOS_Synchronizer](https://github.com/NOAA-CO-OPS/NWLON_WebCOOS_Synchronizer) These script modifications allow additional CSV files with a simple header column of 'datetime,value' listing to provide additional synchronized graphs listed in addition to NWLON water level graphs. A general script/tool flow outline is below.

```
[ Collection & Formatting Scripts ]
                       |
                       v
              [ CSV Files Input ]            [ NWLON Water Level Input ]
                       |                                  |
                       +----------------+-----------------+
                                        |
                                        v
                            [ webcoos_sync script ]
```

To install, go through the installation listed for the earlier [NWLON_WebCOOS_Synchronizer](https://github.com/NOAA-CO-OPS/NWLON_WebCOOS_Synchronizer) which also requires installing the [py-webcoos-client](https://github.com/WebCOOS/py-webcoos-client) and after registering to get a WebCOOS security token used by the scripts, test run the 'Usage' case to successfully produce a movie.

After this, swap in the files here (main.py, CoopsApi.py, API.py) in their respective project folders/places and then should be able to run test1.py successfully to produce the movie below with a single NWLON graph. From there you can try adding the example CSV files and rerunning test1.py to show those additional graphs or CSV graphs of your own choosing. Note the CSV files should be formatted to follow the same datetime fomatting convention and header as the first column and second column header name will provide the y-axis label. The csv filename will be listed in the graph legend. CSV datetime range should be about the same range as the start_time, end_time parameter. Currently the script may take a long time to run with downloading 20 images taking about 1 minute per image or 20 minutes total.

[Watch the webcoos_sync movie](https://drive.google.com/file/d/1pZwJPMehr7tgfj7xClWgO5HHUo5MKGOl/view?usp=sharing)<br/>
!(./media/webcoos_sync.jpg)

