from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from datetime import date, timedelta, datetime


class DateRangeValidator:

    def __call__(self, value):
        parsed_date = datetime.strptime(value, "%d.%m.%Y").date()
        today = date.today()
        max_date = today + timedelta(days=10)

        if parsed_date < today:
            raise ValidationError("Дата не может быть в прошлом")
        if parsed_date > max_date:
            raise ValidationError(f"Дата не может быть позже {max_date.strftime('%d.%m.%Y')}")

        return parsed_date
