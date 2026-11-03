from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import DatasetRecordListView, DatasetViewSet

router = SimpleRouter()
# basename is needed because the viewset has get_queryset() instead of a queryset.
router.register('datasets', DatasetViewSet, basename='dataset')

urlpatterns = [
    # Same name the former `records` action had, so reverse() calls still work.
    path(
        'datasets/<int:pk>/records/',
        DatasetRecordListView.as_view(),
        name='dataset-records',
    ),
    *router.urls,
]
