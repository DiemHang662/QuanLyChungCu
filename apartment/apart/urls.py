from django.contrib import admin
from django.urls import path, re_path, include
from . import views
from .admin import admin_site
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('flats', views.FlatViewSet)
router.register('item',views.ItemViewSet)
router.register('Feedback', views.FeedbackViewSet)
router.register('Survey', views.SurveyViewSet)
router.register('SurveyResult', views.SurveyResultViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('admin/', admin_site.urls),
]
