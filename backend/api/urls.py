from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.recipes.views import IngredientViewSet, RecipeViewSet, TagViewSet
from api.users.views import UsersViewSet, UserVerificationViewSet

router = DefaultRouter()

router.register(r'users', UsersViewSet, basename='users')
router.register(r'auth/token', UserVerificationViewSet, basename='token')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'tags', TagViewSet, basename='tags')

urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('', include(router.urls)),
]
