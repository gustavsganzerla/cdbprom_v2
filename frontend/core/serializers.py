from rest_framework import serializers
from .models import PromoterModel
import re

class PromoterModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoterModel
        fields = '__all__'


