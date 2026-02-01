from rest_framework import serializers
from django.contrib.auth.models import User
from .models import ShortURL

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "password"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class ShortURLSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShortURL
        fields = "__all__"
        read_only_fields = ["user", "short_key", "clicks"]

