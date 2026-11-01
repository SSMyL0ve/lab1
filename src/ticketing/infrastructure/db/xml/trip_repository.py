import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from domain.exceptions import (
    AlreadyExistsError,
    NotFoundError,
    StorageError,
    ValidationError,
)
from domain.trip.city import City
from domain.trip.trip import Trip


# Хранит рейсы в XML-файле: корень <trips>, внутри элементы <trip>.
# Каждая операция заново читает файл и сразу записывает изменения.
class XmlTripRepository:
    def __init__(self, file_path: str | Path) -> None:
        self.__file_path = Path(file_path)

        # Пустой файл создается сразу, чтобы чтение всегда находило его.
        if not self.__file_path.exists():
            self.__write_root(ET.Element("trips"))

    def __read_root(self) -> ET.Element:
        root = self.__parse_file()

        if root.tag != "trips":
            raise StorageError(
                f"В файле {self.__file_path} корень должен быть <trips>"
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
    def __to_element(trip: Trip) -> ET.Element:
        element = ET.Element("trip")

        ET.SubElement(element, "id").text = str(trip.id)
        ET.SubElement(element, "origin").text = trip.origin.value
        ET.SubElement(element, "destination").text = trip.destination.value
        ET.SubElement(element, "departure").text = trip.departure.isoformat()
        ET.SubElement(element, "seat_count").text = str(trip.seat_count)

        return element

    # Любая ошибка в записи файла превращается в StorageError
    # с понятным сообщением вместо KeyError или ValueError.
    def __to_trip(self, element: ET.Element) -> Trip:
        try:
            trip_id = element.findtext("id")
            origin = element.findtext("origin")
            destination = element.findtext("destination")
            departure = element.findtext("departure")
            seat_count = element.findtext("seat_count")

            if (
                not trip_id
                or origin is None
                or destination is None
                or not departure
                or not seat_count
            ):
                raise ValueError("не заполнены обязательные поля")

            return Trip(
                trip_id=int(trip_id),
                origin=City(origin),
                destination=City(destination),
                departure=datetime.fromisoformat(departure),
                seat_count=int(seat_count),
            )
        except (ValueError, ValidationError) as error:
            raise StorageError(
                f"В файле {self.__file_path} повреждена запись рейса"
            ) from error

    @staticmethod
    def __find_element(root: ET.Element, trip_id: int) -> ET.Element | None:
        for element in root.findall("trip"):
            if element.findtext("id") == str(trip_id):
                return element

        return None

    def add(self, trip: Trip) -> None:
        root = self.__read_root()

        if self.__find_element(root, trip.id) is not None:
            raise AlreadyExistsError(f"Рейс {trip.id} уже существует")

        root.append(self.__to_element(trip))
        self.__write_root(root)

    def get_by_id(self, trip_id: int) -> Trip | None:
        element = self.__find_element(self.__read_root(), trip_id)

        if element is None:
            return None

        return self.__to_trip(element)

    def get_all(self) -> list[Trip]:
        root = self.__read_root()

        return [
            self.__to_trip(element)
            for element in root.findall("trip")
        ]

    def find_by_city(self, city: str) -> list[Trip]:
        normalized_city = city.strip().casefold()

        return [
            trip
            for trip in self.get_all()
            if normalized_city in trip.route.casefold()
        ]

    def update(self, trip: Trip) -> None:
        root = self.__read_root()
        element = self.__find_element(root, trip.id)

        if element is None:
            raise NotFoundError(f"Рейс {trip.id} не найден")

        # Заменяем элемент на том же месте, чтобы порядок записей не менялся.
        index = list(root).index(element)
        root.remove(element)
        root.insert(index, self.__to_element(trip))
        self.__write_root(root)

    def delete(self, trip_id: int) -> None:
        root = self.__read_root()
        element = self.__find_element(root, trip_id)

        if element is None:
            raise NotFoundError(f"Рейс {trip_id} не найден")

        root.remove(element)
        self.__write_root(root)
