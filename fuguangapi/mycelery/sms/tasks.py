from ..main import app
from ronglianyunapi import send_sms as send_sms_to_user


@app.task(name="send_sms")
def send_sms(tid, mobile, datas):
    """发送短信"""
    return send_sms_to_user(tid, mobile, datas)


"""
# 简单测试celery的代码
@app.task
def send_sms1():
    print('send_sms1 执行了')

@app.task(name="send_sms2")
def send_sms2(mobile, code):
    print(f'send_sms2 执行了-- mobile={mobile}, code={code}')

@app.task
def send_sms3():
    print('send_sms3执行了')
    return 100
    
@app.task(name="send_sms4")
def send_sms4(x, y):
    print('send_sms4执行了')
    return x + y
"""
