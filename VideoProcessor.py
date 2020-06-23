import os
import numpy as np
import cv2
import pytesseract
from PIL import Image, ImageDraw, ImageFont
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\Charlotte\AppData\Local\Tesseract-OCR\tesseract.exe'
# You have to actually install tesseract. You have to install the python module AND the the exe. 
# This then tells the module where to find the exe. 


# https://www.pyimagesearch.com/2014/09/15/python-compare-two-images/
def mse(imageA, imageB):
    # the 'Mean Squared Error' between the two images is the
    # sum of the squared difference between the two images;
    # NOTE: the two images must have the same dimension
    err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
    err /= float(imageA.shape[0] * imageA.shape[1])

    # return the MSE, the lower the error, the more "similar"
    # the two images are
    return err
    
# My youtube videos are organized by weeks. 2 videos per day, 14 videos per week. 
# The script starts by creating a new week to move the recorded footage into and 
# rename to a more human readable format
def makeNewWeek():
    week = "Week {0}".format(len([name for name in os.listdir('.') if os.path.isdir("{0}\{1}".format('.',name)) and 'Week' in name])+1)
    os.mkdir(week)
    return week

# The script moves the videos from my OBS recording directory to the new folder,
# renaming them to a more human readable format at the same time.
def moveVideos(start, dest):
    MKVS = [name for name in os.listdir(start) if os.path.splitext("{0}\{1}".format(start,name))[1] == ".mkv"]
    count = 0
    for i in range(0,14):
        os.rename("{0}/{1}".format(start,MKVS[i]), "{0}/0{1}0{2}.mkv".format(dest,i//2+1,i%2+1))
        
# The script searches through the videos for two different images which are guaranteed to
# be in specific locations.
# The first is a "perk" text button in the trader screen. The currently played perk will be written
# in text just above it,so we can grab an image of that and OCR it.
# The second is a compressed version of my avatar which is shown in the lose/win screen.
# The map will also be shown in this screen, so we can grab an image of it and OCR it.
# We take this OCR'd text and save it with the episode number in a dict that gets returned.
def grabVideoInfo(week):        
    PATH = "./Week {0}".format(week)
    MKVS = [name for name in os.listdir(PATH) if os.path.splitext("{0}\{1}".format(PATH,name))[1] == ".mkv"]
    CurEpisode = int([name for name in os.listdir('thumbnails') if os.path.splitext(name)[0][0:2].lower() == 'ep'][-1].strip(".jpg")[2:])+1
    Episodes = {}
    
    for MKV in MKVS:
        vidcap = cv2.VideoCapture("{0}/{1}".format(PATH,MKV))
        perk = ""
        map = ""
        
        perk = cv2.imread("ScriptStuff/Icons/perk.png")
        yama = cv2.imread("ScriptStuff/Icons/yama.png")
        
        
        # Sometimes I start on the previous death/win screen
        # So if we start from frame 0, it will find the previous map
        # This skips like 4ish minutes into the video which should be 
        # well into whatever map/perk I settled on
        for i in range(0, 14000):
            vidcap.grab()
        while True:
            # We only want to check if the image is on screen every about 5 seconds
            # Might have to shorten this if it's not 100% reliable
            # But it hasn't had any issues yet so seems good.
            # I probably have the trader screen open for more than 5 seconds at once
            # And the end screen is definitely always open for more than 5 seconds
            for i in range(0,300):
                vidcap.grab()
            success,image = vidcap.read()
            if len(perk) == 0:   
                err = mse(image[154:181,251:308],perk)
                print("Checking episode perk {0}... difference: {1}".format(MKV, err))
                if(err < 1000):
                    perk = pytesseract.image_to_string(Image.fromarray(image[90:147, 234:660]), lang='eng')
                    print("Found perk {0}".format(perk))
            if len(map) ==0:
                err = mse(image[272:304,112:144], yama)
                print("Checking episode map {0}... difference: {1}".format(MKV, err))
                if(err < 1000):
                    map = pytesseract.image_to_string(Image.fromarray(image[103:159,676:1299]), lang='eng')
                    print("Found map {0}".format(map))
            if len(map) != 0 and len(perk) != 0:
                break
        Episodes[CurEpisode] = {"perk" : perk, "map" : map}
        CurEpisode = CurEpisode + 1
        print(Episodes)
    return Episodes
    
# We take a dict of episodes with their perk/map, grab the background for that map
# Put the overlay on top of it, along with the perk icon and episode number.
# Then we save the thumbnail to the thumbnails folder. 
def makeThumbnails(episodes):
    for episode in episodes:
        if not os.path.exists("ScriptStuff/Icons/{0}.png".format(episodes[episode]['map'])):
            input("{0}.png does not exist. Please create the map background and press enter.".format(episodes[episode]['map']))
        if not os.path.exists("ScriptStuff/Icons/{0}.png".format(episodes[episode]['perk'])):
            input("{0}.png does not exist. Please create the perk icon and press enter.".format(episodes[episode]['perk']))
       
        thumbnail = Image.open("ScriptStuff/Icons/{0}.png".format(episodes[episode]['map']))
        overlay = Image.open("ScriptStuff/Icons/overlay.png")
        perk = Image.open("ScriptStuff/Icons/{0}.png".format(episodes[episode]['perk']))
        thumbnail.paste(overlay, (0,0), overlay)
        thumbnail.paste(perk, (0,0), perk)
        draw = ImageDraw.Draw(thumbnail)
        font = ImageFont.truetype("Bahnschrift.ttf", size=105)
        (x, y) = (198, 586)
        colour = 'rgb(255,255,255)'
        draw.text((x, y), str(episode), fill=colour, font=font)
        thumbnail.save("thumbnails/ep{0}.jpg".format(episode))
           


############################
#          TODO
############################
# Upload video/thubmnail to YouTube

if __name__ == "__main__":
    week = makeNewWeek()
    moveVideos("D:\Videos\KF2", week)
    makeThumbnails(grabVideoInfo(week))
    