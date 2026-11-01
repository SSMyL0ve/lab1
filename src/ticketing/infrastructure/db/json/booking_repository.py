import json
from pathlib import Path
from typing import Any

from domain.booking.booking import Booking
from domain.booking.passenger_name import PassengerName
from domain.booking.seat_number import SeatNumber
from domain.exceptions import (
    AlreadyExistsError,
    NotFoundError,
    StorageError,
    ValidationError,
)


# Хранит брони в JSON-файле вида {"bookings": [...]}.
# Каждая операция заново читает файл и сразу записывает изменения.
class JsonBookingRepository:
    def __init__(self, file_path: str | Path) -> None:
        self.__file_path = Path(file_path)

        # Пустой файл создается сразу, чтобы чтение всегда находило его.
        if not self.__file_path.exists():
            self.__write_data([])

    def __read_data(self) -> list[dict[str, Any]]:
        data = self.__read_file()

        if not isinstance(data, dict) or not isinstance(
            data.get("bookings"), list
        ):
            raise StorageError(
                f"В файле {self.__file_path} нет списка bookings"
            )

        bookings: list[dict[str, Any]] = data["bookings"]
        return bookings

    def __read_file(self) -> Any:
        try:
            with self.__file_path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except ValueError as error:
            raise StorageError(
                f"Файл {self.__file_path} повреждён: некорректный JSON"
            ) from error
        except OSError as error:
            raise StorageError(
                f"Не удалось прочитать файл {self.__file_path}"
            ) from error

    def __write_data(self, bookings: list[dict[str, Any]]) -> None:
        try:
            self.__file_path.parent.mkdir(parents=True, exist_ok=True)
            content = json.dumps(
                {"bookings": bookings}, ensure_ascii=False, indent=4
            )
            self.__file_path.write_bytes(content.encode("utf-8"))
        except (OSError, ValueError) as error:
            raise StorageError(
                f"Не удалось записать файл {self.__file_path}"
            ) from error

    # Любая ошибка в записи файла превращается в StorageError
    # с понятным сообщением вместо KeyError или ValueError.
    def __to_booking(self, item: dict[str, Any]) -> Booking:
        try:
            return Booking(
                booking_id=int(item["id"]),
                trip_id=int(item["trip_id"]),
                passenger_name=PassengerName(item["passenger_name"]),
                seat=SeatNumber(item["seat"]),
            )
        except (
            KeyError,
            ValueError,
            TypeError,
            AttributeError,
            ValidationError,
        ) as error:
            raise StorageError(
                f"В файле {self.__file_path} повреждена запись брони"
            ) from error

    @staticmethod
    def __to_dict(booking: Booking) -> dict[str, Any]:
        return {
            "id": booking.id,
            "trip_id": booking.trip_id,
            "passenger_name": booking.passenger_name.value,
            "seat": booking.seat.value,
        }

    @staticmethod
    def __find_index(
        bookings: list[dict[str, Any]], booking_id: int
    ) -> int | None:
        for index, item in enumerate(bookings):
            if item.get("id") == booking_id:
                return index

        return None

    def add(self, booking: Booking) -> None:
        bookings = self.__read_data()

        if self.__find_index(bookings, booking.id) is not None:
            raise AlreadyExistsError(f"Бронь {booking.id} уже существует")

        bookings.append(self.__to_dict(booking))
        self.__write_data(bookings)

    def get_by_id(self, booking_id: int) -> Booking | None:
        bookings = self.__read_data()
        index = self.__find_index(bookings, booking_id)

        if index is None:
            return None

        return self.__to_booking(bookings[index])

    def get_all(self) -> list[Booking]:
        return [
            self.__to_booking(item)
            for item in self.__read_data()
        ]

    def find_by_trip(self, trip_id: int) -> list[Booking]:
        return [
            booking
            for booking in self.get_all()
            if booking.trip_id == trip_id
        ]

    def update(self, booking: Booking) -> None:
        bookings = self.__read_data()
        index = self.__find_index(bookings, booking.id)

        if index is None:
            raise NotFoundError(f"Бронь {booking.id} не найдена")

        bookings[index] = self.__to_dict(booking)
        self.__write_data(bookings)

    def delete(self, booking_id: int) -> None:
        bookings = self.__read_data()
        index = self.__find_index(bookings, booking_id)

        if index is None:
            raise NotFoundError(f"Бронь {booking_id} не найдена")

        del bookings[index]
        self.__write_data(bookings)
