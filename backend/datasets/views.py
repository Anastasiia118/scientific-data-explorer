from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Dataset
from .serializers import DatasetSerializer, SampleRecordSerializer


class DatasetViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /datasets/               list datasets, newest first
    GET /datasets/{id}/          retrieve one dataset
    GET /datasets/{id}/records/  list the records of one dataset
    """

    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer
    # Only numeric ids match the URL; anything else is a 404 from the router.
    lookup_value_regex = r'\d+'

    @action(detail=True)
    def records(self, request, pk=None):
        # get_object() returns 404 for an unknown dataset instead of an empty list.
        dataset = self.get_object()
        serializer = SampleRecordSerializer(dataset.records.all(), many=True)
        return Response(serializer.data)
