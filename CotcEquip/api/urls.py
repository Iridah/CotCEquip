from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TravelerViewSet

router = DefaultRouter()
router.register(r'travelers', TravelerViewSet, basename='traveler')

urlpatterns = [
    path('', include(router.urls)),
]