from django.shortcuts import render
from api.models import Traveler
from .calculator import calculate_rankings


def rankings_view(request):
    travelers = Traveler.objects.all()
    results   = calculate_rankings(travelers)
    return render(request, 'rankings/rankings.html', {'results': results})