from django.urls import path
from . import views

urlpatterns = [
    path('nav/header/', views.HeaderNavListAPIView.as_view()),
    path('nav/footer/', views.FooterNavListAPIView.as_view()),
    path('banner/', views.BannerListAPIView.as_view()),
]
