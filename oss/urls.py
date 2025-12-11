# oss/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('test-connection/', views.test_connection, name='oss_test_connection'),
    path('upload-test/', views.upload_test_file, name='oss_upload_test'),
    path('list-files/', views.list_files, name='oss_list_files'),
    path('delete-file/', views.delete_file, name='oss_delete_file'),
]
