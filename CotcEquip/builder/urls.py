from django.urls import path
from . import views
 
urlpatterns = [
    path('', views.builder_view, name='builder'),
    path('optimize/', views.optimize_view, name='builder_optimize'),
]