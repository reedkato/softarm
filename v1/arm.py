#daisy_chain_8.py
#本格的にCSVからデータを貰いモーターを動かす。

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

#SPI初期設定
spi = spidev.SpiDev()
spi.open(0,1)
spi.max_speed_hz=(10000)

#GPIO初期設定
BUSY_PIN_0 = 5
BUSY_PIN_1 = 6
BUSY_PIN_2 = 4
#BUSY_PIN_3 = 17
#BUSY_PIN_4 = 27
#BUSY_PIN_5 = 22
CS_PIN = 13
#SELECT_PIN_1 = 6
GPIO.setmode(GPIO.BCM)
GPIO.setup(CS_PIN,GPIO.OUT)
GPIO.setup(BUSY_PIN_0,GPIO.IN)
GPIO.setup(BUSY_PIN_1,GPIO.IN)
GPIO.setup(BUSY_PIN_2,GPIO.IN)
#GPIO.setup(BUSY_PIN_3,GPIO.IN)
#GPIO.setup(BUSY_PIN_4,GPIO.IN)
#GPIO.setup(BUSY_PIN_5,GPIO.IN)
GPIO.output(CS_PIN,GPIO.HIGH)

def handler(signal, frame):
    print("***Ctrl + c***")
    GPIO.cleanup()
    sys.exit()
    
def end():
    print("*終了します***")
    GPIO.cleanup()
    sys.exit()

def getkey():
    fno = sys.stdin.fileno()

    #stdinの端末属性を取得
    attr_old = termios.tcgetattr(fno)

    # stdinのエコー無効、カノニカルモード無効
    attr = termios.tcgetattr(fno)
    attr[3] = attr[3] & ~termios.ECHO & ~termios.ICANON # & ~termios.ISIG
    termios.tcsetattr(fno, termios.TCSADRAIN, attr)

    # stdinをNONBLOCKに設定
    fcntl_old = fcntl.fcntl(fno, fcntl.F_GETFL)
    fcntl.fcntl(fno, fcntl.F_SETFL, fcntl_old | os.O_NONBLOCK)

    chr = 0

    try:
        # キーを取得
        c = sys.stdin.read(1)
        if len(c):
            while len(c):
                chr = (chr << 8) + ord(c)
                c = sys.stdin.read(1)
    finally:
        # stdinを元に戻す
        fcntl.fcntl(fno, fcntl.F_SETFL, fcntl_old)
        termios.tcsetattr(fno, termios.TCSANOW, attr_old)

    return chr

# ボタンの状態を変更
def change_state():
    global buttons
    if flag.get():
        #print(flag.get())
        new_state = 'normal'
    else:
        #print(flag.get())
        new_state = 'disabled'
    for b in buttons:
        b.configure(state = new_state)

