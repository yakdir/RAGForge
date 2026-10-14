from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('', views.document_list, name='list'),
    path('upload/', views.document_upload, name='upload'),
    path('<uuid:doc_id>/', views.document_detail, name='detail'),
    path('<uuid:doc_id>/delete/', views.document_delete, name='delete'),
]
