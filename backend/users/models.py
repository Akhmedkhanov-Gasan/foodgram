from api.users.managers import CustomUserManager
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import (EmailValidator, MaxLengthValidator,
                                    RegexValidator)
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserProfile(AbstractUser):
    email = models.EmailField(
        _('email address'),
        unique=True,
        validators=[
            EmailValidator(message=_('Enter a valid email address')),
            MaxLengthValidator(254, _('Email cannot exceed 254 characters')),
        ],
        error_messages={
            'unique': _("A user with that email already exists."),
        },
    )
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message=_('Enter a valid username.'),
            )
        ],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    first_name = models.CharField(
        _('first name'),
        max_length=150,
        blank=False

    )
    last_name = models.CharField(
        _('last name'),
        max_length=150,
        blank=False
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        default=None,
        verbose_name=_('avatar')
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = CustomUserManager()

    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name=_('user')
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name=_('author')
    )

    class Meta:
        unique_together = ('user', 'author')
        verbose_name = _('subscription')
        verbose_name_plural = _('subscriptions')

    def __str__(self):
        return f"{self.user.username} follows {self.author.username}"
