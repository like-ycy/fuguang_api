import re

from django.conf import settings
from django_redis import get_redis_connection
from rest_framework import serializers

import constants
from authenticate import generate_jwt_token
from tencentcloudapi import TencentCloudAPI
from .models import User, UserCourse


class UserRegisterModelSerializer(serializers.ModelSerializer):
    """
    用户注册的序列化器
    """
    re_password = serializers.CharField(required=True, write_only=True)
    sms_code = serializers.CharField(min_length=4, max_length=6, required=True, write_only=True)
    token = serializers.CharField(read_only=True)
    ticket = serializers.CharField(write_only=True)
    randstr = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('mobile', 'password', 're_password', 'sms_code', 'token', 'ticket', 'randstr')
        extra_kwargs = {
            'password': {
                'write_only': True, 'required': True, 'min_length': 4, 'max_length': 18
            },
            'mobile': {
                'write_only': True, 'required': True
            }
        }

    def validate(self, data):
        """
        验证客户端数据
        """
        # 手机号格式验证
        mobile = data.get('mobile', None)
        if not re.match("^1[3-9]\d{9}$", mobile):
            raise serializers.ValidationError(detail="手机号码格式错误", code='mobile')

        # 密码和确认密码是否一致
        password = data.get('password')
        re_password = data.get('re_password')
        if password != re_password:
            raise serializers.ValidationError(detail="两次密码不一致", code='password')

        # 验证码长度
        sms_code = data.get('sms_code')
        if len(sms_code) != 6:
            raise serializers.ValidationError(detail="验证码长度错误", code='sms_code')

        # 手机号是否注册
        try:
            User.objects.get(mobile=mobile)
            raise serializers.ValidationError(detail="手机号已注册")
        except User.DoesNotExist:
            pass

        # 验证短信验证码
        if not settings.IS_TEST:

            # 验证腾讯云的滑动验证码
            api = TencentCloudAPI()
            result = api.captcha(
                data.get('ticket'),
                data.get('randstr'),
                self.context["request"]._request.META.get("REMOTE_ADDR")
            )
            if not result:
                raise serializers.ValidationError(detail="滑动验证码失败", code="verify")

            # 验证短信验证码, sms_code为dev配置文件中的2库
            redis = get_redis_connection("sms_code")
            code = redis.get(f"sms_{mobile}")  # 根据手机号获取redis中的验证码

            # 验证码错误处理
            if not code:
                raise serializers.ValidationError(detail="验证码失效", code="sms_code")
            if code.decode() != data.get('sms_code'):
                raise serializers.ValidationError(detail="验证码错误", code="sms_code")
            redis.delete(f"sms_{mobile}")

            # 验证码正确，返回数据
            return data

    def create(self, validated_data):
        """
        保存用户信息
        """
        mobile = validated_data.get('mobile')
        password = validated_data.get('password')

        user = User.objects.create_user(
            username=mobile,
            password=password,
            avatar=constants.DEFAULT_USER_AVATAR,
            mobile=mobile,
        )

        # 注册成功后，免登陆，生成token
        user.token = generate_jwt_token(user)
        return user


class UserCourseModelSerializer(serializers.ModelSerializer):
    """
    用户课程序列化器
    """
    course_cover = serializers.ImageField(source="course.course_cover")
    course_name = serializers.CharField(source="course.name")
    chapter_name = serializers.CharField(source="chapter.name", default="")
    chapter_id = serializers.IntegerField(source="chapter.id", default=0)
    chapter_orders = serializers.IntegerField(source="chapter.orders", default=0)
    lesson_id = serializers.IntegerField(source="lesson.id", default=0)
    lesson_name = serializers.CharField(source="lesson.name", default="")
    lesson_orders = serializers.IntegerField(source="lesson.orders", default=0)
    course_type = serializers.IntegerField(source="course.course_type", default=0)
    get_course_type_display = serializers.CharField(source="course.get_course_type_display", default="")

    class Meta:
        model = UserCourse
        fields = ["course_id", "course_cover", "course_name", "study_time", "chapter_id", "chapter_orders",
                  "chapter_name", "lesson_id", "lesson_orders", "lesson_name", "course_type", "get_course_type_display",
                  "progress", "note", "qa", "code"]
