from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework import status
from datetime import datetime
import requests
import logging

from .validators import DateRangeValidator
from . import models
from . import serializers


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def get_weather_data(city):
    logger.info(f'Получение данных о погоде с wttr.in для города - {city}')
    url = f"https://wttr.in/{city}?format=j1"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к wttr.in API: {e}")
        return None


def get_forecact_weather(latitude, longitude, city, date):
    logger.info(f'Получение прогноза погоды для города {city}')
    try:
        date_obj = datetime.strptime(date, "%d.%m.%Y")
        api_date = date_obj.strftime("%Y-%m-%d")
        params = {
            "latitude": str(latitude),
            "longitude": str(longitude),
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
            "start_date": api_date,
            "end_date": api_date,
            "timezone": "auto"
        }

        response = requests.get("https://api.open-meteo.com/v1/forecast", params=params)
        response.raise_for_status()
        data = response.json()["daily"]
        return {
            "date": api_date,
            "temp_max": data["temperature_2m_max"][0],
            "temp_min": data["temperature_2m_min"][0],
        }
    except requests.RequestException as e:
        raise Exception(f"Ошибка при запросе к API: {str(e)}")
    except ValueError:
        raise ValueError("Неверный формат даты. Используйте DD.MM.YYYY")
    except Exception as error:
        raise error


class CurrentWeatherView(APIView):

    def get(self, request):
        logger.info('Вызов метода для получения текущей температуры в городе')
        try:
            city = request.query_params.get('city')
            if not city:
                return Response(
                    {"error": "Необходимо указать название города"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            weather_data = get_weather_data(city)
            if not weather_data:
                return Response(
                    {"error": f"Город '{city}' не найден или недоступен."},
                    status=status.HTTP_404_NOT_FOUND
                )

            current_condition = weather_data.get('current_condition')
            temperature = current_condition[0].get('temp_C')
            local_time = current_condition[0].get('localObsDateTime')
            if temperature is not None and local_time is not None:
                data = {
                    "temperature": temperature,
                    "local_time": local_time,
                }

            serializer = serializers.CurrentWeatherSerializer(data=data)
            if serializer.is_valid():
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                logger.error(f"Ошибка сериализации данных: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(e)


class ForecastWeatherView(APIView):
    """
    Позволяет вручную задать или переопределить прогноз погоды
    для указанного города определенную дату.
    """
    def get(self, request):
        logger.info('Вызов метода для получения прогноза погоды в городе')
        try:
            city = request.query_params.get('city')
            date = request.query_params.get('date')

            date_validator = DateRangeValidator()
            try:
                date_validator(date)
            except ValidationError as e:
                return Response({"error": e.detail}, status=status.HTTP_400_BAD_REQUEST)

            if not city or not date:
                return Response(
                    {"error": "Необходимо указать название города и дату"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            forecast = models.WeatherForecast.objects.filter(
                city=city,
                date=datetime.strptime(date, '%d.%m.%Y').date()
            ).exists()
            if forecast:
                logger.info(f'Уже был создан такой прогноз для города {city} на дату {date}')
                obj = models.WeatherForecast.objects.get(
                    city=city,
                    date=datetime.strptime(date, '%d.%m.%Y').date()
                )
                return Response(
                    {
                        "min_temperature": obj.min_temperature,
                        "max_temperature": obj.max_temperature
                    },
                    status=status.HTTP_200_OK
                )

            coordinates = get_weather_data(city)
            if not coordinates:
                return Response(
                    {"error": f"Город '{city}' не найден или недоступен на источнике wttr.in"},
                    status=status.HTTP_404_NOT_FOUND
                )
            nearest_area_list = coordinates.get('nearest_area')
            if nearest_area_list and isinstance(nearest_area_list, list) and len(nearest_area_list) > 0:
                nearest_area = nearest_area_list[0]
                latitude = nearest_area.get('latitude')
                longitude = nearest_area.get('longitude')
            else:
                return Response(
                    {"error": f"Не удалось извлечь широту или долготу для города {city}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            forecact_weather = get_forecact_weather(latitude, longitude, city, date)
            data = {
                "city": city,
                "date": date,
                "min_temperature": forecact_weather['temp_min'],
                "max_temperature": forecact_weather['temp_max']
            }

            serializer = serializers.WeatherForecastSerializer(data=data)
            if serializer.is_valid():
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                logger.error(f"Ошибка сериализации данных: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(e)

    def post(self, request, *args, **kwargs):
        serializer = serializers.WeatherForecastSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            logger.error(f"Ошибка валидации данных: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
