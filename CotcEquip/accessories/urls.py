from django.urls import path
from . import views
 
urlpatterns = [
    path('', views.accessories_view, name='accessories'),
]