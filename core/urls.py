from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path('', include('assessment.urls', namespace='assessment')),
    path('tester/', include('tester.urls', namespace='tester')),
    path('admin/', admin.site.urls),
    path('login/', auth_views.login, name='login'),
    path('logout/', auth_views.logout, name='logout'),
    path('i18n/', include('django.conf.urls.i18n')),
]


from django.conf.urls.static import static
from django.conf import settings
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)