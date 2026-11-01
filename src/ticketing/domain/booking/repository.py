from typing import Protocol

from domain.booking.booking import Booking


# Интерфейс хранилища. Его реализуют репозитории JSON и XML,
# поэтому сервисы не зависят от формата файла.
class BookingRepository(Protocol):
    def add(self, booking: Booking) -> None:
        raise NotImplementedError

    def get_by_id(self, booking_id: int) -> Booking | None:
        raise NotImplementedError

    def get_all(self) -> list[Booking]:
        raise NotImplementedError

    def find_by_trip(self, trip_id: int) -> list[Booking]:
        raise NotImplementedError

    def update(self, booking: Booking) -> None:
        raise NotImplementedError

    def delete(self, booking_id: int) -> None:
        raise NotImplementedError
