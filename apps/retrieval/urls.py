from django.urls import path
from . import views

app_name = 'retrieval'

urlpatterns = [
    path('search/', views.search_page, name='search'),
]
