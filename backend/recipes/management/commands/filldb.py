import json

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    def handle(self, *args, **options):
        file_path = '/app/data/ingredients.json'
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    Ingredient.objects.get_or_create(
                        name=item['name'],
                        measurement_unit=item['measurement_unit']
                    )
            self.stdout.write(self.style.SUCCESS('Данные загружены успешно!'))
        except FileNotFoundError:
            self.stderr.write(f'Файл не найден: {file_path}')
        except json.JSONDecodeError as e:
            self.stderr.write(f'Ошибка JSON: {e}')
        except Exception as e:
            self.stderr.write(f'Неожиданная ошибка: {e}')
