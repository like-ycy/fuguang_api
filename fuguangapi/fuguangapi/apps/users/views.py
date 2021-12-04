import random

from django.conf import settings
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView, GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_jwt.views import ObtainJSONWebToken

from courses.models import Course
from courses.paginations import CourseListPageNumberPagination
from fuguangapi.utils.tencentcloudapi import TencentCloudAPI, TencentCloudSDKException
from .models import User, UserCourse
from .serializers import UserRegisterModelSerializer, UserCourseModelSerializer
# from ronglianyunapi import send_sms
# from mycelery.sms.tasks import send_sms
from .tasks import send_sms


class LoginAPIView(ObtainJSONWebToken):
    """
    用户登录视图
    """

    def post(self, request, *args, **kwargs):
        """
        校验用户操作验证码成功以后的ticket临时票据
        """
        if settings.IS_TEST:
            return super().post(request, *args, **kwargs)
        try:
            api = TencentCloudAPI()
            result = api.captcha(
                request.data.get("ticket"),
                request.data.get("randstr"),
                request._request.META.get("REMOTE_ADDR"),
            )
            if result:
                # print("验证通过")
                return super().post(request, *args, **kwargs)
            else:
                raise TencentCloudSDKException
        except TencentCloudSDKException as err:
            return Response({"errmsg": "验证码校验失败"}, status=status.HTTP_400_BAD_REQUEST)


class MobileAPIView(APIView):
    """
    手机号是否已经注册
    """

    def get(self, request, mobile):
        """
        校验手机号是否已注册
        :param request:
        :param mobile: 手机号
        :return:
        """
        try:
            user = User.objects.get(mobile=mobile)
            return Response({"errmsg": "手机号码已注册"}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            # 查不到说明手机号未注册
            return Response({"errmsg": "ok"}, status=status.HTTP_200_OK)


class UserAPIView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterModelSerializer


class SMSAPIView(APIView):
    """
    发送手机验证码
    """

    def get(self, request, mobile):
        """
        :param request:
        :param mobile: 手机号
        :return:
        """
        redis = get_redis_connection("sms_code")
        # 判断手机短信是否处于发送冷却中[60秒只能发送一次]
        interval = redis.ttl(f'interval_{mobile}')
        if interval != -2:
            return Response({"errmsg": f"短信发送过于频繁，请于{interval}秒后再次点击获取！"},
                            status=status.HTTP_400_BAD_REQUEST)
        # 生成随机验证码
        code = f"{random.randint(0, 999999):06d}"
        # 短信有效期
        time = settings.RONGLIANYUN.get("sms_expire")
        # 短信发送间隔时间
        sms_interval = settings.RONGLIANYUN.get("sms_interval")
        # 异步发送短信
        # send_sms(settings.RONGLIANYUN.get('reg_tid'), mobile, datas=(code, time // 60))
        send_sms.delay(settings.RONGLIANYUN.get("reg_tid"), mobile, datas=(code, time // 60))

        # 将验证码存入redis
        # 使用redis的管道对象pipeline, 一次执行多条命令
        pipe = redis.pipeline()
        pipe.multi()
        pipe.setex(f"sms_{mobile}", time, code)
        pipe.setex(f"interval_{mobile}", sms_interval, 1)
        pipe.execute()

        return Response({"errmsg": "OK"}, status=status.HTTP_200_OK)


class CourseListAPiView(ListAPIView):
    """
    获取用户的课程列表
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserCourseModelSerializer
    pagination_class = CourseListPageNumberPagination

    def get_queryset(self):
        user = self.request.user
        query = UserCourse.objects.filter(user=user)
        course_type = int(self.request.query_params.get("type", -1))
        course_type_list = [item[0] for item in Course.COURSE_TYPE]
        if course_type in course_type_list:
            query = query.filter(course__course_type=course_type)
        return query.order_by("-id").all()


class UserCourseAPIView(GenericAPIView):
    pass
