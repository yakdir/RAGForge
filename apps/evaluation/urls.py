from django.urls import path
from . import views

app_name = 'evaluation'

urlpatterns = [
    path('datasets/', views.dataset_list, name='datasets'),
    path('datasets/create/', views.dataset_create, name='dataset_create'),
    path('datasets/<uuid:dataset_id>/delete/', views.dataset_delete, name='dataset_delete'),
    path('runs/', views.run_list, name='runs'),
    path('runs/create/', views.run_create, name='run_create'),
    path('runs/grid-search/', views.grid_search, name='grid_search'),
    path('runs/<uuid:run_id>/', views.run_detail, name='run_detail'),
    path('runs/<uuid:run_id>/delete/', views.run_delete, name='run_delete'),
]
