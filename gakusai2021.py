# @Date:   2021-11-03T16:06:31+09:00
# @Last modified time: 2021-11-04T22:59:23+09:00



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
pi.set_pull_up_down(IRreceiver1,pigpio.PUD_UP)
pi.setmode(IRreceiver2, pigpio.INPUT)
pi.set_pull_up_down(IRreceiver2,pigpio.PUD_UP)
pi.setmode(IRreceiver3, pigpio.INPUT)
pi.set_pull_up_down(IRreceiver3,pigpio.PUD_UP)
pi.setmode(IRreceiver4, pigpio.INPUT)
pi.set_pull_up_down(IRreceiver4,pigpio.PUD_UP)

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
            radius = movementJsonCode["joystick"]["radius"]
            stick_degree = movementJsonCode["joystick"]["stick_degree"]
            shot_button = movementJsonCode["shot_button"]
            reload_button = movementJsonCode["reload_button"]
            left = movementJsonCode["left"]
            right = movementJsonCode["right"]


            #以下、入力に対して機体を動かすプログラム
            #変数left,right,shot_button,reload_button,radius,stick_degree
            if shot_button == 1:
                #【画面表示】一番右の銃弾(発射前)を銃弾(発射後)に切り替え
                remaining_bullets -=1
                shot()



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
                    #【画面表示】リロードを0.5秒周期で２秒点滅
                    time.sleep(2)#画面表示するなら消す
                else:
                    #【画面表示】リロードを0.5秒周期で１秒点滅
                    time.sleep(1)#画面表示するなら消す
                remaining_bullets =5
                #【画面表示】銃弾(発射前)を5個並べて表示

            if right + left == 1:
                if right == 1:
                    right_rotation()
                if left == 1:
                    left_rotation()


            if radius < 1 : #停止
                stop()
            else:
                move(radius, stick_degree) #動く


    except KeyboardInterrupt:
        pi.stop()


def shot():
    pi.write(RaserGun,1) #発射(点灯)
    time.sleep(0.2)
    pi.write(RaserGun,0) #消灯
    time.sleep(0.8) #発射後硬直
    return

def hit():#ヒットで1を返す、ミスで0を返す
    pin=[IRreceiver1,IRreceiver2,IRreceiver3,IRreceiver4]
    check=[pi.read(IRreceiver1),pi.read(IRreceiver2),pi.read(IRreceiver3),pi.read(IRreceiver4)]

    if 0 in check:
        shot_down_list=[]
        one_shot_start = time.time()
        shot_down = [[],[],[],[]]
        #4つのセンサそれぞれのパルスのスタート時間
        start_time_list = [time.time()]*4
        #パルスの立ち下がりの時のみ反応するようにするためのフラグ
        down_pulse = [False]*4
        while time.time()-one_shot_start <= 0.1:
            if not pi.read(IRreceiver1) and not down_pulse[0]:
                down_pulse[0] = True
                shot_down[0].append(time.time()-start_time_list[0])
                start_time_list[0] = time.time()
            if not pi.read(IRreceiver2) and not down_pulse[1]:
                down_pulse[1] = True
                shot_down[1].append(time.time()-start_time_list[1])
                start_time_list[1] = time.time()
            if not pi.read(IRreceiver3) and not down_pulse[2]:
                down_pulse[2] = True
                shot_down[2].append(time.time()-start_time_list[2])
                start_time_list[2] = time.time()
            if not pi.read(IRreceiver4) and not down_pulse[3]:
                down_pulse[2] = True
                shot_down[3].append(time.time()-start_time_list[3])
                start_time_list[3] = time.time()

            if pi.read(IRreceiver1):
                down_pulse[0] = False
            if pi.read(IRreceiver2):
                down_pulse[1] = False
            if pi.read(IRreceiver2):
                down_pulse[2] = False
            if pi.read(IRreceiver3):
                down_pulse[3] = False

        for i in range(4):
            #最初の信号と最後の信号を除いて、平均をとる
            if len(shot_down[i]) >= 3:
                shot_down[i] = shot_down[i][1:-1]
            shot_down_list.append([sum(shot_down[i])/len(shot_down[i]),i])

        #shot_down_list：[平均のパルス幅,何番目のセンサか]のリスト

        shot_down_list.sort() #平均立ち下がり秒数が最も短いものを先頭に
        pulse = shot_down_list[0][0]


        if pulse <= 0.001:#閾値は後で決める
            #レーザー受け取ったよ
            return 1
        else:
            #レーザー遠いよ
            return 0
    return 0


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
    if 0 <= stick_degree < 3: #直進
        rightPwm = 100
        leftPwm = 100
    elif 3 <= stick_degree < 87: #右前方
        rightPwm = 100 - (stick_degree - 3)
        leftPwm = 100
    elif 87 <= stick_degree < 93: #右旋回
        rightPwm = 50
        leftPwm = 50
    elif 93 <= stick_degree < 177: #右後方
        rightPwm = 100 - (177 - stick_degree)
        leftPwm = 100
    elif 177 <= stick_degree < 183: #後退
        rightPwm = 100
        leftPwm = 100
    elif 183 <= stick_degree < 267: #左後方
        rightPwm = 100
        leftPwm = 100 - (stick_degree - 183)
    elif 267 <= stick_degree < 273: #左旋回
        rightPwm = 50
        leftPwm = 50
    elif 273 <= stick_degree < 357: #左前方
        rightPwm = 100
        leftPwm = 100 - (357 - stick_degree)
    elif 357 <= stick_degree <= 360: #直進
        rightPwm = 100
        leftPwm = 100

    if radius <= 70 : #低速
        rightPwm *= 0.5
        leftPwm *= 0.5

    pi.set_PWM_dutycycle(A_ENABLE, rightPwm)
    pi.set_PWM_dutycycle(B_ENABLE, leftPwm)

    if 0 <= stick_degree < 87 or 273 <= stick_degree <= 360: #前方
        pi.write(A_PHASE, 0)
        pi.write(B_PHASE, 1)
    elif 93 <= stick_degree < 267: #後方
        pi.write(A_PHASE, 1)
        pi.write(B_PHASE, 0)
    elif 87 <= stick_degree < 93: #右旋回
        pi.write(A_PHASE, 1)
        pi.write(B_PHASE, 1)
    elif 267 <= stick_degree < 273: #左旋回
        pi.write(A_PHASE, 0)
        pi.write(B_PHASE, 0)
    time.sleep(0.1)
    stop()

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
