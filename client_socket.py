# -*- coding:utf-8 -*-
import socket
import numpy as np
import time

def init(host,port):
    global client
    #接続設定
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    A = client.connect((host,port))


def rece():   #受信
    recedata = client.recv(4096)
    recedata = np.fromstring(recedata, dtype=np.int16)
    if recedata.shape[0] >= 8:
        recedata = recedata[:8]
    data = []
    for i in range (len(recedata)):
        data.append(int(recedata[i]))
#    responce = np.reshape(recedata, (2,5))
    return data


def send(data):   #送信
#    data = data.flatten()
    client.send(data)


if __name__ == "__main__":
    host = "192.168.2.100"
    port = 1111

    init(host,port)

    #受信
    recedata = rece()
