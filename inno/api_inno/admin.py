from django.contrib import admin
from .models import WeatherForecast


@admin.register(WeatherForecast)
class WeatherForecastAdmin(admin.ModelAdmin):
    """
    Настройка отображения модели WeatherForecast в админке Django.
    """

    list_display = ('city', 'date', 'min_temperature', 'max_temperature')
    list_filter = ('city', 'date')
    search_fields = ('city',)
    ordering = ('date', 'city')
