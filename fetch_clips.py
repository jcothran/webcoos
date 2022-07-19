import subprocess
import pandas as pd

import os.path
from os import path

from pathlib import Path
import time

import datetime


#1 day = 144 periods(10 minute interval)
#4320 periods = 1 month

#the below line drives how this script works, pick a start date and a number of periods some distance into the future and the script will loop through
#the generated dates and attempt to retrieve the given files. If a time point is reached where a file cannot be found, the script will take a longer
#pause(600 seconds) between requests before attempting the same request again, so allowing the script to follow a continuously generated feed
#see the ignore_gap settings to modify this behavior if a gap in the generated feed exists

#another approach for handling gaps would be to test a number of periods into the future to see if file creation has resumed at a later time

datelist = pd.date_range('2020-07-04 13:50:00', periods=2, freq='10min')

#==camsite names
#twinpierscam
#staugustinecam

#follypiernorthcam
#follypiersouthcam

camsite = 'follypiernorthcam'

#ignore_gap variable can be set to True and time_sleep shortened if running this script in a 'catch-up' mode over a historical vs live feed, or if a time gap has been introduced in the feed, causing the script to become stuck waiting for a time point which will never appear

ignore_gap = False #default False, True for gap jumps
time_sleep = 600 #default 600, 1 for gap jumps
file_limit = 50 #default 50


def proc_common(cmd_str):
    proc = subprocess.Popen(cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )

    stdout, stderr = proc.communicate()
    print (stdout)
    print ("\n")

    proc.wait()
    print (proc.returncode)

    if proc.returncode == 0 or ignore_gap:
        print ('file ok')
        return True
    else:
        print ('file error. sleep '+str(time_sleep))
        time.sleep(time_sleep)
        return False

for date_this in datelist:
    
    #skip hours cameras are off or unusable image at night
    if date_this.hour < 5 or date_this.hour >= 21:
        continue

    success = False
    #print(success)

    while not success:
        #print(datetime.datetime.now())
        currentDT = datetime.datetime.now()
        print (str(currentDT))
        print (camsite)
        print (date_this)

        if len(os.listdir("video_fetched") ) > file_limit:
            print (str(file_limit)+' video files fetched already');
            time.sleep(time_sleep)
            continue

        #get video
        cmd_str = 'python -m wget -o video_fetched/'+camsite+'_'+str(date_this.year)+'-'+str(date_this.month).zfill(2)+'-'+str(date_this.day).zfill(2)+'_'+str(date_this.hour).zfill(2)+str(date_this.minute).zfill(2)+'.mp4 https://webcat-video.axds.co/'+camsite+'/raw/'+str(date_this.year)+'/'+str(date_this.year)+'_'+str(date_this.month).zfill(2)+'/'+str(date_this.year)+'_'+str(date_this.month).zfill(2)+'_'+str(date_this.day).zfill(2)+'/'+camsite+'.'+str(date_this.year)+'-'+str(date_this.month).zfill(2)+'-'+str(date_this.day).zfill(2)+'_'+str(date_this.hour).zfill(2)+str(date_this.minute).zfill(2)+'.mp4'
        print (cmd_str)
        success = proc_common(cmd_str)
