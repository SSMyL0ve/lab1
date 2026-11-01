from datetime import datetime
from uuid import UUID, uuid7

from domain.booking.booking import Booking
from domain.booking.passenger_name import PassengerName
from domain.booking.repository import BookingRepository
from domain.booking.seat_number import SeatNumber
from domain.exceptions import (
    AlreadyExistsError,
    NotFoundError,
    ValidationError,
)
from domain.trip.repository import TripRepository
from domain.trip.trip import Trip


# Сценарии работы с бронями.
class BookingService:
    def __init__(
        self,
        booking_repository: BookingRepository,
        trip_repository: TripRepository,
    ) -> None:
        self.__booking_repository = booking_repository
        self.__trip_repository = trip_repository

    def add_booking(
        self,
        trip_id: UUID,
        passenger_name: PassengerName,
        seat: SeatNumber,
    ) -> Booking:
        booking = Booking(
            booking_id=uuid7(),
            trip_id=trip_id,
            passenger_name=passenger_name,
            seat=seat,
        )
        self.__check_seat(booking)
        self.__booking_repository.add(booking)
        return booking

    def get_booking(self, booking_id: UUID) -> Booking:
        booking = self.__booking_repository.get_by_id(booking_id)

        if booking is None:
            raise NotFoundError(f"Бронь {booking_id} не найдена")

        return booking

    def get_all_bookings(self) -> list[Booking]:
        return self.__booking_repository.get_all()

    def get_booking_trip(self, booking: Booking) -> Trip:
        return self.__get_trip(booking.trip_id)

    def update_booking(
        self,
        booking_id: UUID,
        passenger_name: PassengerName,
        seat: SeatNumber,
    ) -> Booking:
        booking = self.get_booking(booking_id)

        # Объекты неизменяемые, поэтому создаем бронь заново с тем же id.
        updated = Booking(
            booking_id=booking.id,
            trip_id=booking.trip_id,
            passenger_name=passenger_name,
            seat=seat,
        )
        self.__check_seat(updated)
        self.__booking_repository.update(updated)
        return updated

    def delete_booking(self, booking_id: UUID) -> None:
        self.__booking_repository.delete(booking_id)

    def __get_trip(self, trip_id: UUID) -> Trip:
        trip = self.__trip_repository.get_by_id(trip_id)

        if trip is None:
            raise NotFoundError(f"Рейс {trip_id} не найден")

        return trip

    def __check_seat(self, booking: Booking) -> None:
        trip = self.__get_trip(booking.trip_id)
        seat = booking.seat.value

        if trip.departure <= datetime.now():
            raise ValidationError(f"Рейс {trip.route} уже отправился")

        if seat > trip.seat_count:
            raise ValidationError(
                f"На рейсе {trip.route} места от 1 до {trip.seat_count}"
            )

        # Сама бронь при изменении не считается занятым местом.
        for other in self.__booking_repository.find_by_trip(trip.id):
            if other.seat.value == seat and other.id != booking.id:
                raise AlreadyExistsError(f"Место {seat} уже занято")
