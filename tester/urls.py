from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('', TemplateView.as_view(template_name='tester.html'), name='index'),
    path('user/', views.user, name='user'),
    path('qa/', views.qa, name='qa'),
    path('qc/', views.qc, name='qc'),
]