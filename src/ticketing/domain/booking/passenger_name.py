from domain.exceptions import ValidationError

MAX_NAME_LENGTH = 100


# Объект-значение: имя пассажира, на которое оформлена бронь.
class PassengerName:
    def __init__(self, value: str) -> None:
        normalized = value.strip()

        if not normalized:
            raise ValidationError("Имя пассажира не может быть пустым")

        if len(normalized) > MAX_NAME_LENGTH:
            raise ValidationError(
                f"Имя пассажира не длиннее {MAX_NAME_LENGTH} символов"
            )

        self.__value = normalized

    @property
    def value(self) -> str:
        return self.__value
