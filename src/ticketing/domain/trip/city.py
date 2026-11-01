from domain.exceptions import ValidationError

MAX_CITY_LENGTH = 60


# Объект-значение: город проверяется один раз при создании,
# поэтому дальше в коде можно не повторять проверки.
class City:
    def __init__(self, value: str) -> None:
        normalized = value.strip()

        if not normalized:
            raise ValidationError("Название города не может быть пустым")

        if len(normalized) > MAX_CITY_LENGTH:
            raise ValidationError(
                f"Название города не длиннее {MAX_CITY_LENGTH} символов"
            )

        self.__value = normalized

    @property
    def value(self) -> str:
        return self.__value
