import cv2 as cv
from cv2 import CAP_PROP_FRAME_WIDTH
from cv2 import CAP_PROP_FRAME_HEIGHT
import paho.mqtt.client as mqtt
import base64
import time
from paho.mqtt import client as mqtt_client
from threading import Thread
import logging

print("Iniz Valori")
MQTT_BROKER = "100.118.30.10"
MQTT_SEND = "veicolo/DH339KV/videoStream/"
MQTT_RECEIVE = "tele/DH339KV/20000/0/"

cap = cv.VideoCapture(0)
client = mqtt.Client() 

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    client.subscribe(MQTT_RECEIVE)

def on_message(client, userdata, msg):
    print(f"Received {msg.payload.decode()}")
          
def start():
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER)
    client.loop_start()

def loop():
    print("Avvio Loop")
    while True:
        start = time.time()
        _, frame = cap.read()
        frame = cv.resize(frame, (640, 640))
        _, buffer = cv.imencode('.jpg', frame)
        cv.imshow("Stream",frame)
        jpg_as_text = base64.b64encode(buffer)
        client.publish(MQTT_SEND, jpg_as_text)
        frame_packet = client.publish(MQTT_SEND, jpg_as_text)
        print(frame_packet)
        end = time.time()
        t = end - start
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