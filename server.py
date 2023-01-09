import socket
import cv2
import numpy as np
import sys

REC_SIZE = 64000

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the port
server_address = ("0.0.0.0", 10000)
sock.bind(server_address)

# Keep track of the cameras that are connected
cameras = {}

def exit():
    sys.exit()

def handle_camera(address, data):
    # If the client is not in the list of connected cameras, add it
    if address not in cameras:
        cv2.namedWindow(f'Frame from {address}', cv2.WINDOW_NORMAL)
        cameras[address] = []
    #check if the data dows not collaps
    #print(data)
    if(data[:3] == b'STR'): 
        print("STR")
        cameras[address] = []
    if(data[-3:] == b'END'):
        print("END")
    # Append the data to the list of data for this camera
    cameras[address].append(data)
    # Concatenate all the data chunks
    image_data = b''.join(cameras[address])
    # If all the data chunks have been received, display the image
    if b'END' == image_data[-3:] and b'STR' ==image_data[:3]:
        print("Entered")
        # Remove the END and STR chunk 
        image_data = image_data[3:-3]

        # Display the image
        try:
            frame = cv2.imdecode(np.fromstring(image_data, dtype=np.uint8), 1)
            cv2.imshow(f'Frame from {address}', frame)
            cv2.waitKey(1)
            key = cv2.waitKey(1)
            if key == 27:
                exit()
        # Clear the data for this camera
        except cv2.error as error:
            print("[Error]: {}".format(error))
        finally:
            cameras[address] = []

while True:
    # Receive data from a client
    data, address = sock.recvfrom(REC_SIZE)
    handle_camera(address, data)
    """
    # Create a new thread to handle this camera
    t = threading.Thread(target=handle_camera, args=(address, data))
    t.start()"""

cv2.destroyAllWindows()
sock.close()