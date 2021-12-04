from django.urls import path

from . import views

urlpatterns = [
    path('', views.CartViewSet.as_view({
        'post': 'add_cart',
        'get': 'list',
        'patch': 'change_select',
        'put': 'together_select',
        'delete': 'delete_course',
    })),
    path(
        'select/', views.CartViewSet.as_view({
            'get': 'cart_select_list',
        })),
]
