from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'tester'
urlpatterns = [
    path('', TemplateView.as_view(template_name='tester.html'), name='index'),
    path('user/', views.user, name='user'),
    path('qa/', views.question_answer, name='qa'),
    path('qc/', views.question_category, name='qc'),
]