# Базовое исключение приложения: консоль перехватывает его
# и показывает пользователю сообщение вместо трассировки.
class TicketingError(Exception):
    pass


# Данные нарушают правила предметной области.
class ValidationError(TicketingError):
    pass


# Записи с указанным id нет в хранилище.
class NotFoundError(TicketingError):
    pass


# Такая запись уже есть в хранилище.
class AlreadyExistsError(TicketingError):
    pass


# Файл хранилища не удалось прочитать, записать или разобрать.
class StorageError(TicketingError):
    pass
