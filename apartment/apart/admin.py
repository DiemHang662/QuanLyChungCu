from django.contrib import admin
from django.db.models import Count, Max
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.utils.html import mark_safe
from .models import Resident, Flat, Bill, Item, Feedback, Survey, SurveyResult
from django import forms
from django.urls import path, reverse


class MyApartAdminSite(admin.AdminSite):
    site_header = "APARTMENT MANAGEMENT SYSTEM"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('statistics/', self.admin_view(self.stats_view), name='statistics'),
        ]
        return custom_urls + urls

    def stats_view(self, request):
        try:
            # Query for statistics here
            queryset = SurveyResult.objects.all()
            stats = queryset.aggregate(
                maximum_cleanliness=Max('cleanliness_rating'),
                maximum_facilities=Max('facilities_rating'),
                maximum_services=Max('services_rating')
            )
            # Render the template with statistics
            return render(request, 'admin/statistical.html', {'stats': stats})
        except Exception as e:
            return render(request, 'admin/statistical.html', {"message": str(e)})

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['stats_link'] = reverse('admin:statistics', current_app=admin_site.name)

        return super().index(request, extra_context=extra_context)

admin_site = MyApartAdminSite(name='myAdmin')



admin_site.register(Flat)
admin_site.register(Resident)
admin_site.register(Bill)
admin_site.register(Item)
admin_site.register(Feedback)
admin_site.register(Survey)
admin_site.register(SurveyResult)