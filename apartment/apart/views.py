from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.views import View
from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from . import perms
from .models import Flat, Item, Resident, Feedback, Survey, SurveyResult
from .serializers import ItemSerializer, SurveySerializer, SurveyResultSerializer
from .serializers import FlatSerializer
from .serializers import FeedbackSerializer
from .perms import OwnerAuthenticated

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
    permission_classes = [perms.OwnerAuthenticated]

    def list(self, request): # lấy danh sách các phản ánh hiện tại
        queryset = Feedback.objects.filter(resident=request.user)
        serializer = FeedbackSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):  #Tạo một phản ánh mới.
        serializer = FeedbackSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(resident=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['put'])
    def resolve(self, request, pk=None): # Tick tình trạng đã hoàn thành chưa
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

    def create(self, request, *args, **kwargs): #API để ban quản trị có thể tạo mới các phiếu khảo sát
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(creator=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#API để cư dân có thể thực hiện khảo sát và gửi kết quả về.
class SurveyResultViewSet(viewsets.ModelViewSet):
    queryset = SurveyResult.objects.all()
    serializer_class = SurveyResultSerializer

    def create(self, request, *args, **kwargs): # Điền vào khảo sát
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(resident=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)