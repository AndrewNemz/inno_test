from django.urls import path
from . import views


urlpatterns = [
    path(
        'weather/current/',
        views.CurrentWeatherView.as_view(),
        name='current_weather'
    ),
    path(
        'weather/forecast/',
        views.ForecastWeatherView.as_view(),
        name='forecast_weather'
    ),
]
