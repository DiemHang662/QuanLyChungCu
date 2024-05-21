from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer
from .models import Resident, Flat, Bill, Item, Feedback, Survey, FaMember, SurveyResult

class ResidentSerializer(ModelSerializer):

    def get_avatar_url(self, instance):
        if instance.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(instance.avatar.url)
            return instance.avatar.url
        return None  # Return None or a default URL if avatar is None

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['avatar'] = self.get_avatar_url(instance)
        return rep

    def create(self, validated_data):  # đăng kí
        resident = Resident(**validated_data)
        resident.set_password(validated_data['password'])
        resident.save()
        return resident
    class Meta:
        model = Resident
        fields = ['id', 'first_name', 'last_name', 'email', 'username', 'password', 'avatar']
        extra_kwargs = {
            'password': {
                'write_only': True
            },
            'is_active': {
                'read_only': True
            }
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