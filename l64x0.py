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
import numpy as np
import client_socket as sock
import getkey
import read_sensor as RS
import threading

#movelist status
movesum = [0,0,0,0,0,0,0]

#socket initialize
host = "192.168.2.100"
port = 1111

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

#sensor pin initialize
rb, r6, r5, r4, r3, r2, r1 = (20,19,16,13,12,6,5)
#lb, l6, l5, l4, l3, l2, l1 = (20,19,16,13,12,6,5)
senR = np.array([rb, r6, r5, r4, r3, r2, r1]) 
#senL = np.array([lb, l6, l5, l4, l3, l2, l1]) 
z_zero, z_max = (21, 26)
GPIO.setup(r1, GPIO.IN)
GPIO.setup(r2, GPIO.IN)
GPIO.setup(r3, GPIO.IN)
GPIO.setup(r4, GPIO.IN)
GPIO.setup(r5, GPIO.IN)
GPIO.setup(r6, GPIO.IN)
GPIO.setup(rb, GPIO.IN)
GPIO.setup(z_zero, GPIO.IN)
GPIO.setup(z_max, GPIO.IN)

#driver pin initialize
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
#    L6470_softhiz(n_dchain)
	L6480_softstop()
#    GPIO.cleanup()
	sys.exit()

def end():
	print("*** end ***")
	L6470_softstop(n_dchain)
	L6470_softhiz(n_dchain)
	L6480_softhiz()
	L6480_softstop()
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
	if (GPIO.input(BUSY_PIN_1) == 1):

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

		print("***L6480 MOVE***")

	else:
		pass

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
	global movesum
	movesum = [x + y for (x,y) in zip(movesum, step)]

	if (GPIO.input(BUSY_PIN_0) == 1):
		#Reversed by the direction of the motor.
		step[6] = step[6] * -1#motor1
		step[5] = step[5] * -1#motor2
		step[2] = step[2] * -1#motor5
		step[0] = step[0] * -1#motorB
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
			L6470_write([movelist[j][0],movelist[j][1],movelist[j][2],movelist[j][3],movelist[j][4],movelist[j][5],movelist[j][6]])
		print("***L6480 MOVE***")

def L6470_gohome(n):
	L6470_write([0x70] * n)
	while (GPIO.input(BUSY_PIN_0) == 0):
		pass
	print("***OK GoHome***")

def L6470_resetpos(n):
	L6470_write([0xD8] * n)
	while (GPIO.input(BUSY_PIN_0) == 0):
		pass
	print("***OK ResetPos***")

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

def L6480_gohome():
	L6480_write([0x70])
	while (GPIO.input(BUSY_PIN_1) == 0):
		pass
	print("***OK GoHome Z***")

def L6480_resetpos():
	L6480_write([0xD8])
	while (GPIO.input(BUSY_PIN_1) == 0):
		pass
	print("***OK ResetPos Z***")

def L6480_softstop():
	L6480_write([0xB0])
	while (GPIO.input(BUSY_PIN_1) == 0):
		pass
	print("***Soft stop Z***")

def L6480_hardstop():
	L6480_write([0xB8])
	while (GPIO.input(BUSY_PIN_1) == 0):
		pass
	print("***Hard stop Z***")

def L6480_softhiz():
	L6480_write([0xA0])
	while (GPIO.input(BUSY_PIN_1) == 0):
		pass
	print("***Soft HiZ Z***")

def L6480_hardhiz():
	L6480_write([0xA8])
	while (GPIO.input(BUSY_PIN_1) == 0):
		pass
	print("***Hard HiZ Z***")



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
#	sock.send(np.array([0,0,0,0,0], dtype=np.int16))
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
	L6470_write([0x00] * n_dchain)
	L6470_write([0x50] * n_dchain)
	#L6470_write([0x03] * n_dchain)
	#L6470_write([0xFF] * n_dchain)
	#DEC
	L6470_write([0x06] * n_dchain)
	L6470_write([0x03] * n_dchain)
	L6470_write([0xFF] * n_dchain)
	#MAX_SPEED
	L6470_write([0x07] * n_dchain)
	L6470_write([0x00] * n_dchain)
	L6470_write([0x05] * n_dchain)
