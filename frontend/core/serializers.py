from rest_framework import serializers
from .models import PromoterModel

class PromoterModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoterModel
        fields = '__all__'
