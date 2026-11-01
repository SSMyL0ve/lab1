import xml.etree.ElementTree as ET
from pathlib import Path
from uuid import UUID

from domain.booking.booking import Booking
from domain.booking.passenger_name import PassengerName
from domain.booking.seat_number import SeatNumber
from domain.exceptions import (
    AlreadyExistsError,
    NotFoundError,
    StorageError,
    ValidationError,
)


# Хранит брони в XML-файле: корень <bookings>, внутри элементы <booking>.
# Каждая операция заново читает файл и сразу записывает изменения.
class XmlBookingRepository:
    def __init__(self, file_path: str | Path) -> None:
        self.__file_path = Path(file_path)

        # Пустой файл создается сразу, чтобы чтение всегда находило его.
        if not self.__file_path.exists():
            self.__write_root(ET.Element("bookings"))

    def __read_root(self) -> ET.Element:
        root = self.__parse_file()

        if root.tag != "bookings":
            raise StorageError(
                f"В файле {self.__file_path} корень должен быть <bookings>"
            )

        return root

    def __parse_file(self) -> ET.Element:
        try:
            return ET.parse(self.__file_path).getroot()
        except ET.ParseError as error:
            raise StorageError(
                f"Файл {self.__file_path} повреждён: некорректный XML"
            ) from error
        except OSError as error:
            raise StorageError(
                f"Не удалось прочитать файл {self.__file_path}"
            ) from error

    def __write_root(self, root: ET.Element) -> None:
        try:
            self.__file_path.parent.mkdir(parents=True, exist_ok=True)
            ET.indent(root, space="    ")
            content = ET.tostring(
                root, encoding="utf-8", xml_declaration=True
            )
            self.__file_path.write_bytes(content)
        except (OSError, ValueError) as error:
            raise StorageError(
                f"Не удалось записать файл {self.__file_path}"
            ) from error

    @staticmethod
    def __to_element(booking: Booking) -> ET.Element:
        element = ET.Element("booking")

        ET.SubElement(element, "id").text = str(booking.id)
        ET.SubElement(element, "trip_id").text = str(booking.trip_id)
        ET.SubElement(
            element,
            "passenger_name",
        ).text = booking.passenger_name.value
        ET.SubElement(element, "seat").text = str(booking.seat.value)

        return element

    # Любая ошибка в записи файла превращается в StorageError
    # с понятным сообщением вместо KeyError или ValueError.
    def __to_booking(self, element: ET.Element) -> Booking:
        try:
            booking_id = element.findtext("id")
            trip_id = element.findtext("trip_id")
            passenger_name = element.findtext("passenger_name")
            seat = element.findtext("seat")

            if (
                not booking_id
                or not trip_id
                or passenger_name is None
                or not seat
            ):
                raise ValueError("не заполнены обязательные поля")

            return Booking(
                booking_id=UUID(booking_id),
                trip_id=UUID(trip_id),
                passenger_name=PassengerName(passenger_name),
                seat=SeatNumber(int(seat)),
            )
        except (ValueError, ValidationError) as error:
            raise StorageError(
                f"В файле {self.__file_path} повреждена запись брони"
            ) from error

    @staticmethod
    def __find_element(
        root: ET.Element, booking_id: UUID
    ) -> ET.Element | None:
        for element in root.findall("booking"):
            if element.findtext("id") == str(booking_id):
                return element

        return None

    def add(self, booking: Booking) -> None:
        root = self.__read_root()

        if self.__find_element(root, booking.id) is not None:
            raise AlreadyExistsError(f"Бронь {booking.id} уже существует")

        root.append(self.__to_element(booking))
        self.__write_root(root)

    def get_by_id(self, booking_id: UUID) -> Booking | None:
        element = self.__find_element(self.__read_root(), booking_id)

        if element is None:
            return None

        return self.__to_booking(element)

    def get_all(self) -> list[Booking]:
        root = self.__read_root()

        return [
            self.__to_booking(element)
            for element in root.findall("booking")
        ]

    def find_by_trip(self, trip_id: UUID) -> list[Booking]:
        return [
            booking
            for booking in self.get_all()
            if booking.trip_id == trip_id
        ]

    def update(self, booking: Booking) -> None:
        root = self.__read_root()
        element = self.__find_element(root, booking.id)

        if element is None:
            raise NotFoundError(f"Бронь {booking.id} не найдена")

        # Заменяем элемент на том же месте, чтобы порядок записей не менялся.
        index = list(root).index(element)
        root.remove(element)
        root.insert(index, self.__to_element(booking))
        self.__write_root(root)

    def delete(self, booking_id: UUID) -> None:
        root = self.__read_root()
        element = self.__find_element(root, booking_id)

        if element is None:
            raise NotFoundError(f"Бронь {booking_id} не найдена")

        root.remove(element)
        self.__write_root(root)
