import json

from django.contrib.sites import requests
from django.db.models import Max
from django.shortcuts import render
from django.http import HttpResponse, Http404, JsonResponse
from django.views import View
from rest_framework import viewsets, permissions, status, generics
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView

from . import perms
from .models import Flat, Item, Resident, Feedback, Survey, SurveyResult
from .perms import IsOwnerOrReadOnly
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

class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [IsOwnerOrReadOnly, IsAdminUser]

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

    @action(detail=True, methods=['put'], permission_classes=[IsAdminUser])
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
class SurveyResultViewSet(viewsets.ViewSet):
    queryset = SurveyResult.objects.all()
    serializer_class = SurveyResultSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self): # User chỉ xem được của mình
        return SurveyResult.objects.filter(resident=self.request.user)

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
        # Ensure that only the owner can update their own survey result
        if survey_result.resident != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = self.serializer_class(survey_result, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        survey_result = self.get_object()
        # Ensure that only the owner can delete their own survey result
        if survey_result.resident != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        survey_result.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class StatisticalViewSet(viewsets.ViewSet):
    def list(self, request):
        return render(request, 'statistical.html', {"message": "Please provide a survey_id to get cleanliness statistics."}, status=400)

    def retrieve(self, request, pk=None):
        try:
            queryset = SurveyResult.objects.filter(survey_id=pk)
            if not queryset.exists():
                return render(request, 'statistical.html', {"message": "Survey with the specified ID does not exist."}, status=404)

            stats = queryset.aggregate(
                maximum_cleanliness=Max('cleanliness_rating'),
                maximum_facilities= Max('facilities_rating'),
                maximum_services = Max('services_rating')
            )

            # Serialize stats to JSON string
            stats_json = json.dumps({
                'maximum_cleanliness': stats['maximum_cleanliness'],
                'maximum_facilities': stats['maximum_facilities'],
                'maximum_services': stats['maximum_services']
            })

            return render(request, 'statistical.html', {'stats_json': stats_json})
        except Exception as e:
            return render(request, 'statistical.html', {"message": str(e)}, status=500)