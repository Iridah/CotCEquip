from django.urls import path
from . import views

urlpatterns = [
    path('', views.inventory_view, name='inventory'),
    path('toggle/', views.toggle_item, name='inventory_toggle'),
]