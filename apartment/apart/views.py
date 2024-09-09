import hashlib
import hmac
import json
from datetime import time, date
import requests
from django.db.models import Max
from django.shortcuts import render, get_object_or_404
from django.http import Http404, JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import viewsets, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from . import paginators
from .models import Flat, Item, Resident, Feedback, Survey, SurveyResult, Bill, FaMember, Cart, Product, CartProduct, \
    Order, OrderProduct
from .serializers import ResidentSerializer, FlatSerializer, ItemSerializer, FeedbackSerializer, SurveySerializer, \
    SurveyResultSerializer, BillSerializer, FaMemberSerializer, CartSerializer, ProductSerializer, \
    CartProductSerializer, OrderSerializer


class ResidentViewSet(viewsets.ModelViewSet):
    queryset = Resident.objects.all()
    serializer_class = ResidentSerializer

    def get_permissions(self):
        if self.action in ['get_current_user', 'lock_account', 'check_account_status', 'change_password']:
            return [permissions.IsAuthenticated()]
        elif self.action == 'create_new_account':
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Resident.objects.all()
        elif user.is_staff:
            return Resident.objects.filter(id=user.id)
        return Resident.objects.none()

    @action(methods=['get', 'patch'], url_path='current-user', detail=False)
    def get_current_user(self, request):
        user = request.user
        if request.method == 'PATCH':
            for k, v in request.data.items():
                setattr(user, k, v)
            user.save()
        return Response(ResidentSerializer(user, context={'request': request}).data)

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
        if not request.user.is_superuser:
            return Response({'error': 'Bạn không có quyền thực hiện hành động này.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(methods=['post'], detail=False, url_path='change-password')
    def change_password(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not user.check_password(old_password):
            return Response({'error': 'Mật khẩu cũ không chính xác.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({'message': 'Đã thay đổi mật khẩu thành công.'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['patch'], url_path='change-avatar', parser_classes=[MultiPartParser, FormParser])
    def change_avatar(self, request):
        user = request.user
        if 'avatar' not in request.data:
            return Response({"error": "Avatar is required"}, status=status.HTTP_400_BAD_REQUEST)

        avatar = request.data['avatar']
        user.avatar = avatar
        user.save()

        return Response({"message": "Avatar updated successfully"}, status=status.HTTP_200_OK)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    pagination_class = paginators.Paginator

class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    pagination_class = paginators.Paginator
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(resident=self.request.user)

    @action(methods=['post'], detail=False, url_path='add-product')
    def add_product(self, request):
        user = request.user
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        try:
            product = get_object_or_404(Product, id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        cart, created = Cart.objects.get_or_create(resident=user)
        cart_product, cart_product_created = CartProduct.objects.get_or_create(cart=cart, product=product)

        if not cart_product_created:
            cart_product.quantity += quantity
        else:
            cart_product.quantity = quantity

        cart_product.save()
        cart.refresh_from_db()
        serialized_cart = CartSerializer(cart)

        return Response({'status': 'Product added to cart', 'cart': serialized_cart.data}, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path='cart-summary')
    def cart_summary(self, request):
        user = request.user
        try:
            cart = Cart.objects.get(resident=user)
        except Cart.DoesNotExist:
            return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)

        cart_products = CartProduct.objects.filter(cart=cart)
        serialized_cart_products = CartProductSerializer(cart_products, many=True)

        total_price = sum(item.product.price * item.quantity for item in cart_products)

        return Response({'cart_products': serialized_cart_products.data, 'total_price': total_price}, status=status.HTTP_200_OK)

    @action(methods=['delete'], detail=True, url_path='delete-product')
    def delete_product(self, request, pk=None):
        user = request.user

        try:
            cart_product = CartProduct.objects.get(cart__resident=user, id=pk)
            cart_product.delete()
            return Response({'status': 'Product removed from cart'}, status=status.HTTP_204_NO_CONTENT)
        except CartProduct.DoesNotExist:
            return Response({'error': 'Product not found in cart'}, status=status.HTTP_404_NOT_FOUND)

    @action(methods=['post'], detail=False, url_path='update-product-quantity')
    def update_product_quantity(self, request):
        user = request.user
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        try:
            product = get_object_or_404(Product, id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            cart = Cart.objects.get(resident=user)
            cart_product = CartProduct.objects.get(cart=cart, product=product)
        except (Cart.DoesNotExist, CartProduct.DoesNotExist):
            return Response({'error': 'Cart or CartProduct not found'}, status=status.HTTP_404_NOT_FOUND)

        if quantity <= 0:
            cart_product.delete()
        else:
            cart_product.quantity = quantity
            cart_product.save()

        total_price = sum(item.product.price * item.quantity for item in CartProduct.objects.filter(cart=cart))

        serialized_cart = CartSerializer(cart)

        return Response({
            'status': 'Product quantity updated',
            'cart': serialized_cart.data,
            'total_price': total_price
        }, status=status.HTTP_200_OK)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='create-order-from-cart')
    def create_order_from_cart(self, request):
        user = request.user
        try:
            cart = Cart.objects.get(resident=user)
        except Cart.DoesNotExist:
            return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)

        order = Order.objects.create(resident=user, total_amount=0)
        cart_products = CartProduct.objects.filter(cart=cart)
        total_amount = 0

        for item in cart_products:
            OrderProduct.objects.create(order=order, product=item.product, quantity=item.quantity,
                                        price=item.product.price)
            total_amount += item.product.price * item.quantity

        order.total_amount = total_amount
        order.save()
        serialized_order = OrderSerializer(order)

        # Clear the cart after creating the order
        cart_products.delete()

        return Response(serialized_order.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='confirm-order')
    def confirm_order(self, request, pk=None):
        user = request.user
        try:
            order = Order.objects.get(id=pk, resident=user, status='ĐANG CHỜ')
            order.status = 'ĐANG GIAO'
            order.save()
            serializer = self.get_serializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({'error': 'Order does not exist or you do not have permission to confirm it.'},
                            status=status.HTTP_404_NOT_FOUND)


class BillViewSet(viewsets.ModelViewSet):
    serializer_class = BillSerializer
    #pagination_class = paginators.Paginator
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        resident = self.request.user
        if resident.is_superuser:
            queryset = Bill.objects.all()
        else:
            queryset = Bill.objects.filter(resident=resident)

        payment_status = self.request.query_params.get('payment_status', None)
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status.upper())
        return queryset

    @action(methods=['post'], detail=False, url_path='create-bill')
    def create_bill(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response({"error": "Only superusers can create bills"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

# @csrf_exempt
# def create_bill_from_cart(request, cart_id):
#     if request.method == 'POST':
#         try:
#             cart = Cart.objects.get(id=cart_id)
#             resident = cart.resident
#             cart_products = cart.cartproduct_set.all()
#             total_amount = sum(item.product.price * item.quantity for item in cart_products)
#
#             # Create a new bill
#             bill = Bill.objects.create(
#                 resident=resident,
#                 amount=total_amount,
#                 issue_date=date.today(),
#                 due_date=date(2024, 8, 31),
#                 bill_type="HÓA ĐƠN MUA HÀNG",
#                 payment_status="UNPAID"
#             )
#
#             # Add products to the bill with pending status
#             for item in cart_products:
#                 BillProduct.objects.create(
#                     bill=bill,
#                     product=item.product,
#                     quantity=item.quantity,
#                     price=item.product.price,
#                 )
#
#             # Clear the cart
#             cart.cartproduct_set.all().delete()
#
#             return JsonResponse({'id': bill.id, 'amount': bill.amount}, status=200)
#
#         except Cart.DoesNotExist:
#             return JsonResponse({'error': 'Cart does not exist'}, status=404)
#     else:
#         return JsonResponse({'error': 'Method not allowed'}, status=405)


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = BillSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        resident = self.request.user
        queryset = Bill.objects. filter(resident=resident, payment_status='UNPAID')
        return queryset

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(payment_status='PAID')
        return Response(serializer.data)

@csrf_exempt
def payment_view(request: HttpRequest):
    partnerCode = "MOMO"
    accessKey = "F8BBA842ECF85"
    secretKey = "K951B6PE1waDMi640xX08PD3vg6EkVlz"
    requestId = f"{partnerCode}{int(time.time() * 1000)}"
    orderId = 'MM' + str(int(time.time() * 1000))
    orderInfo = "pay with MoMo"
    redirectUrl = "https://momo.vn/return"
    ipnUrl = "https://callback.url/notify"
    amount = request.headers.get('amount', '')
    requestType = "payWithATM"
    extraData = ""

    # Construct raw signature
    rawSignature = f"accessKey={accessKey}&amount={amount}&extraData={extraData}&ipnUrl={ipnUrl}&orderId={orderId}&orderInfo={orderInfo}&partnerCode={partnerCode}&redirectUrl={redirectUrl}&requestId={requestId}&requestType={requestType}"

    # Generate signature using HMAC-SHA256
    signature = hmac.new(secretKey.encode(), rawSignature.encode(), hashlib.sha256).hexdigest()

    # Create request body as JSON
    data = {
        "partnerCode": partnerCode,
        "accessKey": accessKey,
        "requestId": requestId,
        "amount": amount,
        "orderId": orderId,
        "orderInfo": orderInfo,
        "redirectUrl": redirectUrl,
        "ipnUrl": ipnUrl,
        "extraData": extraData,
        "requestType": requestType,
        "signature": signature,
        "lang": "vi"
    }

    # Send request to MoMo endpoint
    url = 'https://test-payment.momo.vn/v2/gateway/api/create'
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=data, headers=headers)

    # Process response
    if response.status_code == 200:
        response_data = response.json()
        pay_url = response_data.get('payUrl')
        return JsonResponse(response_data)
    else:
        return JsonResponse({"error": f"Failed to create payment request. Status code: {response.status_code}"},
                            status=500)

class FlatViewSet(viewsets.ModelViewSet):
    queryset = Flat.objects.all()
    serializer_class = FlatSerializer
    pagination_class = paginators.Paginator


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    pagination_class = paginators.Paginator
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            queryset = Item.objects.all()
        else:
            queryset = Item.objects.filter(resident=user)

        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())

        return queryset

    @action(methods=['post'], detail=False, url_path='create-item')
    def create_item(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response({"error": "Only superusers can create item"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['patch'])
    def mark_received(self, request, pk=None):
        user = request.user
        item = self.get_object()

        if not (user.is_superuser and user.is_staff):
            return Response({"detail": "Only superusers or staff members can mark items as received."},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance=item, data={'status': 'RECEIVED'}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class FaMemberViewSet(viewsets.ModelViewSet):
    queryset = FaMember.objects.all()
    serializer_class = FaMemberSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = paginators.Paginator
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return FaMember.objects.all()
        elif user.is_staff:
            return FaMember.objects.filter(id=user.id)
        return FaMember.objects.none()

class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = paginators.Paginator

    def get_queryset(self):
        resident = self.request.user
        queryset = Feedback.objects.all() if resident.is_superuser else Feedback.objects.filter(resident=resident)

        resolved_status = self.request.query_params.get('resolved', None)
        if resolved_status is not None:
            queryset = queryset.filter(resolved=(resolved_status.lower() == 'true'))

        return queryset

    def create(self, request):
        serializer = FeedbackSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(resident=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'])  # Change 'put' to 'patch'
    def mark_as_resolved(self, request, pk=None):
        if not request.user.is_superuser:
            return Response({"detail": "Only superusers can mark feedback as resolved."},
                            status=status.HTTP_403_FORBIDDEN)

        feedback = self.get_object()
        serializer = self.get_serializer(instance=feedback, data={'resolved': True}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def get_object(self):
        try:
            feedback = super().get_object()
            if self.request.user.is_superuser or feedback.resident == self.request.user:
                return feedback
            raise Http404("Feedback not found or you don't have permission to access it.")
        except Feedback.DoesNotExist:
            raise Http404("Feedback not found.")


class SurveyViewSet(viewsets.ModelViewSet):
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = paginators.Paginator

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

    @action(methods=['post'], detail=False, url_path='create-survey')
    def create_survey(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response({"error": "Only superusers can create survey"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class SurveyResultViewSet(viewsets.ModelViewSet):
    queryset = SurveyResult.objects.all()
    serializer_class = SurveyResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # User chỉ xem được của mình
        return SurveyResult.objects.filter(resident=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(resident=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        survey_result = self.get_object()
        serializer = self.get_serializer(survey_result)
        return Response(serializer.data)

    def update(self, request, pk=None):
        survey_result = self.get_object()
        if survey_result.resident != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(survey_result, data=request.data)
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
    permission_classes = [IsAuthenticated]

    def list(self, request):
        return Response({"message": "Please provide a survey_id to get cleanliness statistics."}, status=400)

    def retrieve(self, request, pk=None):
        try:
            queryset = SurveyResult.objects.filter(survey_id=pk)
            if not queryset.exists():
                return Response({"message": "Survey with the specified ID does not exist."}, status=404)

            stats = queryset.aggregate(
                maximum_cleanliness=Max('cleanliness_rating'),
                maximum_facilities=Max('facilities_rating'),
                maximum_services=Max('services_rating')
            )

            return Response({
                'maximum_cleanliness': stats['maximum_cleanliness'],
                'maximum_facilities': stats['maximum_facilities'],
                'maximum_services': stats['maximum_services']
            })
        except Exception as e:
            return Response({"message": str(e)}, status=500)