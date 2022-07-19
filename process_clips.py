from glob import glob
import subprocess

import os.path
from os import path

from pathlib import Path
import time

#process_clips.py - converts video clips to image stills with ffmpeg
#the lock file mechanism can be changed to suit system/performance

time_sleep_file = 1 #was 4, sleep can be set lower depending on system performance

def proc_common(cmd_str):
    proc = subprocess.Popen(cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )

    stdout, stderr = proc.communicate()
    print (stdout)
    print ("\n")

    proc.wait()
    print (proc.returncode)

while True:
    if len(os.listdir("video_fetched") ) == 0:
        print ('no video files to process');
        time.sleep(10)
        continue

    #run through files
    allFiles = sorted(glob("video_fetched/*.mp4"))
    for file in allFiles:
        print (file)

        filename = file.split('_')
        #print (filename)

        while path.exists("lock_tf.txt"):
            time.sleep(2)

        Path('lock_tf.txt').touch()
        
        #get jpg image stils from video, fps=1/60 is 1 for every 1 minute
        cmd_str = 'ffmpeg -i '+file+' -vf fps=1/60 thumbs/'+file.split('/')[-1].split('.')[0]+'_thumb%04d.jpg -hide_banner'
        print(cmd_str)
        proc_common(cmd_str)

        #optional - keep fetched videos in done folder
        #cmd_str  = 'mv video_fetched/'+file.split('/')[-1]+' video_fetched/done/'+file.split('/')[-1]
        #proc_common(cmd_str)

        #remove fetched videos - these could optionally be moved someplace else depending on available storage, etc
        os.remove("video_fetched/"+file.split('/')[-1])

        #print ("begin remove lock_tf.txt")
        os.remove("lock_tf.txt")
        #print ("end remove lock_tf.txt")
        time.sleep(time_sleep_file);

