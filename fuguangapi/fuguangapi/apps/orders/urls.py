from django.urls import path, re_path

from . import views

urlpatterns = [
    path('', views.OrderCreateAPIView.as_view(), name='order_create'),
    path('pay/status/', views.OrderPayChoicesAPIView.as_view(), name='order_pay_choices'),
    path('list/', views.OrderListAPIView.as_view(), name='order_list'),
    re_path("^(?P<pk>\d+)/$", views.OrderViewSet.as_view({"put": "pay_cancel"})),

]
