from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views import View
from interactions.models import Interaction
from interactions.serializers import ShoppingCartSerializer
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Ingredient, Recipe, Tag
from .permissions import IsAuthorOrReadOnly
from .serializers import (IngredientSerializer, RecipeCreateSerializer,
                          RecipeSerializer, TagSerializer)


class RecipeViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """ViewSet for managing recipes."""
    queryset = Recipe.objects.all()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateSerializer
        return RecipeSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'get_link']:
            return [AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAuthorOrReadOnly()]
        return [IsAuthenticated()]

    def apply_interaction_filter(self, queryset, param_name, interaction_type):
        """Filters queryset based on user interactions."""
        filter_value = self.request.query_params.get(param_name)
        user = self.request.user

        if filter_value in ['1', '0']:
            if not user.is_authenticated:
                return queryset.none()  # Anonymous user — empty result
            filter_value = filter_value == '1'
            if filter_value:
                return queryset.filter(
                    interactions__user=user,
                    interactions__interaction_type=interaction_type
                )
            else:
                return queryset.exclude(
                    interactions__user=user,
                    interactions__interaction_type=interaction_type
                )
        return queryset

    def get_queryset(self):
        queryset = super().get_queryset()

        # Sorting by publication date at the ORM level
        queryset = queryset.order_by('-id')

        # Filtering by author
        author_id = self.request.query_params.get('author')
        if author_id:
            queryset = queryset.filter(author__id=author_id)

        # Filtering by tags
        tags = self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()

        # Filtering by is_in_shopping_cart parameter
        queryset = self.apply_interaction_filter(
            queryset, 'is_in_shopping_cart', Interaction.SHOPPING_CART
        )

        # Filtering by is_favorited parameter
        queryset = self.apply_interaction_filter(
            queryset, 'is_favorited', Interaction.FAVORITE
        )

        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['get'], url_path='get-link')
    @permission_classes([AllowAny])
    def get_link(self, request, pk=None):
        """Get short link"""
        recipe = self.get_object()
        base_url = request.build_absolute_uri('/')
        short_link = f"{base_url.rstrip('/')}/s/{recipe.id}"

        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

    @action(
        detail=True, methods=['post', 'delete'], url_path='shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def manage_shopping_cart(self, request, pk=None):
        """Manage shopping cart: add (POST) or remove (DELETE)."""
        recipe = self.get_object()

        if request.method == 'POST':
            # Add to shopping cart
            interaction, created = Interaction.objects.get_or_create(
                user=request.user,
                recipe=recipe,
                interaction_type=Interaction.SHOPPING_CART
            )
            if not created:
                return Response(
                    {"detail": "Recipe is already in the shopping cart"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = ShoppingCartSerializer(interaction)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            # Remove from shopping cart
            interaction = Interaction.objects.filter(
                user=request.user,
                recipe=recipe,
                interaction_type=Interaction.SHOPPING_CART
            )
            if not interaction.exists():
                return Response(
                    {"detail": "Recipe is not in the shopping cart"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            interaction.delete()
            return Response(
                {
                    "detail": (
                        "Recipe successfully removed from the shopping cart"
                    )
                },
                status=status.HTTP_204_NO_CONTENT
            )

    @action(
        detail=False, methods=['get'], url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Download shopping list."""
        # Get all recipes in the shopping cart
        shopping_cart = Interaction.objects.filter(
            user=request.user,
            interaction_type=Interaction.SHOPPING_CART
        ).select_related('recipe')

        if not shopping_cart.exists():
            return Response(
                {"detail": "The shopping cart is empty"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Collect ingredients and their quantities
        shopping_list = {}
        for interaction in shopping_cart:
            recipe = interaction.recipe
            for ingredient in recipe.recipe_ingredients.all():
                name = ingredient.ingredient.name
                unit = ingredient.ingredient.measurement_unit
                amount = ingredient.amount
                if name in shopping_list:
                    shopping_list[name]['amount'] += amount
                else:
                    shopping_list[name] = {
                        'amount': amount,
                        'measurement_unit': unit
                    }

        # Create content for the text file
        shopping_list_content = "\n".join(
            f"{name} ({data['measurement_unit']}) — {data['amount']}"
            for name, data in shopping_list.items()
        )

        # Return text file as response
        response = HttpResponse(
            shopping_list_content,
            content_type='text/plain'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(
        detail=True, methods=['post', 'delete'], url_path='favorite',
        permission_classes=[IsAuthenticated]
    )
    def manage_favorite(self, request, pk=None):
        """Manage favorites: add (POST) or remove (DELETE)."""
        recipe = self.get_object()

        if request.method == 'POST':
            interaction, created = Interaction.objects.get_or_create(
                user=request.user,
                recipe=recipe,
                interaction_type=Interaction.FAVORITE
            )
            if not created:
                return Response(
                    {"detail": "Recipe is already in favorites"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {"detail": "Recipe added to favorites"},
                status=status.HTTP_201_CREATED
            )

        if request.method == 'DELETE':
            interaction = Interaction.objects.filter(
                user=request.user,
                recipe=recipe,
                interaction_type=Interaction.FAVORITE
            )
            if not interaction.exists():
                return Response(
                    {"detail": "Recipe is not in favorites"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            interaction.delete()
            return Response(
                {"detail": "Recipe removed from favorites"},
                status=status.HTTP_204_NO_CONTENT
            )


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for managing ingredients."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset

    def list(self, request, *args, **kwargs):
        """Dynamically disable pagination."""
        name = self.request.query_params.get('name')
        if name:  # If this is an autocomplete request
            self.pagination_class = None
        return super().list(request, *args, **kwargs)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for retrieving the list of tags and tag details."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class ShortLinkRedirectView(View):
    """Handler for redirecting using a short link."""

    def get(self, request, pk):
        # Find the recipe by the given ID
        recipe = get_object_or_404(Recipe, id=pk)
        # Redirect to the recipe detail page
        return HttpResponseRedirect(f'/recipes/{recipe.id}/')