def win_build(self):
    global label2
    global flag
    global buttons
    global v
    root.minsize(750,300)
    root.maxsize(750,300)
    #ウィンドウのタイトル名と表示位置、大きさ
    root.title("SoftRobotics_Controller")
    root.geometry()
    
    #ラジオボタン用ブーリアン型
    flag = tk.BooleanVar()
    flag.set(False)
    v = IntVar()
    v.set(0)
    buttons = []

    self.frame1 = tk.Frame(self)
    self.frame1.pack()
    self.frame2 = tk.Frame(self)
    self.frame2.pack()

    # チェックボタン
    cb = Checkbutton(self.frame1, text = '回数を指定する', variable = flag, command = change_state)
    # ラベルフレーム
    f = LabelFrame(self.frame1, labelwidget = cb)
    
    #実行ボタン
    btn_start = tk.Button(self.frame1,
                          text="実行",
                          font=16,
                          width=20,
                          height=5,
                          borderwidth=4,
                          command = data.action)
    btn_start.grid(row=0, column=0, columnspan=1, sticky=tk.W + tk.E + tk.N + tk.S)

    #回数指定枠
    # ラジオボタン
    for x in (5, 10):
        b = Radiobutton(f, text = '%d　回' % x,value = x, variable = v, state = 'disabled')
        b.pack()
        buttons.append(b)
    b = Radiobutton(f, text = '∞回',value = 10000, variable = v, state = 'disabled')
    b.pack()
    buttons.append(b)
    f.grid(row=0,column=1, columnspan=1, sticky=tk.W + tk.E + tk.N + tk.S)
    #zeroing
    btn_zeroing = tk.Button(self.frame1,
                            text="０点合わせモード",
                            font=16,width=20,
                            height=5,
                            borderwidth=4,
                            command=ZEROING)
    btn_zeroing.grid(row=0, column=2, columnspan=1, sticky=tk.W + tk.E + tk.N + tk.S)
    #送り実行ボタン
    btn_frame = tk.Button(self.frame1,
                           text="送り実行",
                           font=16,
                           width=20,
                           height=5,
                           borderwidth=4)
    btn_frame.grid(row=1, column=0, columnspan=1, sticky=tk.W + tk.E + tk.N + tk.S)
    #CSVボタン
    btn_csv = tk.Button(self.frame1,
                        text="CSV",
                        font=16,
                        width=20,
                        height=5,
                        borderwidth=4,
                        command = data.appendcsv)
    btn_csv.grid(row=1, column=1, columnspan=1, sticky=tk.W + tk.E + tk.N + tk.S)
    #終了ボタン
    btn_exit = tk.Button(self.frame1,
                         text="終了",
                         font=16,
                         width=20,
                         height=5,
                         borderwidth=4,
                         command=end)
    btn_exit.grid(row=1, column=2, columnspan=1, sticky=tk.W + tk.E + tk.N + tk.S)
    self.rowconfigure((0,1), weight=1)
    self.columnconfigure((0,2), weight=1)
    
    #インスペクタ
    label1 = tk.Label(self.frame2,text="現在実行中のファイル:",font=16)
    label1.pack(side="left")
    label2 = tk.Label(self.frame2,text="ほにゃらら",font=16)
    label2.pack(side="left")
    
