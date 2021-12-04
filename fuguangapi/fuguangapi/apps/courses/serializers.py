from django.conf import settings
from drf_haystack.serializers import HaystackSerializer
from rest_framework import serializers

from .models import CourseDirection, CourseCategory, Course, Teacher, CourseChapter, CourseLesson
from .search_indexes import CourseIndex


class CourseDirectionSerializer(serializers.ModelSerializer):
    """学习方向序列化器"""

    class Meta:
        model = CourseDirection
        fields = ('id', 'name')


class CourseCategorySerializer(serializers.ModelSerializer):
    """学习方向序列化器"""

    class Meta:
        model = CourseCategory
        fields = ('id', 'name')


class CourseModelSerializer(serializers.ModelSerializer):
    """课程信息序列化器"""

    class Meta:
        model = Course
        fields = ('id', 'name', "course_cover", "level", "get_level_display",
                  "students", "status", "get_status_display",
                  "lessons", "pub_lessons", "price", "discount")


class CourseIndexHaystackSerializer(HaystackSerializer):
    """搜索序列化器"""

    class Meta:
        index_classes = [CourseIndex]
        fields = ["text", "id", "name", "course_cover", "get_level_display", "students", "get_status_display",
                  "pub_lessons", "price", "discount", "orders"]

    def to_representation(self, instance):
        """用于指定返回数据字段"""
        instance.course_cover = f'https://{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT}/uploads/{instance.course_cover}'
        return super().to_representation(instance)


class CourseTeacherModelSerializer(serializers.ModelSerializer):
    """课程讲师序列化器"""

    class Meta:
        model = Teacher
        fields = ['id', 'name', 'title', 'signature', 'avatar', 'role', 'get_role_display', 'brief']


class CourseLessonModelserializer(serializers.ModelSerializer):
    """课程课时序列化器"""

    class Meta:
        model = CourseLesson
        fields = ['id', 'name', 'orders', 'duration', "lesson_type", "lesson_link", "free_trail"]


class CourseChapterModelSerializer(serializers.ModelSerializer):
    """课程章节序列化器"""

    lesson_list = CourseLessonModelserializer(many=True)

    class Meta:
        model = CourseChapter
        fields = ["id", "orders", "name", "summary", "lesson_list"]


class CourseRetrieveModelSerializer(serializers.ModelSerializer):
    """课程详情序列化器"""
    direction_name = serializers.CharField(source='direction.name')
    category_name = serializers.CharField(source='category.name')
    # 讲师信息
    teacher = CourseTeacherModelSerializer()
    # 章节列表
    chapter_list = CourseChapterModelSerializer(many=True)

    class Meta:
        model = Course
        fields = ["name", "course_cover", "course_video", "level", "get_level_display",
                  "description", "pub_date", "status", "get_status_display", "students", "discount",
                  "credit", "lessons", "pub_lessons", "price", "direction", "direction_name", "category",
                  "category_name", "teacher", "chapter_list", "can_free_study", ]
