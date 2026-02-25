from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    """Разрешение: только автор может изменять объект."""

    def has_object_permission(self, request, view, obj):
        """Проверка прав на уровне объекта."""
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )


class IsAuthenticatedOrRegistration(permissions.BasePermission):
    """Регистрация и чтение всем, остальное только аутентифицированным."""

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or view.action == 'create'
            or request.user.is_authenticated
        )
