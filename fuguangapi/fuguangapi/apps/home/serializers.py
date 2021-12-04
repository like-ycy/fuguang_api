from rest_framework import serializers
from .models import Nav, Banner


class NavModelSerializer(serializers.ModelSerializer):
    """
    导航栏序列化器
    """

    class Meta:
        model = Nav
        fields = ["name", "link", "is_http"]


class BannerModuleSerializer(serializers.ModelSerializer):
    """
    首页轮播图序列化器
    """

    class Meta:
        model = Banner
        fields = ["image", "link", "name", "is_http"]
