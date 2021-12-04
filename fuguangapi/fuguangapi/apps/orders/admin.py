from django.contrib import admin

from .models import Order, OrderDetail


class OrderDetailInLine(admin.StackedInline):
    model = OrderDetail
    fields = ['course', 'price', 'real_price', 'discount_name', ]


class OrderModelAdmin(admin.ModelAdmin):
    """订单模型管理类"""
    list_display = ['id', 'order_number', 'user', 'total_price', 'real_price', 'pay_type',
                    'pay_time', 'created_time', 'updated_time']
    inlines = [OrderDetailInLine]


admin.site.register(Order, OrderModelAdmin)
