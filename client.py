import cv2
import socket
import numpy as np
import sys

REC_SIZE = 64000-3

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = ('x.x.x.x', 10000) #replace x.x.x.x with the server ip

# Initialize the camera
camera = cv2.VideoCapture(0) #0 is for the default camera

def send_frame(frame):
    # Encode the frame as JPEG
    _, enc_frame = cv2.imencode('.jpg', frame)
    print(len(enc_frame))

    # Split the data into chunks (that will allways be 2 chunks)
    chunks = [enc_frame[:REC_SIZE],enc_frame[REC_SIZE:]]

    # Send the chunks to the server
    #Send the STR chunk signal at the start of the first chunk
    sock.sendto(b'STR'+bytes(chunks[0]), server_address)
    sock.sendto(bytes(chunks[1])+b'END', server_address)
    # Send the END chunk to signal the end of the image data


while True:
    #
    ret, frame = camera.read()
    
    send_frame(frame)
