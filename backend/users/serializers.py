import base64
import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers
from rest_framework.serializers import CharField
from rest_framework_simplejwt.tokens import AccessToken

from .models import Subscription

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Field for decoding an image from Base64 and saving it as a file."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr), name=f'{uuid.uuid4()}.{ext}'
            )
        return super().to_internal_value(data)


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ['avatar']


class CustomUserCreateSerializer(UserCreateSerializer):
    """Serializer for user registration."""

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'id', 'email', 'username',
            'first_name', 'last_name', 'password'
        )

    def validate(self, data):
        required_fields = [
            'email', 'username', 'first_name',
            'last_name', 'password'
        ]
        missing_fields = [
            field for field in required_fields if not data.get(field)
        ]
        if missing_fields:
            raise serializers.ValidationError(
                {field: f"{field} is required." for field in missing_fields})
        return data


class CustomUserSerializer(DjoserUserSerializer):
    """Serializer for the current user's profile."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = (
            'id', 'email', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return user.is_authenticated and (
            obj.followers.filter(user=user)
        ).exists()


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for subscriptions."""
    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Subscription
        fields = ['id', 'user', 'author']
        read_only_fields = ['user']


class TokenSerializer(serializers.Serializer):
    """Serializer for obtaining a token using email and password."""
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)
    token = serializers.CharField(read_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        try:
            user = User.objects.get(email=email)
            if not check_password(password, user.password):
                raise serializers.ValidationError("Invalid email or password")
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password")

        token = AccessToken.for_user(user)
        return {"auth_token": str(token)}


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for changing the user's password."""
    current_password = CharField(write_only=True, required=True)
    new_password = CharField(write_only=True, required=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(
                'Password must be at least 8 characters long.'
            )
        return value
