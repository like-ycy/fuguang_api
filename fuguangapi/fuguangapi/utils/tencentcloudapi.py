import json
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.captcha.v20190722 import captcha_client, models
from django.conf import settings


class TencentCloudAPI(object):
    """腾讯云API工具类"""

    def __init__(self):
        self.cred = credential.Credential(settings.TENCENTCLOUD["SecretId"],
                                          settings.TENCENTCLOUD["SecretKey"])

    def captcha(self, ticket, randstr, user_ip):
        """
        验证码校验工具方法
        :ticket  客户端验证码操作成功以后得到的临时验证票据
        :randstr 客户端验证码操作成功以后得到的随机字符串
        :user_ip 客户端的IP地址
        """
        try:
            Captcha = settings.TENCENTCLOUD["Captcha"]
            # 实例化http请求工具类
            httpProfile = HttpProfile()
            # 设置API所在服务器域名
            httpProfile.endpoint = Captcha["endpoint"]
            # 实例化客户端工具类
            clientProfile = ClientProfile()
            # 给客户端绑定请求的服务端域名
            clientProfile.httpProfile = httpProfile
            # 实例化验证码服务端请求工具的客户端对象
            client = captcha_client.CaptchaClient(self.cred, "", clientProfile)
            # 客户端请求对象参数的初始化
            req = models.DescribeCaptchaResultRequest()

            params = {
                # 验证码类型固定为9
                "CaptchaType": Captcha["CaptchaType"],
                # 客户端提交的临时票据
                "Ticket": ticket,
                # 客户端ip地址
                "UserIp": user_ip,
                # 随机字符串
                "Randstr": randstr,
                # 验证码应用ID
                "CaptchaAppId": Captcha["CaptchaAppId"],
                # 验证码应用key
                "AppSecretKey": Captcha["AppSecretKey"],
            }
            # 发送请求
            req.from_json_string(json.dumps(params))
            # 获取腾讯云的响应结果
            resp = client.DescribeCaptchaResult(req)
            # 把响应结果转换成json格式数据
            result = json.loads(resp.to_json_string())
            return result and result.get("CaptchaCode") == 1

        except Exception as err:
            raise TencentCloudSDKException
