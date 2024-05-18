from django.contrib import admin
from django.urls import path, re_path, include
from . import views
from .admin import admin_site
from rest_framework.routers import DefaultRouter
from .models import SurveyResult
from .views import StatisticalViewSet

router = DefaultRouter()
router.register('residents', views.ResidentViewSet, basename='resident')
router.register('flats', views.FlatViewSet,basename='flat')
router.register('items',views.ItemViewSet,basename='item')
router.register('feedback',views.FeedbackViewSet, basename='feedback')
router.register('survey', views.SurveyViewSet, basename='survey')
router.register('surveyresult', views.SurveyResultViewSet,basename='survey-result')
router.register('statistics', StatisticalViewSet, basename='statistics')

urlpatterns = [
    path('', include(router.urls)),
    path('admin/', admin_site.urls),
    path('api/statistics/<int:pk>/', StatisticalViewSet.as_view({'get': 'retrieve'}), name='statistics-api'),

]