class DATA:
    def __init__(self):
        self.mapdata = 0
        self.stopper = True

    def stop(self):
        self.stopper = False

    def appendcsv(self):
        global filename
        #小さいウィンドウを非表示にする
        tk = tkinter.Tk()
        tk.withdraw()
        #表示させる拡張子を制限
        fTyp = [("","*.csv")]
        #ファイルダイアログウィンドウ表示→filenameにフルパスを代入
        filename = tkfd.askopenfilename(filetypes = fTyp)
        label2.config(text=filename)
        #CSVファイルからインポートした文字列データから数値データに変換し格納
        with open(filename)as fp:
                data = (list(csv.reader(fp)))
                
        #行数取得
        self.line = sum(1 for line in open(filename))
        #print ("行数は",self.line,"です。")

        mapdata = [[0 for i in range(3)] for j in range(self.line)]     #CSVの行数に合わせて２次元配列を生成

        print("CSV生データ================")
        for j in range(self.line):
                XX = data[j]                            # 行を代入
                if XX[2] == "":
                    pass
                else:
                    XX = list(map(float,XX))                # 型をstrからfloatに変換
                #print(XX[0])
                #print(XX[1])
                #print(XX[2])
                for i in range(3):
                        #print("j=",j,",i=",i)
                        mapdata[j][i] = XX[i]
                print(j,"|",mapdata[j])
        self.mapdata = mapdata
        return filename

    def action(self):
        #setup()
        #softstop()
        if self.mapdata == 0:
            print("■CSVデータが選択されていません。")
        else:
            print("位置データ===================")
            for i in range(self.line):
                print(i,"|",self.mapdata[i][0],self.mapdata[i][1],self.mapdata[i][2])
            posdata = [[0 for j in range(3)] for i in range(self.line)]
            movedata = [[0 for j in range(3)] for i in range(self.line)]
            mechadata = [[0 for j in range(3)] for i in range(self.line)]
            #====================
            #配列コピー
            for i in range(self.line):
                for j in range(3):
                    posdata[i][j] = self.mapdata[i][j]
            #====================
            #運動データーを補正
            print("運動補正データ===================")
            for i in range(self.line):
                #第１層目
                x = []
                x = posdata[i][::1]
                #print(x[0],x[1],x[2],x[3],x[4],x[5])
                cont = 0
                sum = 0
                if x[0] == "stop":
                    pass
                else:
                    for j in range(3):
                        if x[j] != 0:
                            sum = sum + x[j]
                        else:
                            cont += 1
                    if cont < 3:
                        for j in range(3):
                            if x[j] == 0:
                                posdata[i][j] = int((sum / 3) * -1)
                print(i,"|",posdata[i][0],posdata[i][1],posdata[i][2])
            #====================
            #位置データからモーターの運動データへ変換
            print("運動データ===================")
            offset = False
            for i in range(self.line):
                for j in range(3):
                    if i == 0:
                        #print(movedata[i][j],"=",self.mapdata[i][j])
                        movedata[i][j] = posdata[i][j]
                        #print(movedata[i][j],i,j)
                    elif posdata[i][0] == "stop":
                        #print(j,"stop検知")
                        movedata[i][0] = posdata[i][0]
                        movedata[i][1] = posdata[i][1]
                        offset = True
                        break
                    else:
                        if offset == False:
                            #print(movedata[i][j],i,j,"=",self.mapdata[i][j],"-",self.mapdata[i-1][j])
                            movedata[i][j] = posdata[i][j] - posdata[i-1][j]
                        elif offset == True:
                            movedata[i][j] = posdata[i][j] - posdata[i-2][j]
                            if j == 2:
                                offset = False   
                print(i,movedata[i][0],movedata[i][1],movedata[i][2])
            #====================
            #運動データー[mm]をモーターのデータへ
            print("メカデータ===================")
            for i in range(self.line):
                for j in range(3):
                    if movedata[i][0] == "stop":
                        mechadata[i][0] = movedata[i][0]
                        mechadata[i][1] = movedata[i][1]
                        break
                    else:
                        mechadata[i][j] = 25600 * movedata[i][j] / (20 * 3.14)
                        mechadata[i][j] = int(mechadata[i][j])
                print(i,"|",mechadata[i][0],mechadata[i][1],mechadata[i][2])
            
            
            #実行詳細のprint
            print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")
            print(filename)
            if flag.get() == False:
                loop = 1
                print("■",loop,"回繰り返します。")
            else:
                loop = v.get()
                print("■",loop,"回繰り返します。")
            for i in range(self.line):
                print(i,"|",movedata[i][0],movedata[i][1],movedata[i][2])
            print("■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■")

            ans=tkmsg.askokcancel('askokcancel','moveを実行しますか？')
            if ans == False:
                print("実行がキャンセルされました。")
                return  
            data.action2(mechadata,loop)        
    
    def action2(self,mechadata,loop):
        print("MOVING START================")
        i = 0
        #self.movedata = movedata
        for l in range(loop):
            for i in range(self.line):
                self.stopper = getkey()
                if (self.stopper == 0):
                    if mechadata[i][0] == "stop":
                        print(mechadata[i][1],"秒間stop")
                        timeval = int(mechadata[i][1])
                        time.sleep(timeval)
                    else:
                        move(mechadata[i])
                        print(l+1,"roop",mechadata[i])
                elif(self.stopper >= 1):
                    print("■■緊急停止■■")
                    return



def write(data1,data2,data3):
    GPIO.output(13,GPIO.LOW)
    time.sleep(0.005)
    spi.xfer2([data1])
    spi.xfer2([data2])
    spi.xfer2([data3])
    GPIO.output(13,GPIO.HIGH)
    #print(hex(data))
    time.sleep(0.005)
    
