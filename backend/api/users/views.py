from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.shortcuts import get_object_or_404

from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.pagination import PageToLimitOffsetPagination
from api.users.serializers import (
    AvatarSerializer,
    CustomPasswordChangeSerializer,
    CustomUserCreateSerializer,
    CustomUserSerializer,
    SubscriptionDetailSerializer,
    SubscriptionSerializer,
)
from users.models import Subscription


User = get_user_model()


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
        """Retrieve or update current user's profile."""

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
        methods=['post'],
        url_path='set_password',
        permission_classes=[IsAuthenticated]
    )
    def set_password(self, request):
        """Allow password change using POST method."""

        serializer = CustomPasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=HTTPStatus.NO_CONTENT)

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
                return Response({'avatar': 'This field is required.'},
                                status=HTTPStatus.BAD_REQUEST)
            serializer = AvatarSerializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {'avatar': serializer.data['avatar']}, status=HTTPStatus.OK
            )

        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete()
            return Response(status=HTTPStatus.NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Retrieve the list of subscriptions with detailed information."""

        subscriptions = Subscription.objects.filter(
            user=request.user
        ).select_related('author').annotate(
            recipes_count=Count('author__recipes')
        )
        paginated_subscriptions = self.paginate_queryset(subscriptions)

        serializer = SubscriptionDetailSerializer(
            paginated_subscriptions,
            many=True,
            context={'request': request}
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

        if request.method == 'POST':
            serializer = SubscriptionSerializer(
                data={'author': author.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            subscription = Subscription.objects.filter(
                user=request.user, author=author
            ).annotate(recipes_count=Count('author__recipes')).first()

            return Response(
                SubscriptionDetailSerializer(
                    subscription,
                    context={'request': request}
                ).data,
                status=HTTPStatus.CREATED
            )

        if request.method == 'DELETE':
            deleted_count, _ = Subscription.objects.filter(
                user=request.user, author=author
            ).delete()
            if deleted_count == 0:
                return Response(
                    {'detail': 'You are not subscribed to this user'},
                    status=HTTPStatus.BAD_REQUEST
                )
            return Response(status=HTTPStatus.NO_CONTENT)
