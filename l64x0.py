#l647x.py
#SPI xfer, daisy chained l6470 and single l4680 motor driver control.
#Based on daisy_chain_8.py written by R. Murakami 2018.
# -*- coding: utf-8 -*-

import fcntl
import termios
import os
import signal
import spidev
import RPi.GPIO as GPIO
import time
import sys
import csv
import tkinter
import tkinter.filedialog as tkfd
import tkinter.messagebox as tkmsg
from tkinter import *
import tkinter as tk
import numpy as np

#SPI initialize.
spi = spidev.SpiDev()
spi.open(0,0)
#spi.open(0,1)
spi.max_speed_hz=(1000000)

#daisy chain number
n_dchain = 7

#GPIO initialize.
#L6470 pin connection
BUSY_PIN_0 = 2 
CS_PIN = 3
CS_PIN_1 = 15
#L6480 pin connection
BUSY_PIN_1 = 17
#BUSY_PIN_1 = 20
STBY_PIN_1 = 22

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUSY_PIN_0,GPIO.IN)
GPIO.setup(BUSY_PIN_1,GPIO.IN)
GPIO.setup(STBY_PIN_1,GPIO.OUT)
GPIO.setup(CS_PIN,GPIO.OUT)
GPIO.setup(CS_PIN_1,GPIO.OUT)
GPIO.output(CS_PIN,GPIO.HIGH)
GPIO.output(CS_PIN_1,GPIO.HIGH)

#L6480 reset
GPIO.output(STBY_PIN_1,GPIO.LOW)
time.sleep(0.01)
GPIO.output(STBY_PIN_1,GPIO.HIGH)
time.sleep(0.01)

def handler(signal, frame):
    print("***Ctrl + c***")
    L6470_softstop(n_dchain)
    L6470_softhiz(n_dchain)
    GPIO.cleanup()
    sys.exit()
    
def end():
    print("*** end ***")
    L6470_softstop(n)
    L6470_hiz(n)
    GPIO.cleanup()
    sys.exit()

#L64x0 command
def L6470_write(dlist):
    GPIO.output(CS_PIN,GPIO.LOW)
    time.sleep(0.005)
    spi.xfer2(dlist)
    GPIO.output(CS_PIN,GPIO.HIGH)
    time.sleep(0.005)

#L64x0 command
def L6480_write(data):
    GPIO.output(CS_PIN_1,GPIO.LOW)
    time.sleep(0.005)
    spi.xfer2(data)
    GPIO.output(CS_PIN_1,GPIO.HIGH)
    time.sleep(0.005)

def L6480_move(n_step):
    if (n_step < 0):
        dir = 0x40
        stp = -1 * n_step
    else:
        dir = 0x41
        stp = n_step

    #Dec 2 Hex. 
    stp_h   = (0x3F0000 & stp) >> 16 
    stp_m   = (0x00FF00 & stp) >> 8 
    stp_l   = (0x0000FF & stp)

    L6480_write([dir])

    L6480_write([stp_h])
    L6480_write([stp_m])
    L6480_write([stp_l]) 

    while (GPIO.input(BUSY_PIN_1) == 0):
        pass
    print("***L6480 MOVE***")

def L6470_run(speed, n):
    #initialize movelist.
    spdlist = [[0 for i in range(n)]for j in range(4)]
    print(movelist) 
    for i in range(n):
        n_spd = speed[i]

        if (n_spd < 0):
            dir = 0x50
            spd = -1 * n_spd
        else:
            dir = 0x51
            spd = n_spd

        #Dec 2 Hex. 
        spd_h   = (0x3F0000 & spd) >> 16 
        spd_m   = (0x00FF00 & spd) >> 8 
        spd_l   = (0x0000FF & spd)
        
        spdlist[0][i] = dir
        spdlist[1][i] = spd_h
        spdlist[2][i] = spd_m
        spdlist[3][i] = spd_l
    
    for j in range(4):
        L6470_write([spdlist[j][0],spdlist[j][1],spdlist[j][2]])
    
    while (GPIO.input(BUSY_PIN_0) == 0):
        pass
    print("***OK run***")

