from django.urls import path
from . import views
 
urlpatterns = [
    path('', views.armors_view, name='armors'),
]