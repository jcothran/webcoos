from glob import glob
import subprocess
from subprocess import Popen, PIPE, STDOUT

from pandas import DataFrame, read_csv
import pandas as pd
import os

import requests
import time

#this script reprocesses the detection labels txt files into csv files, prefixing the lines with the camfile id and datetime based on the filename 
#files are moved from runs/detect/exp/labels to beach/results
#this is an example of how these summary files were processed, but could be processed differently depending on the summary storage structure, etc

def proc_common(cmd_str):
    proc = subprocess.Popen(cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )

    stdout, stderr = proc.communicate()
    print (stdout)
    print ("\n")

    proc.wait()
    print (proc.returncode)


home_dir = '/usr/src/app'
txt_dir = '/usr/src/app/runs/detect/exp/labels'

time_sleep_file = 1 #was set to 5 earlier, can be set depending on system performance

while True:
  if len(os.listdir(txt_dir) ) == 0:
    print ('no files to process');
    time.sleep(1)
    continue

  
  #run through txt files
  allFiles = sorted(glob(txt_dir+'/*thumb*.txt'))
  for file in allFiles:
    print(file)
   
    filename = file.split('/')[-1]

    #skip empty files
    if os.stat(file).st_size == 0:
      os.replace(txt_dir+'/'+filename, home_dir+'/beach/results/empty'+filename)
      continue

    filepath = file.split('_')
    #print (filename)

    camsite = filepath[0].split('/')[-1]

    thisDate = filepath[1][-10:]

    hour = int(filepath[2][0:2])
    min10 = int(filepath[2][2:4])
    min10 = min10 + int(filepath[3][-8:-4])

    #handle minute and hour for the file suffixed 0010.jpg case 
    if min10 == 60:
      min10 = 0
      hour = hour + 1
      if hour == 24:
        hour = 0

    site_str = camsite+','+thisDate+'T'+str(hour)+':'+str(min10).zfill(2)+':00'
    #print (site_str)

    //coco class id, subtract 1 from the reference number listed at,e.g. 0 = person, http://gist.github.com/AruniRC/7b3dadd004da04c80198557db5da4bdaeach/results
    //0 = person
    //25 = umbrella
    //56 = chair


    file_out = open(home_dir+'/beach/results/results_'+filename, 'w+')
    file_in = open(file, 'r')
    lines = file_in.readlines()
    for line in lines:
       line = line.strip()
       line_arr = line.split(' ')

       line_out = site_str+','+line_arr[0]+','+line_arr[1]+','+line_arr[2]+','+line_arr[3]+','+line_arr[4]+','+line_arr[5]
       #print (line_out)
       file_out.write(line_out+'\n')

    file_in.close()
    file_out.close()

    #save summary csv file to database table or other summary storage for later summary requests, graphs,etc

    #optional - keep processed files in original format in 'done' folder
    #os.replace(txt_dir+'/'+file.split('/')[-1], home_dir+'/beach/results/done/'+file.split('/')[-1])
   
    #remove summary txt files
    os.remove(txt_dir+'/'+file.split('/')[-1])

  time.sleep(time_sleep_file)

