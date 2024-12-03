from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from recipes.models import Recipe
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Subscription
from .pagination import CustomLimitOffsetPagination
from .serializers import (AvatarSerializer, CustomUserCreateSerializer,
                          CustomUserSerializer, PasswordChangeSerializer,
                          TokenSerializer)

User = get_user_model()


class UserVerificationViewSet(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    """Custom viewset for working with tokens: login and logout."""
    serializer_class = TokenSerializer
    permission_classes = [AllowAny]

    @action(
        detail=False, methods=['post'],
        url_path='login',
        permission_classes=[AllowAny]
    )
    def login(self, request):
        """Method for obtaining a token (login)"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

    @action(
        detail=False, methods=['post'],
        url_path='logout',
        permission_classes=[IsAuthenticated]
    )
    def logout(self, request):
        """Method for logout"""
        return Response(status=status.HTTP_204_NO_CONTENT)


class UsersViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    """ViewSet for managing users."""

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomLimitOffsetPagination

    def get_permissions(self):
        if self.action == 'create':  # User registration
            self.permission_classes = [AllowAny]
        elif self.action in ['list', 'retrieve']:  # Viewing users
            self.permission_classes = [AllowAny]
        else:  # Actions requiring authorization
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        elif self.action == 'avatar':
            return AvatarSerializer
        return CustomUserSerializer

    @action(
        detail=False,
        methods=['get', 'patch'],
        url_path='me',
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        """Get and update information about the current user."""
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        elif request.method == 'PATCH':
            serializer = self.get_serializer(
                request.user,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated]
    )
    def avatar(self, request):
        """Upload or delete user's avatar."""
        user = request.user

        if request.method == 'PUT':
            if 'avatar' not in request.data:
                raise ValidationError({"avatar": "This field is required."})
            avatar_serializer = AvatarSerializer(user, data=request.data)
            avatar_serializer.is_valid(raise_exception=True)
            avatar_serializer.save()
            return Response(
                {"avatar": avatar_serializer.data["avatar"]},
                status=status.HTTP_200_OK
            )

        if request.method == 'DELETE' and user.avatar:
            user.avatar.delete(save=False)
            user.avatar = None
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=['post'],
        url_path='set_password',
        permission_classes=[IsAuthenticated]
    )
    def set_password(self, request):
        """Password reset."""
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Get the list of current user's subscriptions"""
        subscriptions = (
            Subscription.objects.filter(user=request.user)
        ).select_related('author')
        paginator = CustomLimitOffsetPagination()
        paginated_subscriptions = (
            paginator.paginate_queryset(subscriptions, request)
        )

        recipes_limit = request.query_params.get('recipes_limit')
        try:
            recipes_limit = int(recipes_limit) if recipes_limit else None
        except ValueError:
            return Response(
                {"detail": "recipes_limit must be a number"},
                status=status.HTTP_400_BAD_REQUEST
            )

        results = []
        for subscription in paginated_subscriptions:
            author = subscription.author
            recipes_queryset = Recipe.objects.filter(author=author)
            if recipes_limit:
                recipes_queryset = recipes_queryset[:recipes_limit]

            recipes_data = [
                {
                    "id": recipe.id,
                    "name": recipe.name,
                    "image": (
                        request.build_absolute_uri(recipe.image.url)
                        if recipe.image else None
                    ),
                    "cooking_time": recipe.cooking_time,
                }
                for recipe in recipes_queryset
            ]

            results.append({
                "id": author.id,
                "username": author.username,
                "first_name": author.first_name,
                "last_name": author.last_name,
                "email": author.email,
                "is_subscribed": True,
                "avatar": (
                    request.build_absolute_uri(author.avatar.url)
                    if author.avatar else None
                ),
                "recipes_count": Recipe.objects.filter(author=author).count(),
                "recipes": recipes_data,
            })

        return paginator.get_paginated_response(results)

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe',
            permission_classes=[IsAuthenticated])
    def manage_subscription(self, request, pk=None):
        """Manage subscription to a user.

        POST - subscribe.
        DELETE - unsubscribe.
        """
        author = get_object_or_404(User, pk=pk)

        if request.user == author:
            return Response({"detail": "You cannot subscribe to yourself"},
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'POST':
            # Subscribe to the user
            if Subscription.objects.filter(
                    user=request.user,
                    author=author
            ).exists():
                return Response(
                    {"detail": "You are already subscribed to this user"},
                    status=status.HTTP_400_BAD_REQUEST)

            Subscription.objects.create(user=request.user, author=author)
            recipes = Recipe.objects.filter(author=author)[:3]
            recipes_data = [
                {
                    "id": recipe.id,
                    "name": recipe.name,
                    "image": request.build_absolute_uri(
                        recipe.image.url) if recipe.image else None,
                    "cooking_time": recipe.cooking_time,
                }
                for recipe in recipes
            ]

            response_data = {
                "id": author.id,
                "username": author.username,
                "first_name": author.first_name,
                "last_name": author.last_name,
                "email": author.email,
                "is_subscribed": True,
                "avatar": request.build_absolute_uri(
                    author.avatar.url) if author.avatar else None,
                "recipes_count": Recipe.objects.filter(author=author).count(),
                "recipes": recipes_data,
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            # Unsubscribe from the user
            subscription = Subscription.objects.filter(
                user=request.user,
                author=author
            )
            if not subscription.exists():
                return Response(
                    {"detail": "You are not subscribed to this user"},
                    status=status.HTTP_400_BAD_REQUEST)

            subscription.delete()
            return Response({"detail": "You have successfully unsubscribed"},
                            status=status.HTTP_204_NO_CONTENT)
