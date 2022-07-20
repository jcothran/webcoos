Sharing some information where I was experimenting more with object detection and trying to better develop guidelines and confidence thresholds.

The below folder are some beach crowd images I pulled from web searching and these are generally 'good' quality resolution images, probably taken with a higher resolution digital camera. If I lower the confidence threshold pretty low, around 0.01 confidence the detection performs decently without too many false positives or double counts. The person objects are outlined in orange boxes.

#example beach images at 0.01 confidence
https://drive.google.com/drive/folders/1DDUR22MA6Xe_jl6izDQLu1I2FG6nUx50

Taking the 'beach7' example image below

#beach7 image at 0.01 confidence
https://drive.google.com/drive/folders/1rvAhAJdd2qfKU4wnz2IqmqJb7QCSXIJd

the process can provide the individual 'cropped' images of the persons detected in the image
#beach7 person image crops(266 persons/images)
https://drive.google.com/drive/folders/1cyC7AW3Dd5zbsHdtJL5i1kWCN_gwXxOe

from those crops I have attached the image of a person that I think is fairly distant towards the middle of the picture. You can play a game of 'where's waldo?' finding them in the general picture. The image size of this distant person as detected is 21x34 pixels. From what I've read, I think 20-30 pixels width/height is about the minimum for objects to be recognized based on training sets, etc. In the example images, you will notice this translates into about 100 yards(meters) or 300 feet of distance before objects become too small within the image to be detected. 

I also pulled some larger 4k resolution(3840x2160 pixels) images from youtube videos - camera and drone
https://drive.google.com/drive/folders/1Hh_9rUJ2NLCshhhmRU4OMIWW1Nwymqwu

The below 4k drone shot does show some counts from a further distance although with having to set the confidence low at 0.01, it gets some false positives for 'person' with closed umbrellas and trash cans.
https://drive.google.com/file/d/1wXsekBmywnkYG69o0-rwtl8OCp6-xO1J/view?usp=sharing
 
I tried detection for 'car' in the below drone image flyover(3 shots with each shot getting closer), but it was too far to detect well.
https://drive.google.com/drive/folders/1AXVoGE33xbHbv7zLFsCxve_-P-mPWXF1

Also below are tests with mixed results for 2 south carolina beach cameras - the main issues we tend to run into again is that the cameras are placed too far back on the hotel balconies, resulting in the people being too 'small' in the images for detection and also the images are blurry which probably lowers the chance of detection or creates more false positives. We could experiment with a higher 4k camera from a hotel shot(a gopro) to see if that helps overcome some of the issues with regards to distance from the beach and bluriness of image, but ideally camera locations would be closer to the dune line or as close as possible to the objects or crowed to detect. 
https://drive.google.com/drive/folders/1dJboRs4z9CMyDDMjWpGxNZ91t64cFjSv