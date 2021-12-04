import json
from ronglian_sms_sdk import SmsSDK
from django.conf import settings


def send_sms(tid, mobile, datas):
    """
    发送短信
    :param tid: 短信模板id
    :param mobile: 手机号, 多个手机号用逗号隔开
    :param datas: 模板参数
    :return:
    """
    ronglianyun = settings.RONGLIANYUN  # 拿到容联云短信配置
    # 初始化SDK
    sdk = SmsSDK(ronglianyun['accId'], ronglianyun['accToken'], ronglianyun['appId'])
    # 调用发送短信接口
    result = sdk.sendMessage(tid, mobile, datas)
    # 返回结果转换为字典
    response = json.loads(result)
    #
    # print(response, type(response))
    # statusCode值为 000000 的时候表示发送成功
    return response.get("statusCode") == "000000"
