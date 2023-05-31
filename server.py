import socket
import threading
import cv2
import numpy as np
import sys
import tkinter as tk
import PIL.Image, PIL.ImageTk
import ctypes
import re
import sqlite3
import select
import pandas as panda
import time
from datetime import datetime

# The UDP server for the getting the images.
REC_SIZE = 64000
global canvas_list
canvas_list = []
# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Bind the socket to the port
server_address = ("0.0.0.0", 10000)
sock.bind(server_address)

global image_file
image_file = r'C:\Users\Ort Holon 2\Downloads\Connecting.png'

# the TCP server for logging-in and signing-up
open_sockets = []
listening_socket = socket.socket()
TCP_server_address = ("0.0.0.0", 11111)
listening_socket.bind(TCP_server_address)
listening_socket.listen(1)

global cameras
global first_frame
# Keep track of the cameras that are connected
cameras = {}
# keep track of the last frame of each camera.
first_frame = {}
global canvas_id
canvas_id = []  # list of the canvases from 1 to 12
global camera_canvas
camera_canvas = {}
global image_container
image_container = {}
global canvas_to_address
canvas_to_address = {}

global window
window = tk.Tk()
print("ok")

# this part is for the motion detection
# List of all the tracks when there is any detected of motion in the frames
global motionTrackList
motionTrackList = [None, None]
# A new list 'time' for storing the time when movement detected
global motionTime
motionTime = []
# Initialising DataFrame variable 'dataFrame' using pandas libraries panda with Initial and Final column
global dataFrame
dataFrame = panda.DataFrame(columns=["Initial", "Final"])

# this part is the data base

