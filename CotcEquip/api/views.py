from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Traveler, RosterEntry
from .serializers import TravelerSerializer, RosterEntrySerializer


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