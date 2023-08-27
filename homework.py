import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv
from requests.exceptions import HTTPError, RequestException

from exceptions import TokenError

load_dotenv()


PRACTICUM_TOKEN = os.getenv('YA_TOKEN')
TELEGRAM_TOKEN = os.getenv('TG_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка наличия токенов и id чата в env."""
    if (
        PRACTICUM_TOKEN is None
        or TELEGRAM_TOKEN is None
        or TELEGRAM_CHAT_ID is None
    ):
        raise TokenError()

    return True


def send_message(bot, message):
    """Отправка сообщения о статусе работы в telegram."""
    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(timestamp):
    """Запрос к api для получения статуса работы."""
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
    except RequestException as error:
        print(error)

    if response.status_code != HTTPStatus.OK:
        raise HTTPError(
            f'Ошибка запроса со статусом {response.status_code}'
        )

    return response.json()


def check_response(response):
    """Проверка валидности ответа от api."""
    if not isinstance(response, dict):
        raise TypeError('Некорректный тип ответа')

    if 'current_date' not in response:
        raise KeyError('В ответе отсутствует ключ "current_date"')

    if 'homeworks' not in response:
        raise KeyError('В ответе отсутствует ключ "homeworks"')

    if not isinstance(response['homeworks'], list):
        raise TypeError('Некорректный тип "homeworks"')


def parse_status(homework):
    """Получить статус работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    verdict = HOMEWORK_VERDICTS.get(homework_status)

    if not homework_name:
        raise KeyError('Отсутствует ключ "homework_name"')
    if not homework_status:
        raise KeyError('Отсутствует ключ "status"')
    if not verdict:
        raise KeyError('Некорректное значение статуса работы')

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        exit(1)

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    previous_status = ''
    current_status = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)

            if len(response['homeworks']) > 0:
                homework = response['homeworks'][0]
                previous_status = homework['status']

            if current_status != previous_status:
                message = parse_status(homework)
                send_message(bot, message)
                current_status = homework['status']

            timestamp = response['current_date']

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            print(message)

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
