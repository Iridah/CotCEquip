from django.shortcuts import get_object_or_404, render
from django.db.models import Count, Q
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Traveler, RosterEntry
from .serializers import TravelerSerializer, RosterEntrySerializer


# ── API REST ──────────────────────────────────────────────────────────────────

class TravelerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Traveler.objects.all().order_by('name')
    serializer_class = TravelerSerializer

    @action(detail=True, methods=['post', 'patch'], url_path='roster')
    def update_roster(self, request, pk=None):
        traveler = self.get_object()
        entry, created = RosterEntry.objects.get_or_create(traveler=traveler)
        serializer = RosterEntrySerializer(entry, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _pct(n, d):
    return round((n / d) * 100) if d > 0 else 0


# ── VISTAS HTML ───────────────────────────────────────────────────────────────

def roster_view(request):
    """Página principal del roster."""
    travelers = Traveler.objects.prefetch_related('roster_entry').order_by('name')

    total        = travelers.count()
    reclutados   = RosterEntry.objects.filter(is_obtained=True).count()
    seis_estrellas = RosterEntry.objects.filter(is_obtained=True, is_6_stars=True).count()
    despertados  = RosterEntry.objects.filter(is_obtained=True, awakening_level__gt=0).count()

    # Conteos por job
    jobs_stats = []
    for job in Traveler.objects.values_list('job', flat=True).distinct().order_by('job'):
        total_job     = Traveler.objects.filter(job=job).count()
        reclutados_job = RosterEntry.objects.filter(traveler__job=job, is_obtained=True).count()
        jobs_stats.append({
            'job':        job,
            'total':      total_job,
            'reclutados': reclutados_job,
            'pct':        _pct(reclutados_job, total_job),
        })

    stats = {
        'reconocidos':        total,
        'reclutados':         reclutados,
        'seis_estrellas':     seis_estrellas,
        'despertados':        despertados,
        'pct_reclutados':     _pct(reclutados, total),
        'pct_seis_estrellas': _pct(seis_estrellas, reclutados) if reclutados > 0 else 0,
        'pct_despertados':    _pct(despertados, reclutados) if reclutados > 0 else 0,
        'jobs':               jobs_stats,
    }

    jobs      = Traveler.objects.values_list('job', flat=True).distinct().order_by('job')
    armas     = Traveler.objects.values_list('weapon_type', flat=True).distinct().order_by('weapon_type')
    elementos = Traveler.objects.values_list('element', flat=True).distinct().order_by('element')

    return render(request, 'api/roster.html', {
        'travelers': travelers,
        'stats':     stats,
        'jobs':      jobs,
        'armas':     armas,
        'elementos': elementos,
    })


def roster_search(request):
    """Búsqueda y filtros via HTMX, retorna solo la grilla."""
    travelers = Traveler.objects.prefetch_related('roster_entry').order_by('name')

    q               = request.GET.get('q', '').strip()
    job             = request.GET.get('job', '').strip()
    weapon          = request.GET.get('weapon', '').strip()
    elemento        = request.GET.get('element', '').strip()
    solo_reclutados = request.GET.get('solo_reclutados', '')

    if q:
        travelers = travelers.filter(name__icontains=q)
    if job:
        travelers = travelers.filter(job=job)
    if weapon:
        travelers = travelers.filter(weapon_type=weapon)
    if elemento:
        travelers = travelers.filter(element=elemento)
    if solo_reclutados:
        travelers = travelers.filter(roster_entry__is_obtained=True)

    return render(request, 'api/components/traveler_grid.html', {
        'travelers': travelers,
    })


def traveler_modal(request, pk):
    """Retorna el contenido del modal via HTMX."""
    traveler = get_object_or_404(Traveler, pk=pk)
    RosterEntry.objects.get_or_create(traveler=traveler)
    traveler.refresh_from_db()
    return render(request, 'api/components/traveler_modal.html', {
        'traveler': traveler,
    })


@require_http_methods(['POST'])
def traveler_update(request, pk):
    """Graba los cambios del modal y retorna el modal actualizado."""
    traveler = get_object_or_404(Traveler, pk=pk)
    entry, _ = RosterEntry.objects.get_or_create(traveler=traveler)

    entry.is_obtained            = request.POST.get('is_obtained') == 'true'
    entry.is_6_stars             = request.POST.get('is_6_stars') == 'true'
    entry.is_ultimate_awakened   = request.POST.get('is_ultimate_awakened') == 'true'
    entry.has_ultimate_overcharge = request.POST.get('has_ultimate_overcharge') == 'true'

    try:
        entry.current_level      = int(request.POST.get('current_level', 1))
        entry.awakening_level    = int(request.POST.get('awakening_level', 0))
        entry.ultimate_level     = int(request.POST.get('ultimate_level', 0))
        entry.weapon_souls_count = int(request.POST.get('weapon_souls_count', 0))
    except ValueError:
        pass

    entry.current_weapon = request.POST.get('current_weapon', '').strip() or None
    entry.current_armor  = request.POST.get('current_armor', '').strip() or None
    entry.save()

    traveler.refresh_from_db()
    context = {'traveler': traveler, 'saved': True}
    response = render(request, 'api/components/traveler_modal.html', context)
    response['HX-Trigger'] = 'closeModal'
    return response