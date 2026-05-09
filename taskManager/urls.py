"""Top-level URL routing (Django 5 path API)."""
from django.contrib import admin
from django.urls import include, path

from taskManager import views

urlpatterns = [
    path('', views.index, name='index'),
    path('taskManager/', include(('taskManager.taskManager_urls', 'taskManager'),
                                  namespace='taskManager')),
    path('admin/', admin.site.urls),
]
