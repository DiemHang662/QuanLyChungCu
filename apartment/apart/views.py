import json

from django.conf import settings
from django.db.models import Max
from django.shortcuts import render
from django.http import Http404
from rest_framework import viewsets, permissions, status, generics
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from . import serializers
from .models import Flat, Item, Resident, Feedback, Survey, SurveyResult, Bill, FaMember
from .perms import IsOwnerOrReadOnly
from .serializers import ResidentSerializer, FlatSerializer, ItemSerializer, FeedbackSerializer, SurveySerializer, \
    SurveyResultSerializer, BillSerializer, FaMemberSerializer


class ResidentViewSet(viewsets.ModelViewSet):
    queryset = Resident.objects.all()
    serializer_class = ResidentSerializer

    def get_permissions(self):
        if self.action in ['get_current_user', 'lock_account', 'check_account_status', 'create_new_account']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Resident.objects.filter(id=user.id)
        return Resident.objects.all()

    @action(methods=['get', 'patch'], url_path='current-user', detail=False)
    def get_current_user(self, request):
        user = request.user
        if request.method == 'PATCH':
            for k, v in request.data.items():
                setattr(user, k, v)
            user.save()
        return Response(ResidentSerializer(user).data)

    @action(methods=['post'], detail=True, url_path='lock-account')
    def lock_account(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({'status': 'account locked'}, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True, url_path='check-account-status')
    def check_account_status(self, request, pk=None):
        user = self.get_object()
        return Response({'is_active': user.is_active}, status=status.HTTP_200_OK)

    @action(methods=['post'], url_path='create-new-account', detail=False)
    def create_new_account(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class FlatViewSet(viewsets.ModelViewSet):
    queryset = Flat.objects.all()
    serializer_class = FlatSerializer

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self): # Chỉ xem được đồ của mình
        return Item.objects.filter(resident=self.request.user)
    @action(detail=False, methods=['get'], url_path='my-items')
    def my_items(self, request):
        # Lấy danh sách các món hàng của cư dân hiện đang ở trạng thái "Chờ nhận"
        items = self.queryset.filter(resident=request.user, status='PENDING')
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='mark-received')
    def mark_received(self, request, pk=None):
        item = self.get_object()
        if item.resident == request.user:  # Kiểm tra xem mục này thuộc về cư dân đang đăng nhập hay không
            item.status = 'RECEIVED'
            item.save()
        return Response({'status': 'Item is received by resident'}, status=status.HTTP_200_OK)


class BillViewSet(viewsets.ModelViewSet):
    serializer_class = BillSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        resident = self.request.user
        if resident.is_superuser:
            return Bill.objects.all()  # If the user is a superuser, return all bills
        return Bill.objects.filter(resident=self.request.user, payment_status='PAID')

class FaMemberViewSet(viewsets.ModelViewSet):
    queryset = FaMember.objects.all()
    serializer_class = FaMemberSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self): # Chỉ xem được của mình
        return FaMember.objects.filter(resident=self.request.user)

class VNPayCheckoutAPI(APIView):
    def post(self, request, *args, **kwargs):
        amount = request.data.get('amount')
        order_info = request.data.get('order_info')
        payment_data = vnpay.create_payment_data(amount=amount, order_info=order_info)
        return Response(payment_data)

class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]

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
    permission_classes = [permissions.IsAuthenticated]

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
    permission_classes = [permissions.IsAuthenticated]

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
        if survey_result.resident != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        survey_result.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class StatisticalViewSet(viewsets.ViewSet):
    def list(self, request):
        return render(request, 'admin/statistical.html', {"message": "Please provide a survey_id to get cleanliness statistics."}, status=400)

    def retrieve(self, request, pk=None):
        try:
            queryset = SurveyResult.objects.filter(survey_id=pk)
            if not queryset.exists():
                return render(request, 'admin/statistical.html', {"message": "Survey with the specified ID does not exist."}, status=404)

            stats = queryset.aggregate(
                maximum_cleanliness=Max('cleanliness_rating'),
                maximum_facilities= Max('facilities_rating'),
                maximum_services = Max('services_rating')
            )

            stats_json = json.dumps({
                'maximum_cleanliness': stats['maximum_cleanliness'],
                'maximum_facilities': stats['maximum_facilities'],
                'maximum_services': stats['maximum_services']
            })

            return render(request, 'admin/statistical.html', {'stats_json': stats_json})
        except Exception as e:
            return render(request, 'admin/statistical.html', {"message": str(e)}, status=500)