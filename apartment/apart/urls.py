from django.contrib import admin
from django.urls import path, re_path, include
from . import views
from .admin import admin_site
from rest_framework.routers import DefaultRouter

from .views import SurveyResultStatsViewSet

router = DefaultRouter()
router.register(r'residents', views.ResidentViewSet, basename='resident')
router.register('flats', views.FlatViewSet)
router.register('item',views.ItemViewSet)
router.register('feedback',views.FeedbackViewSet)
router.register('Survey', views.SurveyViewSet)
router.register('SurveyResult', views.SurveyResultViewSet)
router.register(r'survey-result-stats', SurveyResultStatsViewSet, basename='survey-result-stats')

urlpatterns = [
    path('', include(router.urls)),
    path('admin/', admin_site.urls),
]
