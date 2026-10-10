from flask import Flask, jsonify
from flask_cloudflared import run_with_cloudflared,get_cloudflared_url
from flask_sock import Sock
import os
import cv2
import time
import json
import mediapipe as mp
import math
import threading

camera = cv2.VideoCapture(1)

app = Flask(__name__)
sock = Sock(app)
run_with_cloudflared(app)


eyeids = {"rightclosed": "120950645773429","leftclosed": "77311195566387", "bothclosed": "106057404944445", "bothopen": "91770181157589"}
mouthids = {"smile":"102380166414309","neutral": "115636305974164", "smileopen": "108337296267071", "neutralopen": "100338318558919"}
ce = "bothopen"
cm = "neutral"


@sock.route('/getid')
def getid(ws):
    while True:
        
        e = eyeids[ce]
        m = mouthids[cm]
        ws.send(json.dumps({"eyes": f"rbxassetid://{e}","mouth": f"rbxassetid://{m}"}))
        time.sleep(1/15)

BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = FaceLandmarkerOptions(
    base_options=BaseOptions(model_asset_path='face_landmarker.task'),
    running_mode=VisionRunningMode.IMAGE)

landmarker = FaceLandmarker.create_from_options(options)

prev = 0
face_id = ""

def runapp():
    app.run(host='0.0.0.0',port=8000, use_reloader=False)
    
if __name__ == "__main__":
    threading.Thread(target=runapp).start()
    

def distlandmarks(a,b):
    pos1 = [a.x, a.y, a.z]
    pos2 = [b.x, b.y, b.z]
    if all([a.x,a.y,a.z,b.x,b.y,b.z]):
        return math.dist(pos1,pos2)
    else:
        return None

def checkOpen(result):
    if result.face_landmarks:
        first = result.face_landmarks[0]
        upper = first[13]
        lower = first[14]
        left = first[33]
        right = first[263]
        
        

        gap_dist = distlandmarks(upper,lower)
        eye_dist = distlandmarks(left,right)
        ratio = gap_dist / eye_dist

        return ratio > 0.2
    else:
        return None

def checkSmile(result):
    if result.face_landmarks:
        first = result.face_landmarks[0]
        width = distlandmarks(first[234], first[454])
        left_right_y = (first[61].y + first[291].y) / 2
        center_y = (first[13].y + first[14].y) / 2
        mouth_width = distlandmarks(first[61], first[291])
        
        ratio = (left_right_y - center_y) / width
        otherratio = mouth_width / width
        
        return ratio < 0.02 and otherratio > 0.35
    
    else:
        return None

def checkClosedEye(result):

    if result.face_landmarks:
        first = result.face_landmarks[0]
        
        left_result = first[374].y - first[386].y
        right_result = first[145].y - first[159].y
        return (left_result < 0.008, right_result < 0.008)



while True:
    success, img = camera.read()
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    mp_vers = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = landmarker.detect(mp_vers)
    value = checkSmile(result)
    othervalue = checkOpen(result)
    if value is not None and othervalue is not None:
        smile = True if value else False
        opened = True if othervalue else False    
        smileopened = smile and opened
        neutralopened = not smile and opened
        leftclosed, rightclosed = checkClosedEye(result)

        if leftclosed and rightclosed:
            ce = "bothclosed"
        elif leftclosed:
            ce = "leftclosed"
        elif rightclosed:
            ce = "rightclosed"
        else:
            ce = "bothopen"

        if smile and opened:
            cm = "smileopen"
        elif smile:
            cm = "smile"
        elif opened:
            cm = "neutralopen"
        else:
            cm = "neutral"
            
    if cv2.waitKey(66) & 0xFF == ord('q'):
        break
    

print('broked')