def L6470_move(step, n):
    #initialize movelist.
    movelist = [[0 for i in range(n)]for j in range(4)]
    for i in range(n):
        n_step = step[i]

        if (n_step < 0):
            dir = 0x40
            stp = -1 * n_step
        else:
            dir = 0x41
            stp = n_step

        #Dec 2 Hex. 
        stp_h   = (0x3F0000 & stp) >> 16 
        stp_m   = (0x00FF00 & stp) >> 8 
        stp_l   = (0x0000FF & stp)
        
        movelist[0][i] = dir
        movelist[1][i] = stp_h
        movelist[2][i] = stp_m
        movelist[3][i] = stp_l
    
    for j in range(4):
        L6470_write([movelist[j][0],movelist[j][1],movelist[j][2]])
    
    while (GPIO.input(BUSY_PIN_0) == 0):
        pass
    print("***OK MOVE***")

def L6470_gohome(n):
    L6470_write([0x70] * n)
    while (GPIO.input(BUSY_PIN_0) == 0):
        pass
    print("***OK GoHome***")

def L6470_softstop(n):
    L6470_write([0xB0] * n)
    while (GPIO.input(BUSY_PIN_0) == 0):
        pass
    print("***Soft stop***")

def L6470_hardstop(n):
    L6470_write([0xB8] * n)
    while (GPIO.input(BUSY_PIN_0) == 0):
        pass
    print("***Hard stop***")

def L6470_softhiz(n):
    L6470_write([0xA0] * n)
    while (GPIO.input(BUSY_PIN_0) == 0):
        pass
    print("***Soft HiZ***")

def L6470_hardhiz(n):
    L6470_write([0xA8] * n)
    while (GPIO.input(BUSY_PIN_0) == 0):
        pass
    print("***Hard HiZ***")

def L6470_hardhiz(n):
    L6470_write([0xA8] * n)
    while (GPIO.input(BUSY_PIN_0) == 0):
        pass
    print("***Hard HiZ***")

#Does not work.
#def L6470_getstatus(n):
#    L6470_write([0xD8] * n)
#    GPIO.output(CS_PIN,GPIO.LOW)
#    resp1 = spi.xfer2([0x00] * n)
#    GPIO.output(CS_PIN_1,GPIO.HIGH)
#    time.sleep(0.005)
#    GPIO.output(CS_PIN,GPIO.LOW)
#    resp2 = spi.xfer2([0x00]*n)
#    while (GPIO.input(BUSY_PIN_0) == 0):
#        pass
#    print(resp1,resp2)

def L6480_getstatus():
    L6480_write([0xD0])
    GPIO.output(CS_PIN_1,GPIO.LOW)
    resp1 = spi.xfer2([0x00])
    GPIO.output(CS_PIN_1,GPIO.HIGH)
    time.sleep(0.005)
    GPIO.output(CS_PIN_1,GPIO.LOW)
    resp2 = spi.xfer2([0x00])
    GPIO.output(CS_PIN_1,GPIO.HIGH)
    print("*** STATUS ***")
    print('{0:08b}'.format(resp1[0],'b'))
    print('{0:08b}'.format(resp2[0],'b'))
    while (GPIO.input(BUSY_PIN_1) == 0):
        pass

