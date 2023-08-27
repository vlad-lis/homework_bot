class TokenError(Exception):
    """Исключение для ошибки токена или чат айди."""

    def __init__(self, message='Ошибка токена'):  # noqa: D107
        self.message = message
        super().__init__(self.message)
