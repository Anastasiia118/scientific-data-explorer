from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import DatasetRecordListView, DatasetViewSet

router = SimpleRouter()
router.register('datasets', DatasetViewSet)

urlpatterns = [
    # Same name the former `records` action had, so reverse() calls still work.
    path(
        'datasets/<int:pk>/records/',
        DatasetRecordListView.as_view(),
        name='dataset-records',
    ),
    *router.urls,
]
