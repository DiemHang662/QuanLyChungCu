from django.db.models import Avg, Count
from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.views import View
from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from . import perms
from .models import Flat, Item, Resident, Feedback, Survey, SurveyResult
from .serializers import ResidentSerializer, FlatSerializer, ItemSerializer, FeedbackSerializer, SurveySerializer, SurveyResultSerializer

class ResidentViewSet(viewsets.ModelViewSet):
    queryset = Resident.objects.all()
    serializer_class = ResidentSerializer

    def get_permissions(self):
        if self.action == 'create_post':
            return [permissions.IsAuthenticated()]  # Example custom permission
        elif self.action == 'current_user':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    @action(methods=['GET'], detail=False, url_path='current_user', url_name='current_user')
    def current_user(self, request):
        serializer = self.get_serializer(request.user)  # Use get_serializer method
        return Response(serializer.data, status=status.HTTP_200_OK)

class FlatViewSet(viewsets.ModelViewSet):
    queryset = Flat.objects.all()
    serializer_class = FlatSerializer

def resident_items(request, resident_id):
    try:
        resident = Resident.objects.get(pk=resident_id)
    except Resident.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    items = resident.items.filter(status='PENDING')  # Lấy danh sách các mặt hàng chờ nhận
    serializer = ItemSerializer(items, many=True)
    return Response(serializer.data)


def update_item_status(request, item_id):
    try:
        item = Item.objects.get(pk=item_id)
    except Item.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    item.status = 'RECEIVED'  # Cập nhật trạng thái thành đã nhận
    item.save()
    return Response(status=status.HTTP_200_OK)

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer

class FeedbackViewSet(viewsets.ViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.IsAdminUser]

    def list(self, request):
        queryset = Feedback.objects.filter(resident=request.user)
        serializer = FeedbackSerializer(queryset, many=True)
        return Response(serializer.data)


    def create(self, request):
        serializer = FeedbackSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(resident=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['put'])
    def resolve(self, request, pk=None):
        feedback = self.get_object(pk)
        feedback.resolved = True
        feedback.save()
        serializer = FeedbackSerializer(feedback)
        return Response(serializer.data)

    def get_object(self, pk):
        try:
            return Feedback.objects.get(pk=pk, resident=self.request.user)
        except Feedback.DoesNotExist:
            raise Http404


class SurveyViewSet(viewsets.ModelViewSet):
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

def retrieve(self, request, pk=None):
    survey = self.get_object()
    serializer = self.serializer_class(survey)
    return Response(serializer.data)

#API để cư dân có thể thực hiện khảo sát và gửi kết quả về.
class SurveyResultViewSet(viewsets.ModelViewSet):
    queryset = SurveyResult.objects.all()
    serializer_class = SurveyResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(resident=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        survey_result = self.get_object()
        serializer = self.serializer_class(survey_result)
        return Response(serializer.data)

    def update(self, request, pk=None):
        survey_result = self.get_object()
        serializer = self.serializer_class(survey_result, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        survey_result = self.get_object()
        survey_result.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class SurveyResultStatsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAdminUser]

    def list(self, request):
        survey_results = SurveyResult.objects.all()
        cleanliness_counts = survey_results.values('cleanliness_rating').annotate(count=Count('cleanliness_rating'))

        cleanliness_stats = {}
        for item in cleanliness_counts:
            cleanliness_rating = item['cleanliness_rating']
            count = item['count']
            cleanliness_stats[cleanliness_rating] = count

        return Response(cleanliness_stats)


