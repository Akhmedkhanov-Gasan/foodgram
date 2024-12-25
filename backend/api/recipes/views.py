from api.pagination import PageToLimitOffsetPagination
from api.permissions import IsAuthorOrReadOnly
from api.recipes.filters import RecipeFilter
from api.recipes.serializers import (IngredientSerializer,
                                     RecipeCreateSerializer, RecipeSerializer,
                                     TagSerializer)
from django.db.models import F, Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from rest_framework import status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing recipes."""

    queryset = Recipe.objects.select_related('author').prefetch_related(
        'tags',
        'ingredients'
    )
    filterset_class = RecipeFilter
    pagination_class = PageToLimitOffsetPagination

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'get_link']:
            return [AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAuthorOrReadOnly()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post', 'delete'], url_path='favorite',
            permission_classes=[IsAuthenticated])
    def manage_favorite(self, request, pk=None):
        """Add or remove a recipe from favorites."""
        recipe = self.get_object()
        return self._handle_interaction(request, recipe, Favorite)

    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart',
            permission_classes=[IsAuthenticated])
    def manage_shopping_cart(self, request, pk=None):
        """Add or remove a recipe from the shopping cart."""
        recipe = self.get_object()
        return self._handle_interaction(request, recipe, ShoppingCart)

    @action(detail=True, methods=['get'], url_path='get-link')
    @permission_classes([AllowAny])
    def get_link(self, request, pk=None):
        """Get short link"""
        recipe = self.get_object()
        base_url = request.build_absolute_uri('/')
        short_link = f"{base_url.rstrip('/')}/s/{recipe.id}"

        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

    def _handle_interaction(self, request, recipe, interaction_model):
        """Helper function to manage interactions (favorite, shopping cart)."""

        user = request.user

        if request.method == 'POST':
            if interaction_model.objects.filter(user=user,
                                                recipe=recipe).exists():
                return Response(
                    {
                        "detail": (
                            f"Recipe is already in the "
                            f"{interaction_model.__name__.lower()}"
                        )},
                    status=status.HTTP_400_BAD_REQUEST
                )
            interaction_model.objects.create(user=user, recipe=recipe)
            response_data = {
                "id": recipe.id,
                "name": recipe.name,
                "image": request.build_absolute_uri(
                    recipe.image.url) if recipe.image else None,
                "cooking_time": recipe.cooking_time,
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            interaction_item = interaction_model.objects.filter(user=user,
                                                                recipe=recipe)
            if not interaction_item.exists():
                return Response(
                    {
                        "detail": (
                            f"Recipe is not in the "
                            f"{interaction_model.__name__.lower()}"
                        )},
                    status=status.HTTP_400_BAD_REQUEST
                )
            interaction_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=['get'], url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Download shopping list."""

        ingredients = (
            request.user.shopping_cart
            .values(
                name=F('recipe__recipe_ingredients__ingredient__name'),
                measurement_unit=F(
                    'recipe__recipe_ingredients__ingredient__measurement_unit')
            )
            .annotate(total_amount=Sum('recipe__recipe_ingredients__amount'))
            .order_by('name')
        )

        if not ingredients:
            return Response(
                {"detail": "The shopping cart is empty"},
                status=status.HTTP_400_BAD_REQUEST
            )

        file_content = self._generate_shopping_list_file(ingredients)

        response = HttpResponse(
            file_content,
            content_type='text/plain'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    def _generate_shopping_list_file(self, ingredients):
        shopping_list = "\n".join(
            f"{item['name']} ({item['measurement_unit']}) "
            f"— {item['total_amount']}"
            for item in ingredients
        )
        return shopping_list


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
        """Return plain list of ingredients without pagination."""

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for retrieving the list of tags and tag details."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class ShortLinkRedirectView(APIView):
    """Handler for redirecting using a short link."""

    def get(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        url = reverse('recipe-detail', args=[recipe.id])
        return HttpResponseRedirect(url)