#	L6470_write([0x70] * n_dchain)
	#MIN_SPEED
	L6470_write([0x08] * n_dchain)
	L6470_write([0x00] * n_dchain)
	L6470_write([0x02] * n_dchain)
#	L6470_write([0x10] * n_dchain)
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
	#L6480_write([0x04])#
	#L6480_write([0x17])#
	L6480_write([0x00])
	#L6480_write([0x27])
	L6480_write([0x20])
	#L6480_write([0x03])
	#L6480_write([0xFF])
	#DEC
	L6480_write([0x06])
	L6480_write([0x04])
	L6480_write([0x16])
#    L6480_write([0x03])
#    L6480_write([0xFF])
	#MAX_SPEED
	L6480_write([0x07])
	L6480_write([0x00])
	L6480_write([0x19])
	#L6480_write([0x20])
#    L6480_write([0x00])
#    L6480_write([0x25])
	#MIN_SPEED
	L6480_write([0x08])
	L6480_write([0x00])
	L6480_write([0x00])
	#FS_SPEED
	L6480_write([0x15])
	L6480_write([0x00])
	L6480_write([0x27])
	#L6480_write([0x20])
	#KvaL_HOLD
	L6480_write([0x09])
	L6480_write([0x60])
#    L6480_write([0x48])
	#KvaL_RUN
	L6480_write([0x0A])
#    L6480_write([0x6E])#
	L6480_write([0x61])
#    L6480_write([0x46])
#    L6480_write([0x40])
	#KvaL_ACC
	L6480_write([0x0B])
#    L6480_write([0x60])
	L6480_write([0x63])
#    L6480_write([0x46])
	#KvaL_DEC
	L6480_write([0x0C])
#    L6480_write([0x60])
	L6480_write([0x46])
	#INT_SPEED
	L6480_write([0x0D])
	L6480_write([0x00])#
	#L6480_write([0x10])#
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
	L6480_write([0xC2])
#	L6480_write([0xDE])#
#	L6480_write([0x1E])
	L6480_write([0x81])

def zero_arm():
	global movesum
	movesum = [0,0,0,0,0,0,0]
	L6470_gohome(n_dchain)
#	L6470_softhiz(n_dchain)
#	for cont in range(9):                     #10回繰り返す
#		movedata = [0,0,0,0,0,0,0]            #movedata initialize
#		for pin in range(len(senR)):
#			if RS.readsens(senR[pin]) == 1:   #ゼロ点ではないとき 
#				movedata[pin] = -6400
#		L6470_move(movedata, n_dchain)
	print("***OK zero_arm***")
	L6470_softstop(n_dchain)
	L6470_softhiz(n_dchain)
#	L6470_resetpos(n_dchain)

def zero_table():
	#L6480_gohome()

	while RS.readsens(z_zero) == 1:     #ゼロ点でないとき
		L6480_move(-16000)	
	L6480_softstop()
	print("***OK zero Table***")
	L6480_resetpos()

#	for cont in range(10):
#		time.sleep(0.5)
#		if RS.readsens(z_zero) == 1:     #ゼロ点でないとき
#			L6480_move(-6400)            #Table 2mm UP
#		elif RS.readsens(z_zero) == 0:   #ゼロ点であるとき
#			L6480_softstop()
#			print("***OK zero Table***")
#			L6480_resetpos()
#			break

