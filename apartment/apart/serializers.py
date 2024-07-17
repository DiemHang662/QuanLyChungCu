from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer
from .models import Resident, Flat, Bill, Item, Feedback, Survey, FaMember, SurveyResult, Product, Cart, \
    CartProduct


class ResidentSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    avatar = serializers.ImageField(write_only=True, required=False)
    is_staff = serializers.BooleanField(required=False, default=False)
    is_superuser = serializers.BooleanField(required=False, default=False)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    def get_avatar_url(self, instance):
        if instance.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(instance.avatar.url)
            return instance.avatar.url
        return None

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['avatar_url'] = self.get_avatar_url(instance)
        return rep

    def create(self, validated_data):
        avatar = validated_data.pop('avatar', None)
        resident = Resident(**validated_data)
        resident.set_password(validated_data['password'])
        if avatar:
            resident.avatar = avatar
        resident.save()
        return resident

    class Meta:
        model = Resident
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'username', 'password', 'avatar', 'avatar_url',
                  'is_staff', 'is_superuser']
        extra_kwargs = {
            'password': {'write_only': True},
            'is_active': {'read_only': True}
        }
class ProductSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    image = serializers.ImageField(write_only=True, required=False)
    def get_image_url(self, instance):
        if instance.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(instance.image.url)
            return instance.image.url
        return None

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['image_url'] = self.get_image_url(instance)
        return rep
    class Meta:
        model = Product
        fields = '__all__'

class CartProductSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), write_only=True, source='product')

    class Meta:
        model = CartProduct
        fields = ['id', 'product', 'product_id', 'quantity']

class CartSerializer(serializers.ModelSerializer):
    items = CartProductSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'resident', 'items']


class FlatSerializer(ModelSerializer):
    class Meta:
        model = Flat
        fields = ["id", "number", "floor"]

class ItemSerializer(ModelSerializer):
    first_name = serializers.CharField(source='resident.first_name')
    last_name = serializers.CharField(source='resident.last_name')

    class Meta:
        model = Item
        fields = '__all__'

class BillSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='resident.first_name', read_only=True)
    last_name = serializers.CharField(source='resident.last_name', read_only=True)
    phone = serializers.CharField(source='resident.phone', read_only=True)
    resident_id = serializers.PrimaryKeyRelatedField(queryset=Resident.objects.all(), write_only=True, source='resident')
    image_url = serializers.SerializerMethodField()
    image = serializers.ImageField(write_only=True, required=False)
    avatar_url = serializers.SerializerMethodField()

    def get_image_url(self, instance):
        if instance.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(instance.image.url)
            return instance.image.url
        return None
    def get_avatar_url(self, instance):
        if instance.resident.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(instance.resident.avatar.url)
            return instance.resident.avatar.url
        return None

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['image_url'] = self.get_image_url(instance)
        rep['avatar_url'] = self.get_avatar_url(instance)
        return rep
    class Meta:
        model = Bill
        fields = '__all__'


class FaMemberSerializer(ModelSerializer):
    first_name = serializers.CharField(source='resident.first_name', read_only=True)
    last_name = serializers.CharField(source='resident.last_name', read_only=True)
    class Meta:
        model = FaMember
        fields = '__all__'

class FeedbackSerializer(ModelSerializer):
    first_name = serializers.CharField(source='resident.first_name')
    last_name = serializers.CharField(source='resident.last_name')

    class Meta:
        model = Feedback
        fields = '__all__'

class SurveySerializer(ModelSerializer):
    class Meta:
        model = Survey
        fields = '__all__'

class SurveyResultSerializer(ModelSerializer):
    class Meta:
        model = SurveyResult
        fields = '__all__'