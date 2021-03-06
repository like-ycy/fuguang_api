import logging
import random

from django.conf import settings
from django.db import transaction
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView, GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_jwt.views import ObtainJSONWebToken

import constants
from courses.models import Course, CourseLesson
from courses.paginations import CourseListPageNumberPagination
from fuguangapi.utils.tencentcloudapi import TencentCloudAPI, TencentCloudSDKException
from .models import User, UserCourse, StudyProgress
from .serializers import UserRegisterModelSerializer, UserCourseModelSerializer
# from ronglianyunapi import send_sms
# from mycelery.sms.tasks import send_sms
from .tasks import send_sms

logger = logging.getLogger('django')


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
    """学习进度"""
    permission_classes = [IsAuthenticated]
    serializers_class = UserCourseModelSerializer

    def get(self, request, course_id):
        """获取用户的课程学习进度"""
        user = request.user
        try:
            user_course = UserCourse.objects.get(user=user, course_id=course_id)
        except UserCourse.DoesNotExist:
            return Response({"errmsg": "当前课程未购买"}, status=status.HTTP_400_BAD_REQUEST)
        # 章节id
        chapter_id = user_course.chapter_id
        if chapter_id:
            """学习过课程"""
            lesson = user_course.lesson
        else:
            """未学习过课程"""
            # 获取课程第1个章节
            chapter = user_course.course.chapter_list.order_by('orders').first()
            # 获取课程第1个章节的第一个课时
            lesson = chapter.lesson_list.order_by('orders').first()
            # 更新用户学习进度
            user_course.chapter = chapter
            user_course.lesson = lesson
            user_course.save()

        serializer = self.get_serializer(user_course)
        data = serializer.data
        # 获取课时类型和连接
        data['lesson_type'] = lesson.lesson_type
        data['lesson_link'] = lesson.lesson_link

        return Response(data)


class StudyLessonAPIView(APIView):
    """用户在当前课时的学习进度"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        lesson_id = int(request.query_params.get("lesson"))
        user = request.user

        # 查找课时
        lesson = CourseLesson.objects.get(id=lesson_id)
        progress = StudyProgress.objects.filter(user=user, lesson=lesson).first()

        # 如果查询没有进度，则默认进度进度为0
        if progress is None:
            progress = StudyProgress.objects.create(user=user, lesson=lesson, study_time=0)
        return Response(progress.study_time)


class StudyProgressAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """添加课时学习进度"""
        try:
            # 1. 接收客户端提交的视频进度和课时ID
            study_time = int(request.data.get("time"))
            lesson_id = int(request.data.get("lesson"))
            user = request.user

            # 判断当前课时是否免费或者当前课时所属的课程是否被用户购买了

            # 判断本次更新学习时间是否超出阈值，当超过阈值，则表示用户已经违规快进了。
            if study_time > constants.MAV_SEEK_TIME:
                raise Exception

            # 查找课时
            lesson = CourseLesson.objects.get(pk=lesson_id)

        except:
            return Response({"error": "无效的参数或当前课程信息不存在！"})

        with transaction.atomic():
            save_id = transaction.savepoint()
            try:
                # 2. 记录课时学习进度
                progress = StudyProgress.objects.filter(user=user, lesson=lesson).first()

                if progress is None:
                    """新增一条用户与课时的学习记录"""
                    progress = StudyProgress(
                        user=user,
                        lesson=lesson,
                        study_time=study_time
                    )
                else:
                    """直接更新现有的学习时间"""
                    progress.study_time = int(progress.study_time) + int(study_time)

                progress.save()

                # 3. 记录课程学习的总进度
                user_course = UserCourse.objects.get(user=user, course=lesson.course)
                user_course.study_time = int(user_course.study_time) + int(study_time)

                # 用户如果往后观看章节，则记录下
                if lesson.chapter.orders > user_course.chapter.orders:
                    user_course.chapter = lesson.chapter

                # 用户如果往后观看课时，则记录下
                if lesson.orders > user_course.lesson.orders:
                    user_course.lesson = lesson

                user_course.save()

                return Response({"message": "课时学习进度更新完成！"})

            except Exception as e:
                logger.error(f"更新课时进度失败！:{e}")
                transaction.savepoint_rollback(save_id)
                return Response({"error": "当前课时学习进度丢失！"})