def L6470_init():
    #reset device.
    L6470_write([0x00] * n_dchain)
    L6470_write([0x00] * n_dchain)
    L6470_write([0x00] * n_dchain)
    L6470_write([0x00] * n_dchain)
    L6470_write([0xc0] * n_dchain)
    #ACC
    L6470_write([0x05] * n_dchain)
    L6470_write([0x03] * n_dchain)
    L6470_write([0xFF] * n_dchain)
    #DEC
    L6470_write([0x06] * n_dchain)
    L6470_write([0x03] * n_dchain)
    L6470_write([0xFF] * n_dchain)
    #MAX_SPEED
    L6470_write([0x07] * n_dchain)
    L6470_write([0x00] * n_dchain)
    L6470_write([0x70] * n_dchain)
    #MIN_SPEED
    L6470_write([0x08] * n_dchain)
    L6470_write([0x00] * n_dchain)
    L6470_write([0x10] * n_dchain)
    #FS_SPEED
    L6470_write([0x15] * n_dchain)
    L6470_write([0x00] * n_dchain)
    L6470_write([0x27] * n_dchain)
    #KvaL_HOLD
    L6470_write([0x09] * n_dchain)
    L6470_write([0x20] * n_dchain)
    #KvaL_RUN
    L6470_write([0x0A] * n_dchain)
    L6470_write([0x35] * n_dchain)
    #KvaL_ACC
    L6470_write([0x0B] * n_dchain)
    L6470_write([0x40] * n_dchain)
    #KvaL_DEC
    L6470_write([0x0C] * n_dchain)
    L6470_write([0x20] * n_dchain)
    #INT_SPEED
    L6470_write([0x0D] * n_dchain)
    L6470_write([0x04] * n_dchain)
    L6470_write([0x08] * n_dchain)
    #ST_SLP
    L6470_write([0x0E] * n_dchain)
    L6470_write([0x19] * n_dchain)
    #FN_SLP_ACC
    L6470_write([0x0F] * n_dchain)
    L6470_write([0x29] * n_dchain)
    #FN_SLP_DEC
    L6470_write([0x10] * n_dchain)
    L6470_write([0x29] * n_dchain)
    #K_THERM
    L6470_write([0x11] * n_dchain)
    L6470_write([0x00] * n_dchain)
    #OCD_TH
    L6470_write([0x13] * n_dchain)
    L6470_write([0x07] * n_dchain)
    #STALL_TH
    L6470_write([0x14] * n_dchain)
    L6470_write([0x40] * n_dchain)
    #STEP_MODE
    L6470_write([0x16] * n_dchain)
    L6470_write([0x07] * n_dchain)
    #ALARM_EN
    L6470_write([0x17] * n_dchain)
    L6470_write([0xFF] * n_dchain)
    #CONFIG
    L6470_write([0x18] * n_dchain)
    L6470_write([0x2E] * n_dchain)
    L6470_write([0x88] * n_dchain)

def L6480_init():
    #reset device.
    L6480_write([0x00])
    L6480_write([0x00])
    L6480_write([0x00])
    L6480_write([0x00])
    L6480_write([0xc0])
    #ACC
    L6480_write([0x05])
    L6480_write([0x03])
    L6480_write([0xFF])
    #DEC
    L6480_write([0x06])
    L6480_write([0x03])
    L6480_write([0xFF])
    #MAX_SPEED
    L6480_write([0x07])
    L6480_write([0x00])
    L6480_write([0x25])
    #MIN_SPEED
    L6480_write([0x08])
    L6480_write([0x00])
    L6480_write([0x00])
    #FS_SPEED
    L6480_write([0x15])
    L6480_write([0x00])
    L6480_write([0x27])
    #KvaL_HOLD
    L6480_write([0x09])
    L6480_write([0x15])
    #KvaL_RUN
    L6480_write([0x0A])
    L6480_write([0x46])
    #KvaL_ACC
    L6480_write([0x0B])
    L6480_write([0x46])
    #KvaL_DEC
    L6480_write([0x0C])
    L6480_write([0x46])
    #INT_SPEED
    L6480_write([0x0D])
    L6480_write([0x00])#
    L6480_write([0x00])#
    #ST_SLP
    L6480_write([0x0E])
    L6480_write([0x35])#
    #FN_SLP_ACC
    L6480_write([0x0F])
    L6480_write([0x40])#
    #FN_SLP_DEC
    L6480_write([0x10])
    L6480_write([0x70])#
    #K_THERM
    L6480_write([0x11])
    L6480_write([0x00])
    #OCD_TH
    L6480_write([0x13])
    L6480_write([0x17])
    #STALL_TH
    L6480_write([0x14])
    L6480_write([0x02])#
    #STEP_MODE
    L6480_write([0x16])
    L6480_write([0x07])
    #ALARM_EN
    #L6480_write([0x17])
    #L6480_write([0xFF])
    #GATECFG1
    L6480_write([0x18])
    L6480_write([0x00])
    L6480_write([0x57])
    #GATECFG2
    L6480_write([0x19])
    L6480_write([0x89])
    #CONFIG
    L6480_write([0x1A])
    L6480_write([0x1E])
    L6480_write([0x81])


if __name__=="__main__":
    print("program start")
    signal.signal(signal.SIGINT, handler)
    L6470_init()
    L6480_init()

    L6470_softstop(n_dchain)
    stp = [25600*2] * 7  
    L6470_move(stp, n_dchain)
    L6470_gohome(n_dchain)
    L6470_softhiz(n_dchain)

    L6480_getstatus()
    L6480_move(25600)
    L6480_getstatus()
    #L6470_getstatus(n_dchain)
    GPIO.cleanup()
