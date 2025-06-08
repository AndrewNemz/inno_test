from rest_framework import serializers
import logging
import re
from datetime import datetime

from .validators import DateRangeValidator
from . import models


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class CurrentWeatherSerializer(serializers.Serializer):
    temperature = serializers.CharField(
        required=False,
        help_text="Текущая температура °C",
    )
    local_time = serializers.CharField(
        required=False,
        help_text="Местное время наблюдения HH:MM",
    )

    def validate_temperature(self, value):
        """
        Валидирует, что температура является числом.
        """
        try:
            celsius = float(value)  # Пытаемся преобразовать в число

            if celsius > 100:
                raise serializers.ValidationError("Температура не может быть выше 100°C")

            return value
        except ValueError:
            raise serializers.ValidationError("Температура должна быть числом")

    def validate_local_time(self, value):
        """
        Валидирует, что время соответствует формату HH:MM.
        """
        if not re.match(r"^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$", value):
            datetime_object = datetime.strptime(value, "%Y-%m-%d %I:%M %p")
            value = datetime_object.strftime("%H:%M")
        return value


class WeatherForecastSerializer(serializers.ModelSerializer):
    date = serializers.CharField(write_only=True, validators=[DateRangeValidator()])
    city = serializers.CharField(write_only=True)

    class Meta:
        model = models.WeatherForecast
        fields = ['city', 'date', 'min_temperature', 'max_temperature']

    def validate(self, data):
        """
        Проверяет что min_temperature <= max_temperature
        и преобразует date в объект date после валидации.
        """
        min_temp = data.get('min_temperature')
        max_temp = data.get('max_temperature')

        if min_temp is not None and max_temp is not None and min_temp > max_temp:
            raise serializers.ValidationError({
                'min_temperature': 'Не может быть больше max_temperature'
            })

        if 'date' in data:
            try:
                data['date'] = datetime.strptime(data['date'], '%d.%m.%Y').date()
            except ValueError:
                raise serializers.ValidationError({
                    'date': 'Неверный формат даты. Используйте DD.MM.YYYY'
                })

        return data

    def create(self, validated_data):
        """
        Создает или обновляет прогноз погоды.
        """
        city = validated_data['city']
        date = validated_data['date']

        instance, created = models.WeatherForecast.objects.update_or_create(
            city=city,
            date=date,
            defaults={
                'min_temperature': validated_data['min_temperature'],
                'max_temperature': validated_data['max_temperature']
            }
        )

        action = 'создан' if created else 'обновлен'
        logger.info(f'Прогноз погоды для {city} на {date} {action}')

        return instance
