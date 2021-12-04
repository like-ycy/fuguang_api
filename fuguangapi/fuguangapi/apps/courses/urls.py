from django.urls import path, re_path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register('search', views.CourseSearchViewSet, basename='search')

urlpatterns = [
                  path('directions/', views.CourseDirectionListView.as_view()),
                  path('categories/', views.CourseCategoryListView.as_view()),
                  re_path('categories/(?P<direction>\d+)/', views.CourseCategoryListView.as_view()),
                  re_path('^(?P<direction>\d+)/(?P<category>\d+)/$', views.CourseListAPiView.as_view()),
                  path('hot_word/', views.HotWordAPIView.as_view()),
                  re_path('^(?P<pk>\d+)/$', views.CourseRetrieveAPIView.as_view()),
                  path('type/', views.CourseTypeListAPIView.as_view()),
                  re_path("^polyv/token/(?P<vid>\w+)/$", views.PolyvViewSet.as_view({"get": "token"})),
              ] + router.urls
