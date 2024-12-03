from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from recipes.views import (IngredientViewSet, RecipeViewSet,
                           ShortLinkRedirectView, TagViewSet)
from rest_framework import routers
from users.views import UsersViewSet, UserVerificationViewSet

API_URL = 'api/'

router = routers.DefaultRouter()
router.register(r'users', UsersViewSet, basename='users')
router.register(r'auth/token', UserVerificationViewSet, basename='token')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'tags', TagViewSet, basename='tags')

urlpatterns = [
    path('admin/', admin.site.urls),
    path(f'{API_URL}', include(router.urls)),
    re_path(r'^s/(?P<pk>\d+)/$', ShortLinkRedirectView.as_view(),
            name='short-link-redirect'),
    path(
        'redoc/',
        TemplateView.as_view(template_name='redoc.html'),
        name='redoc'
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
