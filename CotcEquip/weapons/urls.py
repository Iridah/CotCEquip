from django.urls import path
from . import views

urlpatterns = [
    path('', views.weapons_view, name='weapons'),
]