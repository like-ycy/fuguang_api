from django.contrib import admin

from .models import Activity, Discount, DiscountType, CourseActivityPrice
from .models import CourseDirection, CourseCategory, Course, Teacher, CourseChapter, CourseLesson


class CourseCategoryInLine(admin.StackedInline):
    """课程分类的内嵌类，可以在创建或修改课程方向是也对课程分类进行创建和修改，减少一步操作"""
    model = CourseCategory
    fields = ["id", "name", "direction"]
    ordering = ["id"]
    list_filter = ["direction"]


class CourseDirectionModelAdmin(admin.ModelAdmin):
    """学习方向的模型管理器"""
    list_display = ['id', 'name', 'recomment_home_top', 'recomment_home_hot']
    ordering = ["id"]
    list_filter = ["recomment_home_top", "recomment_home_hot"]
    search_fields = ["name"]
    inlines = [CourseCategoryInLine, ]
    list_per_page = 10


admin.site.register(CourseDirection, CourseDirectionModelAdmin)


class CourseCategoryModelAdmin(admin.ModelAdmin):
    """课程分类的模型管理器"""
    list_display = ["id", "name", "direction"]
    list_filter = ["direction"]
    search_fields = ["name"]
    # 分页配置，一页数据量
    list_per_page = 10
    ordering = ['id']

    # 更新数据时的表单配置项
    fieldsets = (
        ("必填", {'fields': ('name', 'direction', 'remark')}),
        ("选填", {
            'classes': ('collapse',),
            'fields': ('is_show', 'orders'),
        }),
    )
    # 添加数据时的表单配置项
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('name', 'direction', 'remark'),
        }),
    )

    # 当前方法会在显示表单的时候，自动执行，返回值就是表单配置项
    def get_fieldsets(self, request, obj=None):
        """
        获取表单配置项
        :param request: 客户端的http请求对象
        :param obj:     本次修改的模型对象，如果是添加数据操作，则obj为None
        :return:
        """
        if not obj:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)


admin.site.register(CourseCategory, CourseCategoryModelAdmin)


class CourseModelAdmin(admin.ModelAdmin):
    """课程模型管理器"""
    list_display = ["id", "name", "course_cover_small", "course_type", "level", "pub_date", "students", "lessons",
                    "price"]
    list_per_page = 10


admin.site.register(Course, CourseModelAdmin)


class TeacherModelAdmin(admin.ModelAdmin):
    """讲师模型管理器"""
    list_display = ["id", "name", "avatar_small", "title", "role", "signature"]
    list_per_page = 10
    search_fields = ["name"]
    list_filter = ["role"]


admin.site.register(Teacher, TeacherModelAdmin)


class CourseChapterModelAdmin(admin.ModelAdmin):
    """章节模型管理器"""
    list_display = ["id", "name", "pub_date", "text"]
    search_fields = ["name"]
    list_per_page = 10


admin.site.register(CourseChapter, CourseChapterModelAdmin)


class CourseLessonModelAdmin(admin.ModelAdmin):
    """课时模型管理器"""
    list_display = ["id", "text", "text2", "lesson_type", "lesson_link", "duration", "pub_date", "free_trail"]
    list_per_page = 10

    def text(self, obj):
        return obj.__str__()

    text.admin_order_field = "orders"
    text.short_description = "课时名称"


admin.site.register(CourseLesson, CourseLessonModelAdmin)


class ActivityModelAdmin(admin.ModelAdmin):
    """
    优惠活动时间管理器
    """
    list_display = ["id", "name", "start_time", "end_time", "remark"]


admin.site.register(Activity, ActivityModelAdmin)


class DiscountTypeModelAdmin(admin.ModelAdmin):
    """
    优惠类型管理器
    """
    list_display = ["id", "name", "remark"]


admin.site.register(DiscountType, DiscountTypeModelAdmin)


class DiscountModelAdmin(admin.ModelAdmin):
    """
    优惠公式管理器
    """
    list_display = ["id", "name", "discount_type", "condition", "sale"]


admin.site.register(Discount, DiscountModelAdmin)


class CourseActivityPriceModelAdmin(admin.ModelAdmin):
    """
    课程优惠价格的模型管理器
    """
    list_display = ["id", "activity", "course", "discount"]


admin.site.register(CourseActivityPrice, CourseActivityPriceModelAdmin)
