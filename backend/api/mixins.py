class AvatarMixin:
    """Mixin для получения полного URL аватара пользователя."""

    def get_avatar(self, obj):
        """Возвращает полный url аватара."""
        if not obj.avatar:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.avatar.url)
        return obj.avatar.url


class IsSubscribedMixin:
    """Mixin для проверки подписки на пользователя."""

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на автора."""
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and request.user.subscriber.filter(author=obj).exists()
        )


class ImageMixin:
    """Mixin для получения полного URL изображения."""

    def get_image(self, obj):
        """Возвращает полный url изображения."""
        image_field = getattr(obj, 'image', None)
        if not image_field:
            return None
        if not hasattr(image_field, 'url'):
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(image_field.url)
        return image_field.url
