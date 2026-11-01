from domain.exceptions import ValidationError


# Объект-значение: номер места. Верхнюю границу проверяет сервис,
# потому что количество мест известно только рейсу.
class SeatNumber:
    def __init__(self, value: int) -> None:
        if value < 1:
            raise ValidationError("Номер места должен быть больше нуля")

        self.__value = value

    @property
    def value(self) -> int:
        return self.__value