def setup():
    #ドライバ初期化
    write(0x00,0x00,0x00)
    write(0x00,0x00,0x00)
    write(0x00,0x00,0x00)
    write(0x00,0x00,0x00)
    write(0xc0,0xc0,0xc0)
    #ドライバ初期設定
    #ACC加速係数
    write(0x05,0x05,0x05)
    write(0x00,0x00,0x00)
    write(0x04,0x04,0x04)
    #MAX_SPEED設定
    write(0x07,0x07,0x07)
    write(0x01,0x01,0x01)
    #Kval_RUN
    write(0x0A,0x0A,0x0A)
    write(0xFF,0xFF,0xFF)
    #Kval_HOLD
    write(0x09,0x09,0x09)
    write(0xF0,0xF0,0xF0)
    #Kval_ACC
    write(0x0B,0x0B,0x0B)
    write(0xFF,0xFF,0xFF)
    #Kval_DEC
    write(0x0C,0x0C,0x0C)
    write(0xFF,0xFF,0xFF)
    #ResetPos(０点位置決め)
    write(0xD8,0xD8,0xD8)
     
def gohome():
    write(0x70,0x70,0x70)
    while (GPIO.input(5) == 0) or (GPIO.input(6) == 0) or (GPIO.input(4) == 0):
        pass
    print("***OK GoHome***")
    
def softstop():
    write(0xB8,0xB8,0xB8)
    while (GPIO.input(5) == 0) or (GPIO.input(6) == 0) or (GPIO.input(4) == 0):
        pass
    print("***OK STOP***")
    
def move(step):
    #movelist初期化
    movelist = [[0 for i in range(3)]for j in range(4)]
    
    
    for i in range(3):
        #方向検出
        n_step = step[i]

        if (n_step < 0):
            dir = 0x40
            stp = -1 * n_step
        else:
            dir = 0x41
            stp = n_step
    
        #モーター3,5,6は反転させる必要がある
        #if (i == 3) or (i == 5) or (i == 6):
        #    if (dir == 0x40):
        #        dir = 0x41
        #    elif (dir == 0x41):
        #        dir = 0x40
	
	# 送信バイトデータ生成。
        stp_h   = (0x3F0000 & stp) >> 16 
        stp_m   = (0x00FF00 & stp) >> 8 
        stp_l   = (0x0000FF & stp)
        
        #配列に格納
        movelist[0][i] = dir
        movelist[1][i] = stp_h
        movelist[2][i] = stp_m
        movelist[3][i] = stp_l
    
    #データ送信
    for j in range(4):
        write(movelist[j][0],movelist[j][1],movelist[j][2])
    
    #フラグピン監視
    while (GPIO.input(5) == 0) or (GPIO.input(6) == 0) or (GPIO.input(4) == 0):
        pass
    print("***OK MOVE***")
    
def ZEROING():
    while 1:
        key = getkey()
        if key == 1792835: #→
            step = [3200,3200,3200]
            move(step)
        elif key == 1792836: #←
            step = [-3200,-3200,-3200]
            move(step)
        elif key == 114: #R
            step = [0,0,3200]
            move(step)
        elif key == 102: #F
            step = [0,0,-3200]
            move(step)
        elif key == 82: #Shift + R
            step = [0,0,1600]
            move(step)
        elif key == 70: #Shift + F
            step = [0,0,-1600]
            move(step)
        elif key == 116: #T
            step = [0,3200,0]
            move(step)
        elif key == 103: #G
            step = [0,-3200,0]
            move(step)
        elif key == 84: #Shift + T
            step = [0,1600,0]
            move(step)
        elif key == 71: #Shift + G
            step = [0,-1600,0]
            move(step)
        elif key == 121: #Y
            step = [3200,0,0]
            move(step)
        elif key == 104: #H
            step = [-3200,0,0]
            move(step)
        elif key == 89: #Shift + Y
            step = [1600,0,0]
            move(step)
        elif key == 72: #Shift + H
            step = [-1600,0,0]
            move(step)
        elif key == 32: #SPACE
            gohome()
        elif key == 48: #0
            write(0xD8,0xD8,0xD8)
            print("***OK Zeroing***")
        elif key == 10: #Enter
            return


if __name__=="__main__":
    print("program start")
    signal.signal(signal.SIGINT, handler)
    setup()
    softstop()
    data = DATA()
    #画面表示
    root = Tk()
    win_build(root)
    root.mainloop()    
    GPIO.cleanup()