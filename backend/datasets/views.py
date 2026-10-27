from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import Dataset
from .serializers import DatasetSerializer, DatasetUploadSerializer, SampleRecordSerializer


class DatasetViewSet(ReadOnlyModelViewSet):
    """
    GET /datasets/               list datasets, newest first
    GET /datasets/{id}/          retrieve one dataset
    POST /datasets/upload/       create a dataset from a CSV file
    """

    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer
    # Only numeric ids match the URL; anything else is a 404 from the router.
    lookup_value_regex = r'\d+'

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser])
    def upload(self, request):
        # Separate input and output serializers: the client sends name + file
        # and receives the created dataset.
        serializer = DatasetUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dataset = serializer.save()
        return Response(DatasetSerializer(dataset).data, status=status.HTTP_201_CREATED)


class RecordPagination(PageNumberPagination):
    """?page=2&page_size=50; an invalid page_size falls back to the default."""

    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


class StableOrderingFilter(OrderingFilter):
    """
    Always sorts by id last. Without a unique final key, rows with equal values
    (e.g. the same category) may come back in a different order on each query,
    so a row could appear on two pages or on none.
    """

    def get_ordering(self, request, queryset, view):
        ordering = list(super().get_ordering(request, queryset, view) or [])
        if not any(field.lstrip('-') == 'id' for field in ordering):
            ordering.append('id')
        return ordering


class DatasetRecordListView(ListAPIView):
    """
    GET /datasets/{id}/records/  list the records of one dataset, paginated

    ?search=   case-insensitive substring match on sample_id or category
    ?ordering= sample_id, category or value; prefix with "-" for descending.
               Defaults to CSV row order. Unknown fields are ignored.

    ListAPIView applies search, then ordering, to the whole queryset before
    paginating it.
    """

    serializer_class = SampleRecordSerializer
    pagination_class = RecordPagination
    filter_backends = [SearchFilter, StableOrderingFilter]
    search_fields = ['sample_id', 'category']
    ordering_fields = ['sample_id', 'category', 'value']

    def get_queryset(self):
        # 404 for an unknown dataset instead of an empty list.
        dataset = get_object_or_404(Dataset, pk=self.kwargs['pk'])
        return dataset.records.all()
