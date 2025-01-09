from django.contrib.auth import get_user_model

from djoser.serializers import UserCreateSerializer
from djoser.serializers import UserSerializer as DjoserUserSerializer

from rest_framework import serializers

from api.utils import Base64ImageField
from recipes.models import Recipe
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
        return user.is_authenticated and Subscription.objects.filter(
            user=user, author=obj
        ).exists()


class CustomPasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        """Validate that the current password is correct."""

        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Wrong password.')
        return value

    def validate_new_password(self, value):
        """Optional: Add custom validation for new password."""

        if len(value) < 8:
            raise serializers.ValidationError(
                'Password must be at least 8 characters long.'
            )
        return value

    def save(self, **kwargs):
        """Set the new password for the user."""

        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


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
    recipes_count = serializers.IntegerField()

    class Meta:
        model = Subscription
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email',
            'is_subscribed', 'avatar', 'recipes', 'recipes_count'
        ]

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return user.is_authenticated and Subscription.objects.filter(
            user=user, author=obj.author
        ).exists()

    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.author.avatar:
            return request.build_absolute_uri(obj.author.avatar.url)
        return None

    def get_recipes(self, obj):
        """Retrieve author's recipes with an optional limit."""
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit', 10)

        if isinstance(recipes_limit, str) and recipes_limit.isdigit():
            recipes_limit = int(recipes_limit)
        else:
            recipes_limit = None

        recipes_query = obj.author.recipes.all()
        if recipes_limit is not None:
            recipes_query = recipes_query[:recipes_limit]

        return RecipeShortSerializer(
            recipes_query,
            many=True,
            context={'request': request}
        ).data


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for subscriptions."""

    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Subscription
        fields = ['id', 'user', 'author']
        read_only_fields = ['user']

    def validate_author(self, value):
        """Validate the author field for subscription constraints."""

        user = self.context['request'].user
        if user == value:
            raise serializers.ValidationError(
                'You cannot subscribe to yourself.'
            )
        if Subscription.objects.filter(user=user, author=value).exists():
            raise serializers.ValidationError(
                'You are already subscribed to this user.'
            )
        return value

    def create(self, validated_data):
        """Set the user field to the currently authenticated user."""

        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
