from collections.abc import Callable
from datetime import datetime
from typing import Protocol

from domain.booking.booking import Booking
from domain.booking.passenger_name import PassengerName
from domain.booking.seat_number import SeatNumber
from domain.exceptions import TicketingError, ValidationError
from domain.trip.city import City
from domain.trip.trip import Trip

DATE_TIME_FORMAT = "%Y-%m-%d %H:%M"


# Терминал иногда передает обрывки байтов кириллицы.
# Возвращаем их в байты и отбрасываем то, что не декодируется.
def read_line(prompt: str) -> str:
    raw = input(prompt)
    return raw.encode("utf-8", "surrogateescape").decode("utf-8", "ignore")


# Консоль зависит только от тех методов сервисов, которые вызывает.
class TripServicePort(Protocol):
    def next_id(self) -> int:
        raise NotImplementedError

    def add_trip(self, trip: Trip) -> None:
        raise NotImplementedError

    def get_all_trips(self) -> list[Trip]:
        raise NotImplementedError

    def find_trips_by_city(self, city: str) -> list[Trip]:
        raise NotImplementedError

    def update_trip(self, trip: Trip) -> None:
        raise NotImplementedError

    def delete_trip(self, trip_id: int) -> None:
        raise NotImplementedError


class BookingServicePort(Protocol):
    def add_booking(
        self,
        trip_id: int,
        passenger_name: PassengerName,
        seat: SeatNumber,
    ) -> Booking:
        raise NotImplementedError

    def get_all_bookings(self) -> list[Booking]:
        raise NotImplementedError

    def get_booking_trip(self, booking: Booking) -> Trip:
        raise NotImplementedError

    def update_booking(
        self,
        booking_id: int,
        passenger_name: PassengerName,
        seat: SeatNumber,
    ) -> Booking:
        raise NotImplementedError

    def delete_booking(self, booking_id: int) -> None:
        raise NotImplementedError


