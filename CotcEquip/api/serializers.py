from rest_framework import serializers
from .models import Traveler, RosterEntry


class RosterEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = RosterEntry
        fields = '__all__'


class TravelerSerializer(serializers.ModelSerializer):
    roster_entry = RosterEntrySerializer(read_only=True)

    class Meta:
        model = Traveler
        fields = [
            'id', 'name', 'rarity', 'job', 'weapon_type', 'element',
            'hp_120', 'sp_120', 'p_atk_120', 'p_def_120',
            'e_atk_120', 'e_def_120', 'crit_120', 'spd_120',
            'roster_entry'
        ]