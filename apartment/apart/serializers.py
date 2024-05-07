from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer
from .models import Resident, Flat, Bill, Item, Feedback, Survey, FaMember, SurveyResult


class ResidentSerializer(ModelSerializer):
    class Meta:
        model= Resident
        fields ='__all__'

class AvatarSerializers(ModelSerializer):
    avatar = SerializerMethodField(source='avatar')

    def get_avatar(self, user):
        if user.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(user.avatar)
            return user.avatar.url
        return None


class ResidentSerializers(AvatarSerializers):

    class Meta:
        model = Resident
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True},
        }
class FlatSerializer(ModelSerializer):
    class Meta:
        model = Flat
        fields = ["id", "number", "floor"]

class ItemSerializer(ModelSerializer):
    class Meta:
        model = Item
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