from flask import Flask, jsonify
from flask_cloudflared import run_with_cloudflared,get_cloudflared_url
from flask_sock import Sock
import cv2
import time
import json
import mediapipe as mp
import math
from path import Path
import threading
import tkinter as tk
import path
from tkinter import ttk

gettuff = lambda name: Path(__file__).parent / name
camera = cv2.VideoCapture(1)










eyeids = {"rightclosed": "120950645773429","leftclosed": "77311195566387", "bothclosed": "106057404944445", "bothopen": "91770181157589"}
mouthids = {"smile":"102380166414309","neutral": "115636305974164", "smileopen": "108337296267071", "neutralopen": "100338318558919"}
ce = "bothopen"
cm = "neutral"



BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode
landmarkertaskthingy = str(gettuff('face_landmarker.task'))
options = FaceLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=landmarkertaskthingy),
    running_mode=VisionRunningMode.IMAGE)

landmarker = FaceLandmarker.create_from_options(options)

prev = 0
face_id = ""


    

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

        return ratio > 0.18
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

fps = 30
running = False

def loop(root):    
    if running:
        global ce,cm
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
    root.after(1,lambda: loop(root))

                
    

print('broked')

root = tk.Tk()
class Application:
    def __init__(self, root):

        self.root = root
        root.title("Better Dynamic Faces")
        root.geometry("600x120")

        self.label2 = tk.Label(root, text="Better Dynamic Faces", font=("Helvetica", 13))
        self.label2.place(x=10, y=10, width=190, height=30)

        self.beginbutton = tk.Button(root, text="Begin", command=self.on_beginbutton, font=("Helvetica", 17))
        self.beginbutton.place(x=460, y=16, width=120, height=29)

        self.urle = tk.Entry(root, state="readonly")
        self.urle.place(x=60, y=45, width=340, height=30)

        self.urll = tk.Label(root, text="URL:", font=("Helvetica", 12))
        self.urll.place(x=10, y=45, width=40, height=30)

        self.stopbutton = tk.Button(root, text="Stop", command=self.on_stopbutton, font=("Helvetica", 17), state="disabled")
        self.stopbutton.place(x=460, y=71, width=120, height=29)

        self.fpse = tk.Entry(root)
        self.fpse.place(x=60, y=85, width=40, height=30)

        self.set = tk.Button(root, text="Set", command=self.on_set)
        self.set.place(x=105, y=86, width=60, height=30)

        self.fpsl = tk.Label(root, text="FPS:", font=("Helvetica", 12))
        self.fpsl.place(x=10, y=85, width=40, height=30)

    def on_beginbutton(self):
        global running
        running = True
        loop(self.root)
        self.stopbutton.config(state="normal")
        self.beginbutton.config(state="disabled")

    def on_stopbutton(self):
        global running
        running = False      
        self.beginbutton.config(state="normal")
        self.stopbutton.config(state="disabled")
        
    def on_set(self):
        global fps
        fps = int(self.fpse.get().strip())
        print(fps)



def createnrun():
    app = Flask(__name__)
    sock = Sock(app)
    run_with_cloudflared(app)
    @sock.route('/getid')

    def getid(ws):
        while True:
            
            e = eyeids[ce]
            m = mouthids[cm]
            ws.send(json.dumps({"eyes": f"rbxassetid://{e}","mouth": f"rbxassetid://{m}"}))
            time.sleep(1/float(30))
    def runapp():
        app.run(host='0.0.0.0',port=8000, use_reloader=False)
    if __name__ == "__main__":
        threading.Thread(target=runapp).start()
gui = Application(root)

def monitor_url():
    global gui
    while True:
        time.sleep(1)
        
        url = get_cloudflared_url()

        if url:
            gui = Application(root)
            gui.urle.config(state="normal")
            gui.urle.delete(0, tk.END)
            gui.urle.insert(0, f"{url}")
            break
            
        

    
if __name__ == "__main__":
    threading.Thread(target=createnrun).start()
    threading.Thread(target=monitor_url).start()

if __name__ == "__main__":

    
    root.mainloop()

