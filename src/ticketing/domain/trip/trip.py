from datetime import datetime

from domain.exceptions import ValidationError
from domain.trip.city import City

MAX_SEAT_COUNT = 1000


# Рейс. Поля закрыты и доступны только для чтения,
# изменение рейса - это создание нового объекта с тем же id.
class Trip:
    def __init__(
            self,
            trip_id: int,
            origin: City,
            destination: City,
            departure: datetime,
            seat_count: int
    ) -> None:
        if origin.value.casefold() == destination.value.casefold():
            raise ValidationError(
                "Города отправления и прибытия должны различаться"
            )

        if not 1 <= seat_count <= MAX_SEAT_COUNT:
            raise ValidationError(
                f"Количество мест должно быть от 1 до {MAX_SEAT_COUNT}"
            )

        self.__id = trip_id
        self.__origin = origin
        self.__destination = destination
        self.__departure = departure
        self.__seat_count = seat_count

    @property
    def id(self) -> int:
        return self.__id

    @property
    def origin(self) -> City:
        return self.__origin

    @property
    def destination(self) -> City:
        return self.__destination

    @property
    def departure(self) -> datetime:
        return self.__departure

    @property
    def seat_count(self) -> int:
        return self.__seat_count

    @property
    def route(self) -> str:
        return f"{self.__origin.value} → {self.__destination.value}"
