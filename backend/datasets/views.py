from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Dataset
from .serializers import DatasetSerializer, SampleRecordSerializer


class DatasetViewSet(ReadOnlyModelViewSet):
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
        records = dataset.records.all()
        page = self.paginate_queryset(records)

        if page is not None:
            serializer = SampleRecordSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
 
        serializer = SampleRecordSerializer(records, many=True)


        return Response(serializer.data)
