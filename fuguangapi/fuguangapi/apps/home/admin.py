from django.contrib import admin

from .models import Nav, Banner


class NavModelAdmin(admin.ModelAdmin):
    """导航栏模型管理器"""
    list_display = ['id', 'name', 'link', 'is_http']
    list_filter = ['name']
    search_fields = ['name']
    list_per_page = 10
    ordering = ['id']


admin.site.register(Nav, NavModelAdmin)


class BannerModelAdmin(admin.ModelAdmin):
    """轮播图模型管理器"""
    list_display = ['id', 'image_html', 'name', 'link', 'is_http']


admin.site.register(Banner, BannerModelAdmin)
