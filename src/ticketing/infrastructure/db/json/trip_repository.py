import json
from datetime import datetime
from pathlib import Path
from typing import Any

from domain.exceptions import (
    AlreadyExistsError,
    NotFoundError,
    StorageError,
    ValidationError,
)
from domain.trip.city import City
from domain.trip.trip import Trip


# Хранит рейсы в JSON-файле вида {"trips": [...]}.
# Каждая операция заново читает файл и сразу записывает изменения.
class JsonTripRepository:
    def __init__(self, file_path: str | Path) -> None:
        self.__file_path = Path(file_path)

        # Пустой файл создается сразу, чтобы чтение всегда находило его.
        if not self.__file_path.exists():
            self.__write_data([])

    def __read_data(self) -> list[dict[str, Any]]:
        data = self.__read_file()

        if not isinstance(data, dict) or not isinstance(
            data.get("trips"), list
        ):
            raise StorageError(f"В файле {self.__file_path} нет списка trips")

        trips: list[dict[str, Any]] = data["trips"]
        return trips

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

    def __write_data(self, trips: list[dict[str, Any]]) -> None:
        try:
            self.__file_path.parent.mkdir(parents=True, exist_ok=True)
            content = json.dumps(
                {"trips": trips}, ensure_ascii=False, indent=4
            )
            self.__file_path.write_bytes(content.encode("utf-8"))
        except (OSError, ValueError) as error:
            raise StorageError(
                f"Не удалось записать файл {self.__file_path}"
            ) from error

    # Любая ошибка в записи файла превращается в StorageError
    # с понятным сообщением вместо KeyError или ValueError.
    def __to_trip(self, item: dict[str, Any]) -> Trip:
        try:
            return Trip(
                trip_id=int(item["id"]),
                origin=City(item["origin"]),
                destination=City(item["destination"]),
                departure=datetime.fromisoformat(item["departure"]),
                seat_count=item["seat_count"],
            )
        except (
            KeyError,
            ValueError,
            TypeError,
            AttributeError,
            ValidationError,
        ) as error:
            raise StorageError(
                f"В файле {self.__file_path} повреждена запись рейса"
            ) from error

    @staticmethod
    def __to_dict(trip: Trip) -> dict[str, Any]:
        return {
            "id": trip.id,
            "origin": trip.origin.value,
            "destination": trip.destination.value,
            "departure": trip.departure.isoformat(),
            "seat_count": trip.seat_count,
        }

    @staticmethod
    def __find_index(
        trips: list[dict[str, Any]], trip_id: int
    ) -> int | None:
        for index, item in enumerate(trips):
            if item.get("id") == trip_id:
                return index

        return None

    def add(self, trip: Trip) -> None:
        trips = self.__read_data()

        if self.__find_index(trips, trip.id) is not None:
            raise AlreadyExistsError(f"Рейс {trip.id} уже существует")

        trips.append(self.__to_dict(trip))
        self.__write_data(trips)

    def get_by_id(self, trip_id: int) -> Trip | None:
        trips = self.__read_data()
        index = self.__find_index(trips, trip_id)

        if index is None:
            return None

        return self.__to_trip(trips[index])

    def get_all(self) -> list[Trip]:
        return [
            self.__to_trip(item)
            for item in self.__read_data()
        ]

    def find_by_city(self, city: str) -> list[Trip]:
        normalized_city = city.strip().casefold()

        return [
            trip
            for trip in self.get_all()
            if normalized_city in trip.route.casefold()
        ]

    def update(self, trip: Trip) -> None:
        trips = self.__read_data()
        index = self.__find_index(trips, trip.id)

        if index is None:
            raise NotFoundError(f"Рейс {trip.id} не найден")

        trips[index] = self.__to_dict(trip)
        self.__write_data(trips)

    def delete(self, trip_id: int) -> None:
        trips = self.__read_data()
        index = self.__find_index(trips, trip_id)

        if index is None:
            raise NotFoundError(f"Рейс {trip_id} не найден")

        del trips[index]
        self.__write_data(trips)
