from django.shortcuts import render
from api.models import Accessory
 
def accessories_view(request):
    accessories = Accessory.objects.all().order_by('name')
 
    q      = request.GET.get('q', '').strip()
    solo_a4 = request.GET.get('solo_a4', '')
 
    if q:
        accessories = accessories.filter(name__icontains=q)
    if solo_a4:
        accessories = accessories.filter(is_a4=True)
 
    return render(request, 'accessories/accessories.html', {
        'accessories': accessories,
        'q':           q,
        'solo_a4':     solo_a4,
    })