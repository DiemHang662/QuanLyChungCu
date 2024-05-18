from django.contrib import admin
from django.db.models import Count
from django.template.response import TemplateResponse
from django.utils.html import mark_safe
from .models import Resident, Flat, Bill, Item, Feedback, Survey, SurveyResult
from django import forms
from django.urls import path, reverse


class MyApartAdminSite(admin.AdminSite):
    site_header ="APARTMENT MANAGEMENT SYSTEM"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('statistics/', self.admin_view(self.statistics_view), name='statistics')
        ]
        return custom_urls + urls

    def statistics_view(self, request):
        context = dict(
            self.each_context(request),
        )
        return TemplateResponse(request, "admin/statistics.html", context)

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['stats_link'] = reverse('statistics-list')
        return super().index(request, extra_context=extra_context)

admin_site = MyApartAdminSite(name='myAdmin')


admin_site.register(Flat)
admin_site.register(Resident)
admin_site.register(Bill)
admin_site.register(Item)
admin_site.register(Feedback)
admin_site.register(Survey)
admin_site.register(SurveyResult)