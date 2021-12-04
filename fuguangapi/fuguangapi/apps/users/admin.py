from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, _

from .models import User, Credit


class UserModelAdmin(UserAdmin):
    list_display = ["id", "username", "avatar_small", "mobile", "money", "credit"]
    # list_editable = ["credit"]
    # search_fields = ["username", "mobile"]
    ordering = ["id"]
    fieldsets = (
        (None, {'fields': ('username', 'password', 'avatar', 'money', 'credit')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
    )

    def save_model(self, request, obj, form, change):
        if change:
            """更新用户信息"""
            user = User.objects.get(pk=obj.pk)
            has_credit = user.credit
            new_credit = obj.credit

            Credit.objects.create(
                user=user,
                number=int(new_credit - has_credit),
                operation=2
            )
        obj.save()

        if not change:
            """创建用户信息"""
            Credit.objects.create(
                user=obj.id,
                number=obj.credit,
                operation=2
            )


admin.site.register(User, UserModelAdmin)


class CreditModelAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "number", "__str__"]
    ordering = ["id"]


admin.site.register(Credit, CreditModelAdmin)