def debug():
	print("debug  mode")
	while 1:
		key = getkey.getkey()
		if key == 27:  #esc #終了
			end()
			break
		if key == 49:  #1   #L1
			L6470_move([0,0,0,0,0,0,25600], n_dchain)
			#act1 = threading.Thread(target = L6470_move([0,256000,0,0,0,0,512000], n_dchain))
			#act2 = threading.Thread(target = L6480_move(128000))#-40mm
			#act1.start()
			#act2.start()
			#L6480_softstop()
		if key == 113:  #Q   #L1
			L6470_move([0,0,0,0,0,0,-25600], n_dchain)
		if key == 50:  #2   #L2
			L6470_move([0,0,0,0,0,25600,0], n_dchain)
		if key == 119:  #W   #L2
			L6470_move([0,0,0,0,0,-25600,0], n_dchain)
		if key == 51:  #3   #L3
			L6470_move([0,0,0,0,25600,0,0], n_dchain)
		if key == 101:  #E   #L3
			L6470_move([0,0,0,0,-25600,0,0], n_dchain)
		if key == 52:  #4   #L4
			L6470_move([0,0,0,25600,0,0,0], n_dchain)
		if key == 114:  #R   #L4
			L6470_move([0,0,0,-25600,0,0,0], n_dchain)
		if key == 53:  #5   #L5
			L6470_move([0,0,25600,0,0,0,0], n_dchain)
		if key == 116:  #T   #L5
			L6470_move([0,0,-25600,0,0,0,0], n_dchain)
		if key == 54:  #6   #L6
			L6470_move([0,25600,0,0,0,0,0], n_dchain)
		if key == 121:  #Y   #L6
			L6470_move([0,-25600,0,0,0,0,0], n_dchain)
		if key == 55:  #7   #LB
			L6470_move([25600,0,0,0,0,0,0], n_dchain)
		if key == 117:  #U   #LB
			L6470_move([-25600,0,0,0,0,0,0], n_dchain)
		if key == 32:  #space   #print movesum
			print(movesum)		
		
#		if key == 1792833:  #Over
#			L6470_move([0,0,0,0,0,0,117120], n_dchain)
#		if key == 1792834:  #Under
#			L6470_move([0,0,0,0,0,0,-117120], n_dchain)
#		if key == 1792835:  #Right
#			L6470_move([0,0,133851,44617,0,0,0], n_dchain)
#		if key == 1792836:  #Left
#			L6470_move([0,133851,0,44617,0,0,0], n_dchain)

		if key == 48:  #0   #ARM 0点合わせ
			zero_arm()
		if key == 115:  #S   #ARM ReestPos
			L6470_resetpos(n_dchain)
		if key == 56:  #8   #Table UP
#			L6480_move(-6400)  #2mm
#			L6480_move(-16000)  #5mm
#			L6480_move(-64000)  #20mm
#			L6480_move(-128000)  #40mm
			L6480_move(-320000)  #100mm
#			L6480_softstop()
		if key == 105:  #I   #Table DOWN
#			L6480_move(6400)   #2mm
#			L6480_move(16000)  #5mm
#			L6480_move(64000)   #20mm
#			L6480_move(128000)  #40mm
			L6480_move(320000)  #100mm
#			L6480_softstop()
		if key == 107:  #K   #Table UP
			L6480_move(-6400)  #2mm
			L6480_softstop()
		if key == 44:  #,   #Table DOWN
			L6480_move(6400)  #2mm
			L6480_softstop()
 
		if key == 112:  #P   #Table 0点合わせ
			zero_table()
			L6480_softstop()
		if key == 122:  #Z   #Table 0点ResetPos
			L6480_resetpos()
			print("***ResetPos Table***")

		if key == 10:  #enter   #Emergency stop
			z_zero = 0
			L6480_softstop()
			L6470_softstop(n_dchain)
			print("***Stop***")
###
		if key == 99:  #c   #demo
			act1 = threading.Thread(target = L6470_move([0,256000,256000,0,0,0,256000], n_dchain))
			act2 = threading.Thread(target = L6480_move(1184000))  #-370m
			act1.start()
			act2.start()
#			L6480_softstop()

def decoder(data):   
	if len(data) == 8:
		if data[7] == 0:
			movedata = data[:7]
			L6470_move(data, n_dchain)
		if data[7] >= 1:
			movedata = int(data[7])
			L6480_move(movedata)
			L6480_getstatus()

if __name__=="__main__":
	print("program start")
	signal.signal(signal.SIGINT, handler)
	L6470_init()
	L6480_init()

	#デバッグオプションで実行された時にdebug()に飛ばす
	try:
		if sys.argv[1] == "debug":
			debug()
	except IndexError:  #オプション無しで実行した場合
		pass


### socket通信###
#	sock.init(host,port)
#	try:
		#Reception
#		while True:
#			data = sock.rece()			
#			if len(data) == 1:
#				break
#			decoder(data)

#	finally:    #例外の発生に関係なく最後に処理を実行
#		print("***END Processing***")
#		L6470_gohome(n_dchain)
#		L6470_softhiz(n_dchain)
#		GPIO.cleanup()
###
