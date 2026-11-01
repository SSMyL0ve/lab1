from application.booking_service import BookingService
from application.trip_service import TripService
from domain.booking.repository import BookingRepository
from domain.exceptions import TicketingError
from domain.trip.repository import TripRepository
from presentation.console import Console, read_line
from infrastructure.db.json.booking_repository import (
    JsonBookingRepository,
)
from infrastructure.db.json.trip_repository import (
    JsonTripRepository,
)
from infrastructure.db.xml.booking_repository import (
    XmlBookingRepository,
)
from infrastructure.db.xml.trip_repository import (
    XmlTripRepository,
)

# Пункт выбора при запуске и соответствующий формат файлов.
STORAGE_FORMATS = {"1": "xml", "2": "json"}


def choose_storage_format() -> str:
    while True:
        choice = read_line(
            "Формат хранения данных (1 - XML, 2 - JSON): "
        ).strip()

        if choice in STORAGE_FORMATS:
            return STORAGE_FORMATS[choice]

        print("Введите 1 или 2")


def build_repositories(
    storage_format: str,
) -> tuple[TripRepository, BookingRepository]:
    if storage_format == "json":
        return (
            JsonTripRepository("data/trips.json"),
            JsonBookingRepository("data/bookings.json"),
        )

    return (
        XmlTripRepository("data/trips.xml"),
        XmlBookingRepository("data/bookings.xml"),
    )


# Собираем зависимости: репозитории передаются в сервисы,
# сервисы - в консоль.
def build_console(storage_format: str) -> Console:
    trip_repository, booking_repository = build_repositories(storage_format)

    trip_service = TripService(
        trip_repository=trip_repository,
        booking_repository=booking_repository,
    )
    booking_service = BookingService(
        booking_repository=booking_repository,
        trip_repository=trip_repository,
    )

    return Console(
        trip_service=trip_service,
        booking_service=booking_service,
    )


def main() -> None:
    try:
        storage_format = choose_storage_format()
    except (KeyboardInterrupt, EOFError):
        print()
        return

    try:
        console = build_console(storage_format)
    except TicketingError as error:
        print(f"Не удалось подготовить хранилище: {error}")
        return

    console.run()


if __name__ == "__main__":
    main()
