from datetime import datetime, timedelta

from django.conf import settings
from django_redis import get_redis_connection
from drf_haystack.filters import HaystackFilter
from drf_haystack.viewsets import HaystackViewSet
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

import constants
from fuguangapi.libs.polyv import PolyvPlayer
from .models import CourseDirection, CourseCategory, Course
from .paginations import CourseListPageNumberPagination
from .serializers import CourseDirectionSerializer, CourseCategorySerializer, CourseModelSerializer
from .serializers import CourseIndexHaystackSerializer
from .serializers import CourseRetrieveModelSerializer


class CourseDirectionListView(ListAPIView):
    """学习方向视图"""
    queryset = CourseDirection.objects.filter(
        is_show=True, is_delete=False).order_by("orders", "id")
    serializer_class = CourseDirectionSerializer


class CourseCategoryListView(ListAPIView):
    """学习分类视图"""
    serializer_class = CourseCategorySerializer
    # 取消分页
    pagination_class = None

    def get_queryset(self):
        queryset = CourseCategory.objects.filter(is_show=True, is_delete=False)
        # 获取路由参数
        direction = int(self.kwargs.get("direction", 0))
        # 课程方向为0，查询所有课程分类，大于0，查询指定课程方向下的课程分类
        if direction > 0:
            queryset = queryset.filter(direction_id=direction)
        return queryset.order_by("orders", "id")


class CourseListAPiView(ListAPIView):
    """所有课程视图"""
    serializer_class = CourseModelSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ("id", "students", "orders")
    pagination_class = CourseListPageNumberPagination

    def get_queryset(self):
        """列表页数据"""
        queryset = Course.objects.filter(is_delete=False, is_show=True).order_by("-orders", "-id")
        direction = int(self.kwargs.get("direction", 0))
        category = int(self.kwargs.get("category", 0))

        # 只有在学习方向大于0的情况下才进行学习方向的过滤
        if direction > 0:
            queryset = queryset.filter(direction=direction)

        # 只有在课程分类大于0的情况下才进行课程分类的过滤
        if category > 0:
            queryset = queryset.filter(category=category)

        return queryset.all()


class CourseSearchViewSet(HaystackViewSet):
    # 指定本次搜索的最终真实数据的保存模型
    index_models = [Course]
    serializer_class = CourseIndexHaystackSerializer
    filter_backends = [OrderingFilter, HaystackFilter]
    ordering_fields = ('id', 'students', 'orders')
    pagination_class = CourseListPageNumberPagination

    def list(self, request, *args, **kwargs):
        redis = get_redis_connection("hot_word")
        text = request.query_params.get("text")
        if text:
            key = f'{constants.DEFAULT_HOT_WORD}:{datetime.now().strftime("%Y:%m:%d")}'
            is_exists = redis.exists(key)
            redis.zincrby(key, 1, text)
            if not is_exists:
                redis.expire(key, constants.HOT_WORD_EXPIRE * 24 * 3600)
        return super().list(request, *args, **kwargs)


class HotWordAPIView(APIView):
    """热搜词视图"""

    def get(self, request):
        redis = get_redis_connection("hot_word")
        # 获取指定天数的热搜词
        date_list = []
        for i in range(0, constants.HOT_WORD_EXPIRE):
            day = datetime.now() - timedelta(days=i)
            key = f'{constants.DEFAULT_HOT_WORD}:{day.year}:{day.month}:{day.day}'
            date_list.append(key)

        # 先删除原有的热搜词
        redis.delete(constants.DEFAULT_HOT_WORD)
        # 根据date_list找到最近指定天数的所有集合，并完成并集计算，产生新的有序统计集合constants.DEFAULT_HOT_WORD
        redis.zunionstore(constants.DEFAULT_HOT_WORD, date_list, aggregate='sum')
        # 按分数store进行倒序显示排名靠前的指定数量的热词
        word_list = redis.zrevrange(constants.DEFAULT_HOT_WORD, 0, constants.HOT_WORD_LENGTH - 1)
        print(word_list)
        return Response(word_list)


class CourseRetrieveAPIView(RetrieveAPIView):
    """课程详情视图"""
    queryset = Course.objects.filter(is_delete=False, is_show=True)
    serializer_class = CourseRetrieveModelSerializer


class CourseTypeListAPIView(APIView):
    """课程类型"""

    def get(self, request):
        return Response(Course.COURSE_TYPE)


class PolyvViewSet(ViewSet):
    """保利威云视频服务相关的API接口"""
    permission_classes = [IsAuthenticated]

    def token(self, request, vid):
        """获取视频播放的授权令牌"""
        userId = settings.POLYV["userId"]
        secretkey = settings.POLYV["secretkey"]
        tokenUrl = settings.POLYV["tokenUrl"]
        polyv = PolyvPlayer(userId, secretkey, tokenUrl)

        user_ip = request.META.get("REMOTE_ADDR")  # 客户端的IP地址
        user_id = request.user.id  # 用户ID
        user_name = request.user.username  # 用户名

        token = polyv.get_video_token(vid, user_ip, user_id, user_name)

        return Response({"token": token})