class Console:
    def __init__(
        self,
        trip_service: TripServicePort,
        booking_service: BookingServicePort,
    ) -> None:
        self.__trip_service = trip_service
        self.__booking_service = booking_service
        # Пункт меню: клавиша, название и метод-обработчик.
        self.__menu: list[tuple[str, str, Callable[[], None]]] = [
            ("1", "Показать все рейсы", self.__show_trips),
            ("2", "Найти рейс по городу", self.__find_trips),
            ("3", "Добавить рейс", self.__add_trip),
            ("4", "Изменить рейс", self.__update_trip),
            ("5", "Удалить рейс", self.__delete_trip),
            ("6", "Показать все брони", self.__show_bookings),
            ("7", "Забронировать билет", self.__add_booking),
            ("8", "Изменить бронь", self.__update_booking),
            ("9", "Удалить бронь", self.__delete_booking),
        ]

    def run(self) -> None:
        print("\nДобро пожаловать в систему бронирования билетов!")

        while True:
            self.__print_menu()

            try:
                choice = read_line("\nВыберите действие: ").strip()

                if choice == "0":
                    break

                self.__run_action(choice)
            # Ошибка не завершает программу: сообщение выводится,
            # и пользователь возвращается в меню.
            except TicketingError as error:
                print(f"\nОшибка: {error}")
            except ValueError as error:
                print(f"\nОшибка в данных: {error}")
            except (KeyboardInterrupt, EOFError):
                print()
                break

        print("\nДо свидания!")

    def __print_menu(self) -> None:
        print()

        for key, label, _ in self.__menu:
            print(f"{key}. {label}")

        print("0. Выход")

    def __run_action(self, choice: str) -> None:
        for key, _, action in self.__menu:
            if key == choice:
                action()
                return

        print("\nНеизвестная команда")

    def __show_trips(self) -> None:
        trips = self.__trip_service.get_all_trips()

        if not trips:
            print("\nРейсов пока нет")
            return

        self.__print_trips(trips)

    def __find_trips(self) -> None:
        city = read_line("\nВведите город или часть названия: ")
        trips = self.__trip_service.find_trips_by_city(city)

        if not trips:
            print("\nРейсы не найдены")
            return

        self.__print_trips(trips)

    def __add_trip(self) -> None:
        print()
        trip = self.__read_trip(self.__trip_service.next_id())

        self.__trip_service.add_trip(trip)
        print(f"\nРейс {trip.route} добавлен")

    def __update_trip(self) -> None:
        trip = self.__pick_trip("Номер рейса: ")

        if trip is None:
            return

        print("Оставьте поле пустым, чтобы не менять его")
        updated = self.__read_trip(trip.id, trip)

        self.__trip_service.update_trip(updated)
        print("\nРейс изменён")

    def __delete_trip(self) -> None:
        trip = self.__pick_trip("Номер рейса для удаления: ")

        if trip is None:
            return

        if not self.__confirm(f"Удалить рейс {trip.route}?"):
            print("\nУдаление отменено")
            return

        self.__trip_service.delete_trip(trip.id)
        print("\nРейс удалён")

    def __show_bookings(self) -> None:
        bookings = self.__booking_service.get_all_bookings()

        if not bookings:
            print("\nБроней пока нет")
            return

        self.__print_bookings(bookings)

    def __add_booking(self) -> None:
        trip = self.__pick_trip("Номер рейса: ")

        if trip is None:
            return

        print()
        name = self.__ask_name()
        seat = self.__ask_seat()

        self.__booking_service.add_booking(trip.id, name, seat)
        print(f"\nМесто {seat.value} забронировано")

    def __update_booking(self) -> None:
        booking = self.__pick_booking("Номер брони: ")

        if booking is None:
            return

        print("Оставьте поле пустым, чтобы не менять его")
        name = self.__ask_name(booking.passenger_name)
        seat = self.__ask_seat(booking.seat)

        self.__booking_service.update_booking(booking.id, name, seat)
        print("\nБронь изменена")

    def __delete_booking(self) -> None:
        booking = self.__pick_booking("Номер брони для удаления: ")

        if booking is None:
            return

        name = booking.passenger_name.value

        if not self.__confirm(f"Удалить бронь пассажира {name}?"):
            print("\nУдаление отменено")
            return

        self.__booking_service.delete_booking(booking.id)
        print("\nБронь удалена")

    def __pick_trip(self, prompt: str) -> Trip | None:
        trips = self.__trip_service.get_all_trips()

        if not trips:
            print("\nРейсов пока нет")
            return None

        self.__print_trips(trips)
        return trips[self.__choose(len(trips), prompt)]

    def __pick_booking(self, prompt: str) -> Booking | None:
        bookings = self.__booking_service.get_all_bookings()

        if not bookings:
            print("\nБроней пока нет")
            return None

        self.__print_bookings(bookings)
        return bookings[self.__choose(len(bookings), prompt)]

    # Поля вводятся по очереди, текущий рейс задает значения по умолчанию.
    def __read_trip(self, trip_id: int, current: Trip | None = None) -> Trip:
        origin = self.__ask_city(
            "Откуда", current.origin if current else None
        )

        def to_trip(raw: str) -> Trip:
            if raw:
                destination = City(raw)
            elif current is not None:
                destination = current.destination
            else:
                raise ValidationError("Название города не может быть пустым")

            # Временный рейс проверяет маршрут по правилам домена.
            return Trip(trip_id, origin, destination, datetime.max, 1)

        label = f" [{current.destination.value}]" if current else ""
        destination = self.__ask(f"Куда{label}: ", to_trip).destination

        return Trip(
            trip_id=trip_id,
            origin=origin,
            destination=destination,
            departure=self.__ask_departure(current),
            seat_count=self.__ask_seat_count(current),
        )

    def __ask_city(self, label: str, current: City | None) -> City:
        if current is None:
            return self.__ask(f"{label}: ", City)

        return self.__ask(
            f"{label} [{current.value}]: ",
            lambda raw: City(raw) if raw else current,
        )

    def __ask_departure(self, current: Trip | None) -> datetime:
        if current is None:
            return self.__ask(
                "Отправление (ГГГГ-ММ-ДД ЧЧ:ММ): ", self.__parse_date_time
            )

        departure = current.departure
        return self.__ask(
            f"Отправление [{departure:{DATE_TIME_FORMAT}}]: ",
            lambda raw: self.__parse_date_time(raw) if raw else departure,
        )

    def __ask_seat_count(self, current: Trip | None) -> int:
        if current is None:
            return self.__ask("Количество мест: ", self.__parse_int)

        seat_count = current.seat_count
        return self.__ask(
            f"Количество мест [{seat_count}]: ",
            lambda raw: self.__parse_int(raw) if raw else seat_count,
        )

    def __ask_name(
        self, current: PassengerName | None = None
    ) -> PassengerName:
        if current is None:
            return self.__ask("Имя пассажира: ", PassengerName)

        return self.__ask(
            f"Имя пассажира [{current.value}]: ",
            lambda raw: PassengerName(raw) if raw else current,
        )

    def __ask_seat(self, current: SeatNumber | None = None) -> SeatNumber:
        if current is None:
            return self.__ask(
                "Номер места: ",
                lambda raw: SeatNumber(self.__parse_int(raw)),
            )

        return self.__ask(
            f"Номер места [{current.value}]: ",
            lambda raw: (
                SeatNumber(self.__parse_int(raw)) if raw else current
            ),
        )

    @staticmethod
    def __print_trips(trips: list[Trip]) -> None:
        for index, trip in enumerate(trips, start=1):
            print(f"\n{index}. {trip.route}")
            print(f"   Отправление: {trip.departure:{DATE_TIME_FORMAT}}, "
                  f"мест: {trip.seat_count}")

    def __print_bookings(self, bookings: list[Booking]) -> None:
        for index, booking in enumerate(bookings, start=1):
            trip = self.__booking_service.get_booking_trip(booking)

            print(f"\n{index}. {booking.passenger_name.value}, "
                  f"место {booking.seat.value}")
            print(f"   Рейс: {trip.route}, "
                  f"{trip.departure:{DATE_TIME_FORMAT}}")

    @staticmethod
    def __parse_int(raw: str) -> int:
        try:
            return int(raw)
        except ValueError as error:
            raise ValidationError(f"«{raw}» — не целое число") from error

    @staticmethod
    def __parse_date_time(raw: str) -> datetime:
        try:
            return datetime.strptime(raw, DATE_TIME_FORMAT)
        except ValueError as error:
            raise ValidationError(
                f"«{raw}» — неверное время, нужен формат ГГГГ-ММ-ДД ЧЧ:ММ"
            ) from error

    # Повторяет вопрос, пока введенное значение не пройдет проверку.
    @staticmethod
    def __ask[T](prompt: str, parse: Callable[[str], T]) -> T:
        while True:
            raw = read_line(prompt).strip()

            try:
                return parse(raw)
            except ValidationError as error:
                print(f"Ошибка: {error}. Повторите ввод")

    # Пользователь вводит номер из списка, а возвращается индекс.
    def __choose(self, count: int, prompt: str) -> int:
        def to_index(raw: str) -> int:
            number = self.__parse_int(raw)

            if not 1 <= number <= count:
                raise ValidationError(f"Нужен номер от 1 до {count}")

            return number - 1

        print()
        return self.__ask(prompt, to_index)

    @staticmethod
    def __confirm(question: str) -> bool:
        answer = read_line(f"{question} (да/нет): ").strip().casefold()
        return answer in ("да", "д", "yes", "y")
