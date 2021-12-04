from datetime import datetime

from alipay import AliPay
from alipay.utils import AliPayConfig
from django.conf import settings


class AliPaySDK(AliPay):
    """支付宝支付SDK"""

    def __init__(self, config=None):
        if config is None:
            self.config = settings.ALIPAY
        else:
            self.config = config

        # 读取公钥私钥文件
        app_private_key_string = open(settings.ALIPAY["app_private_key_path"]).read()
        alipay_public_key_string = open(settings.ALIPAY["alipay_public_key_path"]).read()
        super().__init__(
            appid=self.config["appid"],
            app_notify_url=self.config["notify_url"],  # 默认全局回调 url
            app_private_key_string=app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=alipay_public_key_string,
            sign_type=self.config["sign_type"],  # RSA 或者 RSA2
            debug=self.config["debug"],  # 默认 False，沙箱模式下必须设置为True
            verbose=self.config["verbose"],  # 输出调试数据
            config=AliPayConfig(timeout=self.config["timeout"])  # 可选，请求超时时间，单位：秒
        )

    def page_pay(self, order_number, real_price, order_name):
        """生成支付链接"""
        order_string = self.client_api(
            "alipay.trade.page.pay",
            biz_content={
                "out_trade_no": order_number,  # 订单号
                "total_amount": float(real_price),  # 订单金额 单位：元
                "subject": order_name,  # 订单标题
                "product_code": "FAST_INSTANT_TRADE_PAY",  # 产品码，目前只能支持 FAST_INSTANT_TRADE_PAY
            },
            return_url=self.config["return_url"],  # 同步回调地址
            notify_url=self.config["notify_url"]
        )

        return f"{self.config['gateway']}?{order_string}"

    def check_sign(self, data):
        """验证签名"""
        signature = data.pop("sign")
        success = self.verify(data, signature)
        return success

    def query(self, order_number):
        """
        根据订单号查询订单状态
        @params order_number: 订单号
        """
        return self.server_api(
            "alipay.trade.query",
            biz_content={
                "out_trade_no": order_number
            }
        )

    def refund(self, order_number, real_price):
        """
        原路退款
        @params order_number: 退款的订单号
        @params real_price: 退款的订单金额
        """
        self.server_api(
            "alipay.rade.refund",
            biz_content={
                "out_trade_no": order_number,
                "refund_amount": real_price
            }
        )

    def transfer(self, account, amount):
        """
        转账给个人
        @params account: 收款人的支付宝账号
        @params amount: 转账金额
        """
        return self.server_api(
            "alipay.fund.trans.toaccount.transfer",
            biz_content={
                "out_biz_no": datetime.now().strftime("%Y%m%d%H%M%S"),
                "payee_type": "ALIPAY_LOGONID/ALIPAY_USERID",
                "payee_account": account,
                "amount": amount
            }
        )
