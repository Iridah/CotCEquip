from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TravelerViewSet,
    roster_view,
    roster_search,
    traveler_modal,
    traveler_update,
)

router = DefaultRouter()
router.register(r'travelers', TravelerViewSet, basename='traveler')

urlpatterns = [
    # API REST
    path('api/', include(router.urls)),
    # Vistas HTML
    path('', roster_view, name='roster'),
    path('roster/search/', roster_search, name='roster_search'),
    path('roster/traveler/<int:pk>/modal/', traveler_modal, name='traveler_modal'),
    path('roster/traveler/<int:pk>/update/', traveler_update, name='traveler_update'),
]