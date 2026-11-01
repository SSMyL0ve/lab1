from typing import Protocol
from uuid import UUID

from domain.trip.trip import Trip


# Интерфейс хранилища. Его реализуют репозитории JSON и XML,
# поэтому сервисы не зависят от формата файла.
class TripRepository(Protocol):
    def add(self, trip: Trip) -> None:
        raise NotImplementedError

    def get_by_id(self, trip_id: UUID) -> Trip | None:
        raise NotImplementedError

    def get_all(self) -> list[Trip]:
        raise NotImplementedError

    def find_by_city(self, city: str) -> list[Trip]:
        raise NotImplementedError

    def update(self, trip: Trip) -> None:
        raise NotImplementedError

    def delete(self, trip_id: UUID) -> None:
        raise NotImplementedError
