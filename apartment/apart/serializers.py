from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer
from .models import Resident, Flat, Bill, Item, Feedback, Survey, FaMember, SurveyResult

class ResidentSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    avatar = serializers.ImageField(write_only=True, required=False)
    is_staff = serializers.BooleanField(required=False, default=False)
    is_superuser = serializers.BooleanField(required=False, default=False)

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
        fields = ['id', 'first_name', 'last_name', 'email', 'username', 'password', 'avatar', 'avatar_url', 'is_staff', 'is_superuser']
        extra_kwargs = {
            'password': {'write_only': True},
            'is_active': {'read_only': True}
        }

class FlatSerializer(ModelSerializer):
    class Meta:
        model = Flat
        fields = ["id", "number", "floor"]

class ItemSerializer(ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'

class BillSerializer(ModelSerializer):
    class Meta:
        model = Bill
        fields = '__all__'

class FaMemberSerializer(ModelSerializer):
    class Meta:
        model = FaMember
        fields = '__all__'

class FeedbackSerializer(ModelSerializer):
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