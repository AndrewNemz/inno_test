from django.db import models


class WeatherForecast(models.Model):
    """
    Модель для хранения прогноза погоды для конкретного города
    на определенную дату.
    """

    city = models.CharField(max_length=100, verbose_name="Город")
    date = models.CharField(max_length=32, verbose_name="Дата прогноза")
    min_temperature = models.FloatField(verbose_name="Мин температура °C")
    max_temperature = models.FloatField(verbose_name="Мак температура °C")

    def __str__(self):
        return f"Прогноз погоды для {self.city} на {self.date}"

    class Meta:
        verbose_name = "Прогноз погоды"
        verbose_name_plural = "Прогнозы погоды"
