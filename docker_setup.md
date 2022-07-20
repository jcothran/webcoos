First step is to pull the below docker image (around 19 gigabytes) which I've found to be a nice package of YOLOv5 (You-Only-Look-Once) tools, the primary focus here being on object detection(inference) using their detect.py script. 

https://hub.docker.com/r/ultralytics/yolov5

https://github.com/ultralytics/yolov5/blob/master/detect.py

#additional links<br/>
https://github.com/ultralytics/yolov5<br/>
https://colab.research.google.com/github/ultralytics/yolov5/blob/master/tutorial.ipynb

Once this docker instance is up and running, the default starting path is 
/usr/src/app to which I've added(on my own, not in the docker pull) a beach/thumbs folder where jpg images are dropped to

If you drop sample beach jpg images with persons, etc(chairs, umbrellas) to that folder
/usr/src/app/beach/thumbs

and run

python detect.py --source beach/thumbs

it will run the detection(giving info while processing) on those images and drop the results (images with bounding boxes and confidence levels) to /usr/src/app/runs/detect/exp Subsequent runs will index the target folder to exp2,exp3,...

Once you have that running detections successfully, let me know and will continue with next steps sharing the helper python scripts I have that turn this into more of a continuous cron to summary database process.

The detect.py option flags to generate the text output of this process is the following.

python detect.py --source beach/thumbs --save-txt --save-conf --nosave --exist-ok

where the text file output is saved under an additional exp/labels folder

The file line format is
object class#,confidence,x,y,width,height 

In my processing, I prefix these lines with the camera id and datetime for the image like below with coco object class id's at the below link

coco class id, subtract 1 from the reference number listed at,e.g. 0 = person, http://gist.github.com/AruniRC/7b3dadd004da04c80198557db5da4bdaeach/results
    0 = person
    25 = umbrella
    56 = chair

detect.py is currently run with the --class 0 25 56 as a [nms](https://learnopencv.com/non-maximum-suppression-theory-and-implementation-in-pytorch/) filter for only detecting these 'beach' classes of interest, this class id list can be changed as needed

    follypiernorthcam,2020-07-04T13:51:00,0,0.955859,0.54375,0.0132813,0.0625,0.25475
    follypiernorthcam,2020-07-04T13:51:00,56,0.291797,0.765278,0.0382813,0.0805556,0.253011
    follypiernorthcam,2020-07-04T13:51:00,25,0.810547,0.584028,0.0835937,0.120833,0.28308

detect.py can also be run with a flag specifying to only 

I'll also mention it can be tricky getting the docker container to fully or properly utilize the underlying GPU hardware. Generally the below type link is what I followed with the command like listed in starting the docker container with nvidia GPU. The nvidia-smi command was also useful in monitoring the GPU memory usage and performance

https://www.howtogeek.com/devops/how-to-use-an-nvidia-gpu-with-docker-containers/

docker run -it --gpus all nvidia/cuda:11.4.0-base-ubuntu20.04 nvidia-smi