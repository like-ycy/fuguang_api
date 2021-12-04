from django.contrib import admin
from django_redis import get_redis_connection

from .models import Coupon, CouponDirection, CouponCourseCat, CouponCourse, CouponLog
from .services import add_coupon_to_redis


class CouponDirectionInLine(admin.TabularInline):
    """学习方向的内嵌类"""
    model = CouponDirection
    fields = ['id', 'direction']


class CouponCourseCatInLine(admin.TabularInline):
    """课程分类的内嵌类"""
    model = CouponCourseCat
    fields = ['id', 'category']


class CouponCourseInLine(admin.TabularInline):
    """课程的内嵌类"""
    model = CouponCourse
    fields = ['id', 'course']


class CouponModelAdmin(admin.ModelAdmin):
    """优惠券模型管理类"""
    list_display = ['id', 'name', 'start_time', 'end_time', 'total',
                    'has_total', 'coupon_type', 'get_type']
    list_filter = ['name']
    search_fields = ['name']
    inlines = [CouponDirectionInLine, CouponCourseCatInLine, CouponCourseInLine]


admin.site.register(Coupon, CouponModelAdmin)


class CouponLogModelAdmin(admin.ModelAdmin):
    """优惠券发放和使用模型管理类"""
    list_display = ['id', 'user', 'coupon', 'order', 'use_time', 'use_status']
    list_filter = ['user']
    search_fields = ['user']
    ordering = ["id"]

    # 更新数据时的表单配置项
    fieldsets = (
        ("必填", {'fields': ('name', 'user', 'coupon')}),
        ("选填", {
            'classes': ('collapse',),
            'fields': ('order', 'use_time', 'use_status', 'orders',),
        }),
    )

    # 添加数据时的表单配置项
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('name', 'user', 'coupon'),
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

    def save_model(self, request, obj, form, change):
        """
        保存或更新记录时自动执行的钩子
        request: 本次客户端提交的请求对象
        obj: 本次操作的模型实例对象
        form: 本次客户端提交的表单数据
        change: 值为True，表示更新数据，值为False，表示添加数据
        """
        obj.save()  # obj为模型中的CouponLog
        redis = get_redis_connection('coupon')
        if obj.use_status == 0 and obj.use_time is None:
            # 记录优惠券信息到redis中
            add_coupon_to_redis(obj)
        else:
            redis.delete(f"{obj.user.id}:{obj.id}")

    def delete_model(self, request, obj):
        """删除记录时自动执行的钩子"""
        # 如果系统后台管理员删除当前优惠券记录，则redis中的对应记录也被删除
        redis = get_redis_connection('coupon')
        redis.delete(f'{obj.user.id}:{obj.id}')
        obj.delete()

    def delete_queryset(self, request, queryset):
        """在列表页中进行删除优惠券记录时，也要同步删除容redis中的记录"""
        redis = get_redis_connection('coupon')
        for obj in queryset:
            redis.delete(f'{obj.user.id}:{obj.id}')
        queryset.delete()


admin.site.register(CouponLog, CouponLogModelAdmin)
