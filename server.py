import base64
import cv2 as cv
import numpy as np
import paho.mqtt.client as mqtt
from ultralytics import YOLO
import supervision as sv
from threading import Thread
import time
import csv
import datetime

"""
Su un PC a bordo veicolo a cui è connessa la videocamera si andrà ad effettuare inferenza sullo stato del conducente e
si andrà a misurare il tempo necessario a svolgere l inferenza, così come la CPU necessaria.
"""

MQTT_BROKER = "100.118.30.10"
MQTT_RECEIVE = "veicolo/Lancia_Y/videoStream/"
MQTT_SEND = "tele/Lancia_Y/20000/0/"

model = YOLO("best.pt")
frame = np.zeros((480, 680, 3), np.uint8)
client = mqtt.Client()
print("Iniz Valori")

box_annotator = sv.BoxAnnotator(
    thickness=2,
    text_thickness=2,
    text_scale=1
)

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe(MQTT_RECEIVE)


def on_message(client, userdata, msg):
    global frame
    img = base64.b64decode(msg.payload)
    npimg = np.frombuffer(img, dtype=np.uint8)
    frame = cv.imdecode(npimg, 1)

def start():
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER)
    client.loop_start()


def loop():
    global frame
    print("Avvio Loop")
    now = datetime.datetime.now()
    f1 = open(rf"{now.year}{now.month}{now.day}_{now.hour}{now.minute}{now.second}.csv", "x", encoding='UTF8', newline='')
    
    while True:
        start = time.time()
        result = model(frame, max_det=1)[0]
        detections = sv.Detections.from_yolov8(result)
        print(detections.class_id)
        frame = box_annotator.annotate(scene=frame, detections=detections)
        timer = datetime.datetime.now()
        timestamp=str(timer.day)+'/'+str(timer.month)+'/'+str(timer.year)+' '+str(timer.hour)+':'+str(timer.minute)+':'+str(timer.second)
        message='{\"tmstp\":\"'+timestamp+'\",\"e\":[{\"n\":0,\"v\":"Object detection"},{\"n\":1,\"v\":"CNN"},{\"n\":2,\"v\":'+str(3.30)+'},{\"n\":4,\"v\":"'
        cv.imshow("Stream", frame)
        risultato = "no_detection"
        id = detections.class_id
        if(id == 0):
            risultato = "awake"
        elif(id == 1):
            risultato = "closed"
        elif(id == 2):
            risultato = "sleep"
        result = str(message) + str(risultato) + '\"}]}'
        client.publish(MQTT_SEND, result)
        file = client.publish(MQTT_SEND, result)
        print(file)
        print(len(file))
        end = time.time()
        t = end - start
        writer_1 = csv.writer(f1)
        writer_1.writerow([str(now.hour)  +":"+str(now.minute) + ":" + str(now.second) + " " + str(t) +" "+ str(result)])
        print("Inference time "+ str(t))

        if cv.waitKey(1) & 0xFF == ord('q'):
            break

def loop_stop():
    client.loop_stop()

if __name__ == "__main__":
    
    thread1 = Thread(target=start)
    thread2 = Thread(target=loop)
    thread3 = Thread(target=loop_stop)

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()
    
    thread3.start()
    thread3.join()