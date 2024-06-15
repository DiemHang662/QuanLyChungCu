from django.contrib import admin
from django.urls import path, include
from . import views
from .admin import admin_site
from rest_framework.routers import DefaultRouter
from .views import StatisticalViewSet

router = DefaultRouter()
router.register('residents', views.ResidentViewSet, basename='resident')
router.register('flats', views.FlatViewSet, basename='flat')
router.register('items', views.ItemViewSet, basename='item')
router.register('famembers', views.FaMemberViewSet, basename='famember')
router.register('bills', views.BillViewSet, basename='bill')
router.register('payment', views.PaymentViewSet, basename='payment')
router.register('feedback', views.FeedbackViewSet, basename='feedback')
router.register('survey', views.SurveyViewSet, basename='survey')
router.register('surveyresult', views.SurveyResultViewSet, basename='surveyresult')
router.register('statistics', StatisticalViewSet, basename='statistic')

urlpatterns = [
    path('', include(router.urls)),
    path('admin/', admin_site.urls),
    path('api/', include(router.urls)),
    path('api/statistics/<int:pk>/', StatisticalViewSet.as_view({'get': 'retrieve'}), name='statistics-api'),
]
