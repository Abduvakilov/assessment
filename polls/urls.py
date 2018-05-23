from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('start/', views.start, name='start'),
    path('test/', views.test, name='test'),
    path('tanla/', views.choose, name='tanla'),
]
