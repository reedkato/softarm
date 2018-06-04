import time
import RPi.GPIO as GPIO
import numpy as np

rb, r6, r5, r4, r3, r2, r1 = (20,19,16,13,12,6,5)
lb, l6, l5, l4, l3, l2, l1 = (20,19,16,13,12,6,5)
senR = np.array([rb, r6, r5, r4, r3, r2, r1]) 
senL = np.array([lb, l6, l5, l4, l3, l2, l1]) 
z_zero, z_max = (21, 26)

GPIO.setmode(GPIO.BCM)
GPIO.setup(r1, GPIO.IN)
GPIO.setup(r2, GPIO.IN)
GPIO.setup(r3, GPIO.IN)
GPIO.setup(r4, GPIO.IN)
GPIO.setup(r5, GPIO.IN)
GPIO.setup(r6, GPIO.IN)
GPIO.setup(z_zero, GPIO.IN)
GPIO.setup(z_max, GPIO.IN)

def readsens(pin):
    return GPIO.input(pin)

if __name__ == "__main__":
    try:
        while 1:
            print(readsens(z_zero))
    finally:
        GPIO.cleanup()
        print("***OK cleanup***")
