# @Date:   2021-11-03T16:06:31+09:00
# @Last modified time: 2021-11-03T21:08:45+09:00



import pigpio
import time
import posix_ipc
import json

A_PHASE = 22
A_ENABLE = 10
B_PHASE = 9
B_ENABLE = 11

IRreceiver1 = 4
IRreceiver2 = 17
IRreceiver3 = 14
IRreceiver4 = 15

RaserGun = 21

SERVO = 19

pi = pigpio.pi()

pi.set_mode(A_PHASE, pigpio.OUTPUT)
pi.set_mode(A_ENABLE, pigpio.OUTPUT)
pi.set_mode(B_PHASE, pigpio.OUTPUT)
pi.set_mode(B_ENABLE, pigpio.OUTPUT)

pi.set_PWM_range(A_ENABLE, 100)
pi.set_PWM_range(B_ENABLE, 100)

pi.setmode(IRreceiver1, pigpio.INPUT)
pi.setmode(IRreceiver2, pigpio.INPUT)
pi.setmode(IRreceiver3, pigpio.INPUT)
pi.setmode(IRreceiver4, pigpio.INPUT)

pi.setmode(RaserGun, pigpio.OUTPUT)

pi.set_mode(SERVO,pigpio.OUTPUT)
pi.set_PWM_frequency(SERVO,50)

pi.set_PWM_range(SERVO,2000)

gun_degree = 0 #砲塔の角度 -90~90 5°刻み
n = 0 #砲塔の動き -18~18 pulse=145+n*95/18
pulse = 145 #初期設定（砲塔0°）
pi.set_PWM_dutycycle(SERVO,145)

right = 1 #仮置き、エラーでるの気持ち悪いから
left = 1
radius = 1
stick_degree = 0
shot = 0

def main():
    mq = posix_ipc.MessageQueue("/gakusai2021.1")
    try:
        remaining_machines = 5 #残機
        remaining_bullets = 5 #残弾数　
        #【画面表示】戦車(被弾前)を5個並べて表示
        #【画面表示】銃弾(発射前)を5個並べて表示
        while 1:
            mqs = mq.receive()
            movementJsonCode = json.loads(mqs[0].decode())
            # 以下の入出力を参考すること
            print(movementJsonCode["joystick"]["r"])
            print(movementJsonCode["joystick"]["sita"])
            print(movementJsonCode["shoot"])
            print(movementJsonCode["LR"])
            #以下、入力に対して機体を動かすプログラム
            #変数left,right,shot_button,reload_button,radius,stick_degree
            if shot_button == 1:
                shot()
                remaining_bullets -=1　
                #【画面表示】一番右の銃弾(発射前)を銃弾(発射後)に切り替え　
                time.sleep(1)

            hit_check =hit()
            if hit_check ==1:
                remaining_machines -=1
                #【画面表示】一番右の戦車(被弾前)を戦車(被弾後)に切り替え
                if remaining_machines==0:
                    #【画面表示】負けた方にlose、勝った方にwinを５秒表示
                    pi.stop()
                    time.sleep(5)
                    break

            if reload_button ==1:
                if remaining_bullets!=0:
                    time.sleep(2)
                    #【画面表示】リロードを0.5秒周期で２秒点滅
                else:
                    time.sleep(1)
                    #【画面表示】リロードを0.5秒周期で１秒点滅
                remaining_bullets =5
                #【画面表示】銃弾(発射前)を5個並べて表示

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


def shot():
    pass
    return

def hit():#ヒットで1を返す、ミスで0を返す
    pass
    return


def right_rotation(): #砲塔の右旋回
    global n
    global gun_degree
    if n < 18:
        n += 1
        pulse = round(145 + n*95/18)
        gun_degree = n*5
        pi.set_PWM_dutycycle(SERVO,pulse)
        time.sleep(0.1)
        return

def left_rotation(): #砲塔の左旋回
    global n
    global gun_degree
    if n > -18:
        n -= 1
        pulse = round(145 + n*95/18)
        gun_degree = n*5
        pi.set_PWM_dutycycle(SERVO,pulse)
        time.sleep(0.1)
        return

#dcモーター１が右前輪、dcモーター２が左前輪
def stop():
        pi.write(A_ENABLE, 0)
        pi.write(B_ENABLE, 0)
        return

def move(radius, stick_degree):
    if 0 <= stick_degree < 15: #直進
        rightPwm = 100
        leftPwm = 100
    elif 15<= stick_degree < 75: #右前方
        rightPwm = 100 - (stick_degree - 15)
        leftPwm = 100
    elif 75 <= stick_degree < 105: #右旋回
        rightPwm = 50
        leftPwm = 50
    elif 105 <= stick_degree < 165: #右後方
        rightPwm = 100 - (165 - stick_degree)
        leftPwm = 100
    elif 165 <= stick_degree < 195: #後退
        rightPwm = 100
        leftPwm = 100
    elif 195 <= stick_degree < 255: #左後方
        rightPwm = 100
        leftPwm = 100 - (stick_degree - 195)
    elif 255 <= stick_degree < 285: #左旋回
        rightPwm = 50
        leftPwm = 50
    elif 285 <= stick_degree < 345: #左前方
        rightPwm = 100
        leftPwm = 100 - (345 - stick_degree)
    elif 345 <= stick_degree < 360: #直進
        rightPwm = 100
        leftPwm = 100

    if radius < 50 : #低速
        rightPwm *= 0.5
        leftPwm *= 0.5

    pi.set_PWM_dutycycle(A_ENABLE, rightPwm)
    pi.set_PWM_dutycycle(B_ENABLE, leftPwm)

    if 0 <= stick_degree < 75 or 285 <= stick_degree < 360: #前方
        pi.write(A_PHASE, 0)
        pi.write(B_PHASE, 1)
    elif 105 <= stick_degree < 255: #後方
        pi.write(A_PHASE, 1)
        pi.write(B_PHASE, 0)
    elif 75 <= stick_degree < 105: #右旋回
        pi.write(A_PHASE, 1)
        pi.write(B_PHASE, 1)
    elif 255 <= stick_degree < 285: #左旋回
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

#メイン関数
while True:
    start=input() #enter押したら始動
    if start=='':
        main()
