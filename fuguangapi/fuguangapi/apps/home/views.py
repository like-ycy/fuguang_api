from home.models import Nav, Banner
import constants
from home.serializers import NavModelSerializer, BannerModuleSerializer
from views import ListAPIView


class HeaderNavListAPIView(ListAPIView):
    """
    头部导航
    """
    queryset = Nav.objects.filter(is_delete=False, is_show=True, position=constants.NAV_HEADER
                                  ).order_by("orders", "-id")[:constants.NAV_HEADER_SIZE]
    serializer_class = NavModelSerializer


class FooterNavListAPIView(ListAPIView):
    """
    脚部导航
    """
    queryset = Nav.objects.filter(is_delete=False, is_show=True, position=constants.NAV_FOOTER
                                  ).order_by("orders", "-id")[:constants.NAV_FOOTER_SIZE]
    serializer_class = NavModelSerializer


class BannerListAPIView(ListAPIView):
    """
    轮播图
    """
    queryset = Banner.objects.filter(is_delete=False, is_show=True).order_by("orders", "-id")[:constants.BANNER_SIZE]
    serializer_class = BannerModuleSerializer
