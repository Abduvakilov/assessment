from django.urls import path

from . import views

app_name = 'assessment'
urlpatterns = [
    path('', views.index, name='index'),
    path('lang/', views.lang, name='lang'),
    path('lang/<int:language_id>/', views.lang, name='lang'),
    path('start/', views.start, name='start'),
    path('test/<int:question_no>/', views.test, name='test'),
    path('tanla/<int:question_no>/', views.choose, name='tanla'),
    path('finish/', views.finish, name='finish'),
    path('confirm/', views.confirm, name='confirm'),

    # Tester Zone
    path('tester/', views.tester, name='tester'),
    path('tester/import/', views.import_questions, name='import'),
    path('tester/result/<int:response_id>/', views.result, name='result'),
    path('tester/report/', views.report, name='report'),
]