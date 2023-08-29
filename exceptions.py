class ResponseTypeError(TypeError):
    """Response type error."""

    def __init__(self):  # noqa: D107
        super().__init__('Некорректный тип ответа. Ожидается dict.')


class HomeworksTypeError(TypeError):
    """Homeworks list type error."""

    def __init__(self, homeworks):  # noqa: D107
        self.homeworks = homeworks
        super().__init__(f'Некорректный тип перечня работ "{homeworks}"')


class CustomKeyError(KeyError):
    """General Custom KeyError."""

    def __init__(self, key_name):  # noqa: D107
        self.key_name = key_name
        super().__init__(f'В ответе отсутствует ключ "{key_name}"')


class CurrentDateKeyError(CustomKeyError):
    """Current Date Key Error."""

    pass


class HomeworksKeyError(CustomKeyError):
    """Homeworks Key Error."""

    pass


class HomeworkNameKeyError(CustomKeyError):
    """No homework_name in response."""

    pass


class HomeworkStatusKeyError(CustomKeyError):
    """No homework_status in response."""

    pass


class VerdictKeyError(KeyError):
    """Unexpected value of verdict (status)."""

    def __init__(self):  # noqa: D107
        super().__init__('Неизвестное значение статуса (вердикт)')
