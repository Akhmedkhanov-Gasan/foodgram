from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from api.pagination import PageToLimitOffsetPagination
from api.users.serializers import (AvatarSerializer,
                                   CustomUserCreateSerializer,
                                   CustomUserSerializer,
                                   PasswordChangeSerializer,
                                   SubscriptionDetailSerializer,
                                   TokenSerializer)
from recipes.models import Recipe
from users.models import Subscription

User = get_user_model()


class UserVerificationViewSet(GenericViewSet, CreateModelMixin):
    """Custom viewset for working with tokens: login and logout."""

    serializer_class = TokenSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=200)

    @action(detail=False, methods=['post'], url_path='logout')
    def logout(self, request):
        return Response(status=204)


class UsersViewSet(ModelViewSet):
    """ViewSet for managing users."""

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = PageToLimitOffsetPagination

    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

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
                return Response({"avatar": "This field is required."},
                                status=400)
            serializer = AvatarSerializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"avatar": serializer.data['avatar']}, status=200)

        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete()
            return Response(status=204)

    @action(
        detail=False, methods=['post'],
        url_path='set_password',
        permission_classes=[IsAuthenticated]
    )
    def set_password(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response(status=204)

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Retrieve the list of subscriptions with detailed information."""

        subscriptions = Subscription.objects.filter(
            user=request.user).select_related('author')
        paginated_subscriptions = self.paginate_queryset(subscriptions)

        recipes_limit = request.query_params.get('recipes_limit')
        recipes_limit = (
            int(recipes_limit)
            if recipes_limit and recipes_limit.isdigit()
            else None
        )

        serializer = SubscriptionDetailSerializer(
            paginated_subscriptions,
            many=True,
            context={'request': request, 'recipes_limit': recipes_limit}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='subscribe',
        permission_classes=[IsAuthenticated]
    )
    def manage_subscription(self, request, pk=None):
        """Manage subscription to a user."""

        author = get_object_or_404(User, pk=pk)

        if request.user == author:
            return Response({"detail": "You cannot subscribe to yourself"},
                            status=400)

        if request.method == 'POST':
            if Subscription.objects.filter(user=request.user,
                                           author=author).exists():
                return Response(
                    {"detail": "You are already subscribed to this user"},
                    status=400
                )

            Subscription.objects.create(user=request.user, author=author)

            recipes_limit = request.query_params.get('recipes_limit', None)
            try:
                recipes_limit = int(recipes_limit) if recipes_limit else None
            except ValueError:
                return Response(
                    {"detail": "recipes_limit must be a number"},
                    status=400
                )

            recipes = Recipe.objects.filter(author=author)
            if recipes_limit:
                recipes = recipes[:recipes_limit]

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
            return Response(response_data, status=201)

        if request.method == 'DELETE':
            subscription = Subscription.objects.filter(user=request.user,
                                                       author=author)
            if not subscription.exists():
                return Response(
                    {"detail": "You are not subscribed to this user"},
                    status=400
                )

            subscription.delete()
            return Response({"detail": "You have successfully unsubscribed"},
                            status=204)
