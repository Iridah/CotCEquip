from django.contrib import admin
from .models import Traveler, RosterEntry


@admin.register(Traveler)
class TravelerAdmin(admin.ModelAdmin):
    list_display = ['name', 'rarity', 'job', 'element', 'is_released']
    search_fields = ['name', 'job', 'element']
    list_filter = ['rarity', 'element', 'job', 'is_released']
    ordering = ['name']


@admin.register(RosterEntry)
class RosterEntryAdmin(admin.ModelAdmin):
    list_display = ['traveler', 'is_obtained', 'is_6_stars', 'awakening_level', 'ultimate_level']
    list_filter = ['is_obtained', 'is_6_stars']
    search_fields = ['traveler__name']
