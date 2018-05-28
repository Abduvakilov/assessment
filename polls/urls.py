from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('start/', views.start, name='start'),
    path('test/<int:question_no>/', views.test, name='test'),
    path('tanla/<int:question_no>/', views.choose, name='tanla'),
    path('finish/', views.finish, name='finish'),
    path('confirm/', views.confirm, name='confirm'),
    path('tester/', views.tester, name='tester'),
]


