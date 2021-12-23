from ronglianyunapi import send_sms as send_sms_to_user
from ..main import app


@app.task(name="send_sms")
def send_sms(tid, mobile, datas):
    """发送短信"""
    return send_sms_to_user(tid, mobile, datas)
