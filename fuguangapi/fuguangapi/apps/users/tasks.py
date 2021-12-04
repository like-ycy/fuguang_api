from celery import shared_task
from ronglianyunapi import send_sms as sms
import logging

# 记录日志
logger = logging.getLogger("django")


@shared_task(name="send_sms")
def send_sms(tid, mobile, datas):
    """异步发送短信"""
    try:
        return sms(tid, mobile, datas)
    except Exception as e:
        logger.error(f"发送短信失败 - {e}")
