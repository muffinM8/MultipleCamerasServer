import cv2
import socket
import threading
import numpy as np
import sys
import sqlite3
import tkinter as tk
import re
import ctypes
import rsa

REC_SIZE = 64000 - 3

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = ('192.168.3.22', 10000)
TCP_server_address = ('192.168.3.22', 11111)

# Initialize the camera
camera = cv2.VideoCapture(0)

global path_rsa
path_rsa = r'C:\Users\Ort Holon 2\MultipleCamerasServer'

#encryption
def generateKeys():
    (publicKey, privateKey) = rsa.newkeys(1024)
    with open('publcKeyCL.pem', 'wb') as p:
        p.write(publicKey.save_pkcs1('PEM'))
    with open('privateKeyCL.pem', 'wb') as p:
        p.write(privateKey.save_pkcs1('PEM'))

def load_keys():
    global path_rsa
    with open(path_rsa + '\publcKeyCL.pem', 'rb') as p:
        publicKey = rsa.PublicKey.load_pkcs1(p.read())
    with open(path_rsa + '\privateKeyCL.pem', 'rb') as p:
        privateKey = rsa.PrivateKey.load_pkcs1(p.read())
    return privateKey, publicKey

def encrypt(message, key):
    return rsa.encrypt(message, key)

def decrypt(ciphertext, key):
    try:
        return rsa.decrypt(ciphertext, key)
    except:
        return False

generateKeys()
global public_key, private_key
private_key, public_key = load_keys()

def send_frame(frame):
    # Encode the frame as JPEG
    _, enc_frame = cv2.imencode('.jpg', frame)
    print(len(enc_frame))

    # Split the data into chunks (that will allways be 2 chunks)
    chunks = [enc_frame[:REC_SIZE], enc_frame[REC_SIZE:]]

    # Send the chunks to the server
    # Send the STR chunk signal at the start of the first chunk
    sock.sendto(b'STR' + bytes(chunks[0]), server_address)
    sock.sendto(bytes(chunks[1]) + b'END', server_address)
    # Send the END chunk to signal the end of the image data


def start_camera():
    while True:
        #
        _, frame = camera.read()

        send_frame(frame)


global base
base = tk.Tk()
base.geometry('500x500')
global frame
frame = tk.Frame(base)
frame.pack()


def send_info_to_server(en1, en2, en3=""):
    global priavte_key, server_public_key
    if (en3 == ""):  # login
        my_socket.send(encrypt(f'L,{en1},{en2}'.encode(),server_public_key))
        print(f"Sent data Log-in L,{en1},{en2}")
    else:  # sign up
        my_socket.send(encrypt(f'S,{en1},{en2},{en3}'.encode(),server_public_key))
        print(f"Sent data Log-in S,{en1},{en2},{en3}")
    data = my_socket.recv(1024)
    data = decrypt(data, private_key).decode()
    print(data)
    if (data == "This mail already exists"):
        ctypes.windll.user32.MessageBoxW(0, u"This mail already exists", u"Error", 0)
    elif (data == "wrong password"):
        ctypes.windll.user32.MessageBoxW(0, u"wrong password", u"Error", 0)
    elif (data == "Account not found - wrong email"):
        ctypes.windll.user32.MessageBoxW(0, u"Account not found - wrong email", u"Error", 0)
    elif (data == "con" or data == "conL"):
        global frame
        frame.destroy()
        base.destroy()
        start_camera()
    else:
        ctypes.windll.user32.MessageBoxW(0, u"something went wrong", u"Error", 0)
    if(en3==""):
        return
    sign_up()


def check_input_sign_up(en1, en2, en3):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    print("good")
    if (en1 == "" or en2 == "" or en3 == ""):
        ctypes.windll.user32.MessageBoxW(0, u"Not all Fields are full", u"Error", 0)
        sign_up()
    if (not re.fullmatch(regex, en2)):
        ctypes.windll.user32.MessageBoxW(0, u"Invalid Email", u"Error", 0)
        sign_up()
    send_info_to_server(en1, en2, en3)


def check_input_sign_in(en1, en2):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    print("bad")
    if (en1 == "" or en2 == ""):
        ctypes.windll.user32.MessageBoxW(0, u"Not all Fields are full", u"Error", 0)
        sign_in()
    if (not re.fullmatch(regex, en1)):
        ctypes.windll.user32.MessageBoxW(0, u"Invalid Email", u"Error", 0)
        sign_in()
    send_info_to_server(en1, en2)


def sign_in():
    print("Entered")
    global frame, base
    frame.destroy()
    frame = tk.Frame(base)
    frame.pack()
    base.title = ("Sing-in Form")

    labl_0 = tk.Label(frame, text="Sign-in form", width=20, font=("bold", 20))
    labl_0.pack()

    labl_2 = tk.Label(frame, text="Email", width=20, font=("bold", 10))
    labl_2.pack()

    entry_02 = tk.Entry(frame)
    entry_02.pack()

    labl_3 = tk.Label(frame, text="Password", width=20, font=("bold", 10))
    labl_3.pack()

    entry_03 = tk.Entry(frame, show="*")
    entry_03.pack()

    empty_space = tk.Label(frame, text="", width=20, font=("bold", 10))
    empty_space.pack()

    tk.Button(frame, command=lambda: check_input_sign_in(entry_02.get(), entry_03.get()), text='Submit', width=20,
              bg='brown', fg='white').pack()
    tk.Button(frame, command=sign_up, text='create a new account', width=20, bg='brown', fg='white').pack()

    base.mainloop()


def sign_up():
    global frame, base
    base.title = ("Registration Form")
    frame.destroy()
    frame = tk.Frame(base)
    frame.pack()

    labl_0 = tk.Label(frame, text="Registration form", width=20, font=("bold", 20))
    labl_0.pack()

    labl_1 = tk.Label(frame, text="FullName", width=20, font=("bold", 10))
    labl_1.pack()

    entry_1 = tk.Entry(frame)
    entry_1.pack()

    labl_2 = tk.Label(frame, text="Email", width=20, font=("bold", 10))
    labl_2.pack()

    entry_02 = tk.Entry(frame)
    entry_02.pack()

    labl_4 = tk.Label(frame, text="Password:", width=20, font=("bold", 10))
    labl_4.pack()

    entry_03 = tk.Entry(frame, show="*")
    entry_03.pack()

    empty_space = tk.Label(frame, text="", width=20, font=("bold", 10))
    empty_space.pack()

    tk.Button(frame, command=lambda: check_input_sign_up(entry_1.get(), entry_02.get(), entry_03.get()), text='Submit',
              width=20, bg='brown', fg='white').pack()
    tk.Button(frame, command=sign_in, text='Already have an account', width=20, bg='brown', fg='white').pack()

    base.mainloop()



global  server_public_key
my_socket = socket.socket()
my_socket.connect(TCP_server_address)
my_socket.send(public_key.save_pkcs1(format='DER'))
server_public_key = my_socket.recv(1024)
server_public_key = rsa.key.PublicKey.load_pkcs1(server_public_key, format='DER')
sign_in()


