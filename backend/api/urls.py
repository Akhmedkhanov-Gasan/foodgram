from django.urls import include, path

from rest_framework.routers import DefaultRouter

from api.recipes.views import IngredientViewSet, RecipeViewSet, TagViewSet
from api.users.views import UsersViewSet


router = DefaultRouter()

router.register(r'users', UsersViewSet, basename='users')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'tags', TagViewSet, basename='tags')

urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
