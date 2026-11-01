from datetime import datetime

from domain.booking.repository import BookingRepository
from domain.exceptions import NotFoundError, ValidationError
from domain.trip.repository import TripRepository
from domain.trip.trip import Trip


# Сценарии работы с рейсами.
class TripService:
    def __init__(
        self,
        trip_repository: TripRepository,
        booking_repository: BookingRepository,
    ) -> None:
        self.__trip_repository = trip_repository
        self.__booking_repository = booking_repository

    # Новый id на единицу больше самого большого из сохраненных.
    def next_id(self) -> int:
        ids = [trip.id for trip in self.get_all_trips()]
        return max(ids, default=0) + 1

    def add_trip(self, trip: Trip) -> None:
        self.__check_departure(trip)
        self.__trip_repository.add(trip)

    def get_trip(self, trip_id: int) -> Trip:
        trip = self.__trip_repository.get_by_id(trip_id)

        if trip is None:
            raise NotFoundError(f"Рейс {trip_id} не найден")

        return trip

    def get_all_trips(self) -> list[Trip]:
        return self.__trip_repository.get_all()

    def find_trips_by_city(self, city: str) -> list[Trip]:
        return self.__trip_repository.find_by_city(city)

    def update_trip(self, trip: Trip) -> None:
        self.__check_departure(trip)

        # Нельзя убрать места, которые уже забронированы.
        for booking in self.__booking_repository.find_by_trip(trip.id):
            if booking.seat.value > trip.seat_count:
                raise ValidationError(
                    f"Место {booking.seat.value} уже забронировано"
                )

        self.__trip_repository.update(trip)

    def delete_trip(self, trip_id: int) -> None:
        trip = self.get_trip(trip_id)

        # Рейс с бронями удалять нельзя: у броней останутся
        # ссылки на несуществующую запись.
        if self.__booking_repository.find_by_trip(trip.id):
            raise ValidationError(
                f"Нельзя удалить рейс {trip.route}: у него есть брони"
            )

        self.__trip_repository.delete(trip.id)

    # Правило проверяет сервис, а не Trip: в файле могут законно
    # лежать рейсы, которые уже отправились.
    @staticmethod
    def __check_departure(trip: Trip) -> None:
        if trip.departure <= datetime.now():
            raise ValidationError("Отправление должно быть в будущем")