global sqlite_file
sqlite_file = r'db_server.sqlite'
conn = sqlite3.connect(sqlite_file)
c = conn.cursor()
# get the count of tables with the name
c.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='users_table' ''')
# if the count is 1, then table exists
if c.fetchone()[0] == 1:
    print('Table exists.')
# else create table
else:
    # Creating a new SQLite table with 1 column
    c.execute("""CREATE TABLE users_table
                  (password TEXT, user_name TEXT, email TEXT PRIMARY KEY)""")

    # Committing changes and closing the connection to the database file
    conn.commit()
conn.close()


def insert_row(user_pass, user_name, email):
    # Connecting to the database file
    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    sql_str = """INSERT INTO users_table VALUES ('{pswrd}', '{us}', '{eml}')""".format(pswrd=user_pass, us=user_name,
                                                                                       eml=email)

    try:
        c.execute(sql_str)
    except sqlite3.IntegrityError:
        print('ERROR: ID already exists in PRIMARY KEY column {}'.format(email))

    # Committing changes and closing the connection to the database file
    conn.commit()
    conn.close()


def query_user(email):
    # Connecting to the database file
    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    sql_str = """SELECT * FROM users_table WHERE email='{eml}'""".format(eml=email)
    c.execute(sql_str)
    all_rows = c.fetchall()
    if (len(all_rows) > 0):
        print(all_rows[0][0], all_rows[0][1], all_rows[0][2])

    # Closing the connection to the database file
    conn.close()
    print(all_rows)
    return all_rows


# end of database

# change the size of the first 4 canvases
def check_all_sizes():
    if (len(canvas_list) < 5):
        pass


def exit():
    sys.exit()


def handle_cameras():
    #while True:
    data, address = sock.recvfrom(REC_SIZE)
    # If the client is not in the list of connected cameras, add it
    if address not in cameras:
        cameras[address] = []
        label = tk.Label(image=photo)
        label.pack()
        #c = tk.Canvas(window)
        #c.grid(row=j, column=i)
        #c.pack()
        canvas_id.append(label)
        #image_container[c] = c.create_image(0, 0, anchor='nw', image=photo)
        camera_canvas[address] = canvas_id[len(cameras) - 1]
        #camera_canvas[address].delete(image_container[camera_canvas[address]])#delete the connecting image
        canvas_to_address[canvas_id[len(cameras) - 1]] = address
        #window.update()
    # check if the data dows not collaps
    # print(data)
    if (data[:3] == b'STR'):
        print("STR")
        cameras[address] = []
    if (data[-3:] == b'END'):
        print("END")
    # Append the data to the list of data for this camera
    cameras[address].append(data)
    # Concatenate all the data chunks
    image_data = b''.join(cameras[address])
    # If all the data chunks have been received, display the image
    if b'END' == image_data[-3:] and b'STR' == image_data[:3]:
        global motionTrackList
        print("Entered")
        # Remove the END and STR chunk
        image_data = image_data[3:-3]
        # Display the image
        # Defining 'motion' variable equal to zero as initial frame
        var_motion = 0
        try:
            frame = cv2.imdecode(np.frombuffer(image_data, dtype=np.uint8), 1)
            frame = cv2.resize(frame, (450, 350))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # From colour images creating a gray frame
            gray_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # To find the changes creating a GaussianBlur from the gray scale image
            gray_frame = cv2.GaussianBlur(gray_image, (21, 21), 0)
            lab = camera_canvas[address]
            if address not in first_frame:  # set the first frame for each camera
                data = PIL.Image.fromarray(frame)  # converting a cv2 frame to an image.
                display = PIL.ImageTk.PhotoImage(data)
                first_frame[address] = gray_frame
                lab.configure(image=display)
                lab.image = display
            # Calculation of difference between static or initial and gray frame we created
            differ_frame = cv2.absdiff(first_frame[address], gray_frame)
            # the change between static or initial background and current gray frame are highlighted
            thresh_frame = cv2.threshold(differ_frame, 30, 255, cv2.THRESH_BINARY)[1]
            thresh_frame = cv2.dilate(thresh_frame, None, iterations=2)
            # For the moving object in the frame finding the coutours
            cont, _ = cv2.findContours(thresh_frame.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cur in cont:
                if cv2.contourArea(cur) < 5000:
                    continue
                var_motion = 1
                (cur_x, cur_y, cur_w, cur_h) = cv2.boundingRect(cur)
                # To create a rectangle of green color around the moving object
                cv2.rectangle(frame, (cur_x, cur_y), (cur_x + cur_w, cur_y + cur_h), (0, 255, 0), 3)
            # from the frame adding the motion status
            motionTrackList.append(var_motion)
            motionTrackList = motionTrackList[-2:]
            # Adding the Start time of the motion
            if motionTrackList[-1] == 1 and motionTrackList[-2] == 0:
                motionTime.append(datetime.now())
            # Adding the End time of the motion
            if motionTrackList[-1] == 0 and motionTrackList[-2] == 1:
                motionTime.append(datetime.now())
            data = PIL.Image.fromarray(frame)  # converting a cv2 frame to an image.
            display = PIL.ImageTk.PhotoImage(data)
            lab.configure(image=display)
            lab.image = display
            #image_container[c] = c.create_image(0, 0, anchor='nw', image=display)
            #c.itemconfig(image_container[c], image=display)
            #window.update()
        # Clear the data for this camera
        except Exception as e:
            sys.setrecursionlimit(sys.getrecursionlimit() + 10000)
            print("[Error]: {}".format(e))
        finally:
            cameras[address] = []
    #window.update_idletasks()
    window.update()

    window.after(0, handle_cameras)  # crytical part - won't work without this line - calling the same function after 0 secends



def TCP_server():
    while True:
        allSock = [listening_socket] + open_sockets
        rlist, _, _ = select.select(allSock, allSock, [])
        for TCP_sock in rlist:
            if TCP_sock is listening_socket:
                client_socket, _ = listening_socket.accept()
                open_sockets.append(client_socket)
            else:
                data = TCP_sock.recv(1024).decode()
                if (not data == ""):
                    print(f"Server recieved: {data}")
                    if (data[0] == "S"):  # the sign up proces
                        data = data.split(',')
                        email = data[2]
                        print(query_user(email))
                        if (query_user(email) == []):  # checking if email is new
                            insert_row(data[3], data[1], email)
                            TCP_sock.send("con".encode())
                        else:  # email already in db
                            TCP_sock.send("This mail already exists".encode())
                    if (data[0] == "L"):  # Log in proces
                        data = data.split(',')
                        email = data[1]
                        query = query_user(email)
                        print("this is query:", query)
                        if (query == []):
                            TCP_sock.send("Account not found - wrong email".encode())
                        elif (query[0][0] == data[2]):  # check password
                            TCP_sock.send("conL".encode())
                        else:
                            TCP_sock.send("wrong password".encode())
                # check if data is correct, and if so dissconect client
                rlist.remove(TCP_sock)
                allSock.remove(TCP_sock)


if __name__ == "__main__":
    print("main")
    # Create a new thread to handle this camera
    t = threading.Thread(target=handle_cameras)
    t2 = threading.Thread(target=TCP_server)

    # this is the gui part. The images on the background are the connecting image.
    window.state('zoomed')
    window.title = ("Cameras:")

    img = PIL.Image.open(image_file)
    photo = PIL.ImageTk.PhotoImage(img)

    # the white blocks are because the image is blocking the video - false
    """
    for i in range(4):
        for j in range(3):
            c = tk.Canvas(window)
            c.grid(row=j, column=i)
            canvas_id.append(c)
            image_container[c] = c.create_image(0, 0, anchor='nw', image=photo)
            window.update()"""
    print(image_container)
    #t.start()
    t2.start()
    handle_cameras()
    window.mainloop()

window.mainloop()

cv2.destroyAllWindows()
sock.close()