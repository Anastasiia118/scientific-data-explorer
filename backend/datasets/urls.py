from rest_framework.routers import SimpleRouter

from .views import DatasetViewSet

router = SimpleRouter()
router.register('datasets', DatasetViewSet)

urlpatterns = router.urls
