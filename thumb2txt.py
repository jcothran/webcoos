from glob import glob
from subprocess import Popen, PIPE, STDOUT
import time

#this script performs the object detection in batches of images
#the batching may or may not be needed depending on if the detection process runs out of memory. earlier development had issues with out of memory errors
#due to too many images being batch processed at once, but the latest development does not seem to have the same issue - max_batch_size can be set arbitrarily large to batch everything to one pass
#the below script shuffles files into batch folders so only max_batch_size is processed at one time


#min_batch_size is currently set to the number of images(10) produced from a 10 minute clip, but can be changed to suit performance
min_batch_size = 10
max_batch_size = 30


while True:
  if len(glob("thumbs/*.jpg")) < min_batch_size:
    print ('not enough files to process');
    time.sleep(10)
    continue

  cntFile = 0

  #run through files
  allFiles = sorted(glob("thumbs/*.jpg"))
  for file in allFiles:
    print (file)

    #move file to buffer folder
    cmd_str ='mv '+file+' thumbs/buf'
    proc = Popen([cmd_str], shell=True)
    proc.wait()
    #print (proc.returncode)

    cntFile = cntFile + 1
    print ("cntFile:"+str(cntFile))

    if (cntFile % max_batch_size == 0 or len(glob("thumbs/*.jpg")) == 0): #if batch size reached or thumbs empty
      cntFile = 0 

      #do object detection
      #note '--conf_thres=0.01, default is 0.25, but lowering this to 0.01 increases detections without too many false positives in testing
      #note '--class 0 25 56', (0=person,25=umbrella,56=chair), default is to run without class filter or class list can be changed depending on scene or interest
      cmd_str = 'python /usr/src/app/detect.py --source /usr/src/app/beach/thumbs/buf --conf_thres=0.01 --class 0 25 56 --save-txt --save-conf --nosave --exist-ok'

      proc = Popen([cmd_str], stdout=PIPE, shell=True)
      for line in iter(proc.stdout.readline, b''):
        print (line,)
      proc.stdout.close()
      proc.wait()

      #move processed buffer files to done folder - could optionally choose not to keep these image files
      cmd_str = 'mv thumbs/buf/*.jpg thumbs/done'
      proc = Popen([cmd_str], shell=True)


