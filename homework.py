import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv
from requests.exceptions import HTTPError, RequestException
from telegram.error import TelegramError

from exceptions import (CurrentDateKeyError, ResponseTypeError,
                        HomeworksTypeError, HomeworksKeyError,
                        HomeworkNameKeyError, HomeworkStatusKeyError,
                        VerdictKeyError)

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
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message):
    """Отправка сообщения о статусе работы в telegram."""
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logging.debug(f'Сообщение отправлено: "{message}"')


def get_api_answer(timestamp):
    """Запрос к api для получения статуса работы."""
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
    except RequestException as error:
        logging.error(f'Ошибка эндпоинта {error}')

    if response.status_code != HTTPStatus.OK:
        raise HTTPError(
            f'Ошибка запроса со статусом {response.status_code}'
        )

    return response.json()


def check_response(response):
    """Проверка валидности ответа от api."""
    if not isinstance(response, dict):
        logging.error('Ответ - не словарь!')
        raise ResponseTypeError()

    if 'current_date' not in response:
        logging.error('В ответе отсутствует текущая дата')
        raise CurrentDateKeyError('current_date')

    if 'homeworks' not in response:
        logging.error('В ответе отсутствует список работ')
        raise HomeworksKeyError('homeworks')

    if not isinstance(response['homeworks'], list):
        logging.error('Перечень работ - не список!')
        raise HomeworksTypeError('homeworks')


def parse_status(homework):
    """Получить статус работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    verdict = HOMEWORK_VERDICTS.get(homework_status)

    if not homework_name:
        logging.error('Отсутствует ключ "homework_name"')
        raise HomeworkNameKeyError('homework_name')
    if not homework_status:
        logging.error('Отсутствует ключ "status"')
        raise HomeworkStatusKeyError('status')
    if not verdict:
        logging.error('Некорректное значение статуса работы')
        raise VerdictKeyError()

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Ошибка при получении токенов или id чата')
        raise SystemExit(1)

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    previous_status = ''
    current_status = ''
    error_message_sent = False

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
                error_message_sent = False
            else:
                logging.info('Изменений нет')

            timestamp = response['current_date']

        except Exception as error:
            logging.error(f'Ошибка: {error}')

            if not error_message_sent:
                message = f'Сбой в работе программы: {error}'

                try:
                    send_message(bot, error)
                    error_message_sent = True
                except TelegramError as tg_error:
                    logging.error(f'Ошибка TG: {tg_error}')

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    log_file_path = os.path.join(BASE_DIR, 'output.log')

    logging.basicConfig(
        level=logging.DEBUG,
        format=(
            '%(asctime)s [%(levelname)s] - '
            '(%(filename)s).%(funcName)s:%(lineno)d - %(message)s'
        ),
        handlers=[
            logging.FileHandler(log_file_path),
            logging.StreamHandler(sys.stdout)
        ]
    )

    main()
