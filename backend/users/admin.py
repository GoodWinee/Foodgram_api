from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from users.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Админ-панель пользователя."""

    list_display = ('username', 'email', 'first_name', 'last_name', 'avatar')
    search_fields = ('username', 'email')
    list_filter = ('username', 'email')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительно', {'fields': ('avatar',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Дополнительно', {'fields': ('avatar',)}),
    )
