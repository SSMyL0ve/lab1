from domain.booking.passenger_name import PassengerName
from domain.booking.seat_number import SeatNumber


# Бронь хранит только id рейса, сами рейсы лежат
# в отдельном хранилище.
class Booking:
    def __init__(
            self,
            booking_id: int,
            trip_id: int,
            passenger_name: PassengerName,
            seat: SeatNumber
    ) -> None:
        self.__id = booking_id
        self.__trip_id = trip_id
        self.__passenger_name = passenger_name
        self.__seat = seat

    @property
    def id(self) -> int:
        return self.__id

    @property
    def trip_id(self) -> int:
        return self.__trip_id

    @property
    def passenger_name(self) -> PassengerName:
        return self.__passenger_name

    @property
    def seat(self) -> SeatNumber:
        return self.__seat
