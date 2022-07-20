import datetime
import subprocess
import time

#this script uses ffmpeg to grab a single image from an rtsp feed
#the script is hard-coded to a specific rtsp, but could be modified to loop over multiple rtsp endpoint references

#default 6,19 - these are the local server timezone hour references of when not to request images based on nighttime hours
startHour = 6
endHour = 19

import urllib.request, urllib.error, urllib.parse
import re

url = 'https://rtsp.me/embed/Qs3ba7n8/'
startTime = time.time()
#print (startTime)
nextSampleTime = startTime-1
sampleNum = 0
intervalTime = 300 #number of seconds between samples

while True:
    currentHour = datetime.datetime.now().strftime('%H')
    #print ('hour:'+currentHour)

    if int(currentHour) >= startHour and int(currentHour) < endHour:
        if time.time() > nextSampleTime:
            # run during daylight
            sampleNum += 1
            nextSampleTime = startTime+(sampleNum*intervalTime)

            response = urllib.request.urlopen(url)

            for line in response:
                match = re.search(r'm3u8',str(line))

                if match:
                    #print ('found', match.group())
                    #print (str(line))
                    str_parts = str(line).split('/')
                    #print (str_parts[3]+'/'+str_parts[4])
                    
                    #-ss time offset helps to get a better image, avoidng artifacts
                    cmd_str = 'ffmpeg -i "https://mia.rtsp.me/'+str_parts[3]+'/'+str_parts[4]+'/hls/Qs3ba7n8.m3u8" -ss 00:00:01.50 -vframes 1 rtsp_fetched/northinlet_%04d.jpg -hide_banner'

                    print (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    print (cmd_str)
                    proc = subprocess.Popen(cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
                    time.sleep(intervalTime-1)
    else:
        time.sleep(60)  # sleep if nighttime 
