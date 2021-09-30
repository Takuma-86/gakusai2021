import pigpio
import time
import posix_ipc
import json

A_PHASE = 27
A_ENABLE = 22
B_PHASE = 5
B_ENABLE = 25
SERVO = 19

pi = pigpio.pi()

pi.set_mode(A_PHASE, pigpio.OUTPUT)
pi.set_mode(A_ENABLE, pigpio.OUTPUT)
pi.set_mode(B_PHASE, pigpio.OUTPUT)
pi.set_mode(B_ENABLE, pigpio.OUTPUT)

pi.set_PWM_range(A_ENABLE, 100)
pi.set_PWM_range(B_ENABLE, 100)

pi.set_mode(SERVO,pigpio.OUTPUT)
pi.set_PWM_frequency(SERVO,50)

pi.set_PWM_range(SERVO,2000) #-90°:50 0°:145 90°:240 5°刻み(19刻み)で動く

pulse = 145 #初期設定（砲塔0°、モーター停止）
pi.set_PWM_dutycycle(SERVO,145)

right = 1 #仮置き、エラーでるの気持ち悪いから
left = 1
radius = 1
angle = 0
shot = 0

def main():
    mq = posix_ipc.MessageQueue("/gakusai2021.1")
    try:
        while 1:
            mqs = mq.receive()
            movementJsonCode = json.loads(mqs[0].decode())
            # 以下の入出力を参考すること
            print(movementJsonCode["joystick"]["r"])
            print(movementJsonCode["joystick"]["sita"])
            print(movementJsonCode["shoot"])
            print(movementJsonCode["LR"])
            #以下、入力に対して機体を動かすプログラム
            #変数left,right,shot,radius,angle
            if shot == 1:
                shot()

            if right + left == 1:
                if right == 1:
                    right_rotation()
                if left == 1:
                    left_rotation()


            if radius < 5 : #停止(仮置き)ジョイスティックのあそびを考慮
                stop()
            else:
                move() #動く

    except KeyboardInterrupt:
        pi.stop()
        exit()

def shot(): #レーザーガン班
    return

def right_rotation(): #砲塔の右旋回
    global pulse
    if pulse < 240:
        pulse += 19
        pi.set_PWM_dutycycle(SERVO,pulse)
        time.sleep(0.1)
        return

def left_rotation(): #砲塔の左旋回
    global pulse
    if pulse > 50:
        pulse -= 19
        pi.set_PWM_dutycycle(SERVO,pulse)
        time.sleep(0.1)
        return

#dcモーター１が右前輪、dcモーター２が左前輪
def stop():
        pi.write(A_ENABLE, 0)
        pi.write(B_ENABLE, 0)
        return

def move(radius, angle):
    if 0 <= angle < 15: #直進
        rightPwm = 100
        leftPwm = 100
    elif 15<= angle < 75: #右前方
        rightPwm = 100 - (angle - 15)
        leftPwm = 100
    elif 75 <= angle < 105: #右旋回
        rightPwm = 50
        leftPwm = 50
    elif 105 <= angle < 165: #右後方
        rightPwm = 100 - (165 - angle)
        leftPwm = 100
    elif 165 <= angle < 195: #後退
        rightPwm = 100
        leftPwm = 100
    elif 195 <= angle < 255: #左後方
        rightPwm = 100
        leftPwm = 100 - (angle - 195)
    elif 255 <= angle < 285: #左旋回
        rightPwm = 50
        leftPwm = 50
    elif 285 <= angle < 345: #左前方
        rightPwm = 100
        leftPwm = 100 - (345 - angle)
    elif 345 <= angle < 360: #直進
        rightPwm = 100
        leftPwm = 100

    if radius < 50 : #低速
        rightPwm *= 0.5
        leftPwm *= 0.5

    pi.set_PWM_dutycycle(A_ENABLE, rightPwm)
    pi.set_PWM_dutycycle(B_ENABLE, leftPwm)

    if 0 <= angle < 75 or 285 <= angle < 360: #前方
        pi.write(A_PHASE, 0)
        pi.write(B_PHASE, 1)
    elif 105 <= angle < 255: #後方
        pi.write(A_PHASE, 1)
        pi.write(B_PHASE, 0)
    elif 75 <= angle < 105: #右旋回
        pi.write(A_PHASE, 1)
        pi.write(B_PHASE, 1)
    elif 255 <= angle < 285: #左旋回
        pi.write(A_PHASE, 0)
        pi.write(B_PHASE, 0)
    time.sleep(0.1)

    return

def test(): #動作確認用
    for i in range(360):
        move(100,i)
    for i in range(10):
        right_rotation()
    for i in range(10):
        left_rotation()
    pi.set_PWM_dutycycle(SERVO,145) #0°に戻す
    time.sleep(1)
    stop()
    pi.stop()

main()
