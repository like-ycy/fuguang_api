from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

# 编写测试的接口地址
TOKEN_URL = "/users/login/"
MOBILE_URL = "/users/mobile/"
REGISTER_URL = "/users/register/"
SMS_URL = "/users/sms/"


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class MobileTestCase(TestCase):
    """
    手机号验证是否合规的测试集
    """

    def setUp(self):
        self.client = APIClient()

    def test_mobile_is_unregister(self):
        """测试手机号未注册"""
        mobile = 15210197546
        response = self.client.get(f"{MOBILE_URL}{mobile}/")
        self.assertIn("errmsg", response.data)
        self.assertEqual("ok", response.data["errmsg"])
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_mobile_is_registerd(self):
        """测试手机号已经注册"""
        # 先注册拥有当前手机号码的用户信息
        data = {"username": "xiaoming", "password": "123456", "mobile": "13334500000"}
        create_user(**data)
        # 基于已经注册的手机号码进行单元测试
        mobile = "13334500000"
        response = self.client.get(f"{MOBILE_URL}{mobile}/")
        self.assertIn("errmsg", response.data)
        self.assertEqual("手机号码已注册", response.data["errmsg"])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mobile_is_invalid(self):
        """测试手机号不合规"""
        mobile = 123456789
        response = self.client.get(f"{MOBILE_URL}{mobile}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class UserTestCase(TestCase):
    """用户登录的测试集"""

    def setUp(self):
        self.client = APIClient()

    def test_user_login_by_username(self):
        """测试用户用户名登录,是否创建了令牌"""
        data = {"username": "xiaoming", "password": "123.com"}
        create_user(**data)
        res = self.client.post(TOKEN_URL, data)
        self.assertIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_user_login_by_mobile(self):
        """测试用户手机号登录,是否创建了令牌"""
        data = {"username": "15210198547", "password": "123.com", "mobile": "15210198547"}
        create_user(**data)
        data = {"username": "15210198547", "password": "123.com"}
        res = self.client.post(TOKEN_URL, data)
        self.assertIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_token_invalid_whether_credentials(self):
        """测试令牌是否失效"""
        create_user(username="xiaoming", password="123.com")
        data = {"username": "xiaoming", "password": "123456"}
        res = self.client.post(TOKEN_URL, data)
        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """测试用户不存在是否创建令牌"""
        data = {"username": "xiaoming", "password": "123456"}
        res = self.client.post(TOKEN_URL, data)
        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        """测试用户缺少必须字段是否创建令牌"""
        res = self.client.post(TOKEN_URL, {"username": "xiaoming", "password": ""})
        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class RegisterTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_not_exist_mobile(self):
        """测试不存在的手机号是否通过[不存在的手机号即未注册,返回ok,可以注册]"""
        mobile = 15210198546
        res = self.client.get(f"{MOBILE_URL}{mobile}/")
        self.assertIn("ok", res.data["errmsg"])
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_exist_mobile(self):
        """测试已注册的手机号是否通过"""
        # 先注册拥有当前手机号码的用户信息
        data = {"username": "xiaoming", "password": "123456", "mobile": "13334500000"}
        create_user(**data)
        # 基于已经注册的手机号码进行单元测试
        mobile = "13334500000"
        # mobile = 15212198546
        res = self.client.get(f"{MOBILE_URL}{mobile}/")
        self.assertEqual("手机号码已注册", res.data["errmsg"])
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_mobile(self):
        """测试不合规的手机号是否通过"""
        mobile = 123456789
        res = self.client.get(f"{MOBILE_URL}{mobile}/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_short_password(self):
        """测试短的密码长度是否通过,最小4位,最大18位"""
        pass

    def test_long_password(self):
        """测试长的密码长度是否通过,最小4位,最大18位"""
        pass

    def test_empty_password(self):
        """测试空密码是否通过测试"""
        pass
