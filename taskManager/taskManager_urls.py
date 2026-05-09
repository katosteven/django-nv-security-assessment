"""App URL routing (Django 5 path API)."""
from django.urls import path, re_path

from taskManager import views

urlpatterns = [
    path('', views.index, name='index'),

    # File
    path('download/<int:file_id>/', views.download, name='download'),
    path('<int:project_id>/upload/', views.upload, name='upload'),
    path('downloadprofilepic/<int:user_id>/',
         views.download_profile_pic, name='download_profile_pic'),

    # Auth
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('manage_groups/', views.manage_groups, name='manage_groups'),
    path('profile/', views.profile, name='profile'),
    path('change_password/', views.change_password, name='change_password'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('reset_password/', views.reset_password, name='reset_password'),
    path('profile/<int:user_id>', views.profile_by_id, name='profile_by_id'),
    path('profile_view/<int:user_id>', views.profile_view, name='profile_view'),

    # Projects
    path('project_create/', views.project_create, name='project_create'),
    path('<int:project_id>/edit_project/', views.project_edit, name='project_edit'),
    path('manage_projects/', views.manage_projects, name='manage_projects'),
    path('<int:project_id>/project_delete/', views.project_delete, name='project_delete'),
    path('<int:project_id>/', views.project_details, name='project_details'),
    path('project_list/', views.project_list, name='project_list'),

    # Tasks
    path('<int:project_id>/task_create/', views.task_create, name='task_create'),
    path('<int:project_id>/<int:task_id>/', views.task_details, name='task_details'),
    path('<int:project_id>/task_edit/<int:task_id>', views.task_edit, name='task_edit'),
    path('<int:project_id>/task_delete/<int:task_id>', views.task_delete, name='task_delete'),
    path('<int:project_id>/task_complete/<int:task_id>',
         views.task_complete, name='task_complete'),
    path('task_list/', views.task_list, name='task_list'),
    path('<int:project_id>/manage_tasks/', views.manage_tasks, name='manage_tasks'),

    # Notes
    path('<int:project_id>/<int:task_id>/note_create/',
         views.note_create, name='note_create'),
    path('<int:project_id>/<int:task_id>/note_edit/<int:note_id>',
         views.note_edit, name='note_edit'),
    path('<int:project_id>/<int:task_id>/note_delete/<int:note_id>',
         views.note_delete, name='note_delete'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('search/', views.search, name='search'),

    # Tutorials
    path('tutorials/', views.tutorials, name='tutorials'),
    re_path(r'^tutorials/(?P<vuln_id>[a-z\-]+)/$',
            views.show_tutorial, name='show_tutorial'),

    # Settings (debug)
    path('settings/', views.tm_settings, name='settings'),
]
