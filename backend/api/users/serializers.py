from api.utils import Base64ImageField
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from djoser.serializers import UserCreateSerializer
from djoser.serializers import UserSerializer as DjoserUserSerializer
from recipes.models import Recipe
from rest_framework import serializers
from rest_framework.serializers import CharField
from rest_framework_simplejwt.tokens import AccessToken
from users.models import Subscription

User = get_user_model()


class AvatarSerializer(serializers.ModelSerializer):
    """Serializer for managing user avatar."""

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


class RecipeShortSerializer(serializers.ModelSerializer):
    """Serializer for short representation of recipes."""

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class SubscriptionDetailSerializer(serializers.ModelSerializer):
    """Serializer for subscriptions with detailed author info and recipes."""

    id = serializers.IntegerField(source='author.id')
    username = serializers.CharField(source='author.username')
    first_name = serializers.CharField(source='author.first_name')
    last_name = serializers.CharField(source='author.last_name')
    email = serializers.EmailField(source='author.email')
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email',
            'is_subscribed', 'avatar', 'recipes', 'recipes_count'
        ]

    def get_is_subscribed(self, obj):
        return True

    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.author.avatar:
            return request.build_absolute_uri(obj.author.avatar.url)
        return None

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = self.context.get('recipes_limit')

        if recipes_limit and isinstance(recipes_limit, int):
            recipes = obj.author.recipes.all()[:recipes_limit]
        else:
            recipes = obj.author.recipes.all()

        return RecipeShortSerializer(
            recipes,
            many=True,
            context={'request': request}).data

    def get_recipes_count(self, obj):
        return obj.author.recipes.count()


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
