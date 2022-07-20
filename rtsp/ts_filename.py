from glob import glob
from subprocess import Popen, PIPE, STDOUT
import time

import datetime

#this script creates cam id, timestamp and 'thumb' suffix for later file processing
#the fixed 'thumb0000.jpg' assumes rtsp sampling time interval of 1 minute or greater

camsite = ['northinlet'] #currently only one listed for example, but could be multiple rtsp/camera id's

while True:
    if len(glob('rtsp_fetched/*.jpg')) == 0:
        print ('no files to process');
        time.sleep(10)
        continue

    #run through files

    for cam in camsite:

        #print ('rtsp_fetched/'+cam+'_*.jpg')
        allFiles = sorted(glob('rtsp_fetched/'+cam+'_*.jpg'))
        if len(allFiles) == 0:
            print ('no jpg files to process');
            time.sleep(10)
            continue
        
        for file in allFiles:
            print (file)

            currentDT = datetime.datetime.now().strftime('%Y-%m-%d_%H%M')
            print (str(currentDT))

            #thumb0000 is for later process filename parsing 
            cmd_str = 'mv rtsp_fetched/'+file.split('/')[-1]+' thumbs/'+cam+'_'+str(currentDT)+'_thumb0000.jpg'
            proc = Popen([cmd_str], shell=True)
            proc.wait()
                  
