import constants
from rest_framework.generics import ListAPIView as DRFListAPIView
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator


class ListAPIView(DRFListAPIView):
    """
    列表页缓存
    """

    @method_decorator(cache_page(constants.LIST_PAGE_CACHE_TIME))
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
