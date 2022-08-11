import re
import datetime
import requests

import pygsheets

from configs.admin_bot_config import ADMIN_BOT_TOKEN, ADMIN_CHAT_ID


def time_converter(time: str) -> float:
	"""
	Преобразует входящую время из любого формата (8ч, 8часов, 8 часов, 8,3 часов, 8, 8,3, 8) в формат 8.0
			Параметры:
					time (str): время исходного формата
			Возвращаемое значение:
					curr_digits (float): время, преобразованное в конечный формат
	"""
	curr_time = time.replace(',', '.')
	time_list = curr_time.split()[0]
	digits = re.match('[.0-9]+', time_list)[0]
	curr_digits = float(digits)
	return curr_digits


def date_converter(date: str) -> str:
	"""
	Преобразует входящую дату из любого формата (6.5.22, 06.05.22, 6.5.2022, 06.05.2022) в формат 06.05.2022
			Параметры:
					date (str): дата исходного формата
			Возвращаемое значение:
					current_date (str): дата, преобразованная в конечный формат
	"""
	current_year = datetime.datetime.today().year
	splited_date = date.split('.')
	if len(splited_date) == 2:
		splited_date.append(str(current_year))
	splited_date[-1] = splited_date[-1] if len(splited_date[-1]) == 4 else f'20{splited_date[-1]}'
	int_date = list(map(int, splited_date))
	current_date = datetime.date(int_date[2], int_date[1], int_date[0]).strftime('%d.%m.%Y')
	return current_date


def send_to_admin_bot(text: str):
	"""
	Отправляет уведомления в Админ-бот
			Параметры:
					text (str): Сообщение, которое должно быть отправлено
	"""
	requests.get(f'https://api.telegram.org/bot{ADMIN_BOT_TOKEN}/sendMessage?chat_id={ADMIN_CHAT_ID}&text={text}')


def report_time_converter(time: str) -> tuple:
	"""
	Преобразует информацию о времени, до которого необходимо сдать отчет, из строкового формата в числовой
				Параметры:
					time (str): Время, до которого необходимо сдать отчет
				Возвращаемое значение:
					hour (int): Час, до которого необходимо сдать отчет
					minute (int): Минута, до которой необходимо сдать отчет
	"""
	splited_report_time = time.split(':')
	hour, minute = list(map(int, splited_report_time))
	return hour, minute


def open_sheet():
	"""
	Функция открывает таблицу report_info в Google-таблицах. Если такой таблицы не существует, создает ее
				Возвращаемое значение:
					worksheet (Google-sheet): Таблица в Google-таблицах
	"""
	client = pygsheets.authorize(service_account_file='usr/bin/New/service.json')
	try:
		sheet = client.open('report_info')
	except Exception:
		client.create("report_info")
		sheet = client.open('report_info')

		sheet.share('alien.testingacc@gmail.com', role='writer', type='user')
		sheet.share('', role='reader', type='anyone')

	worksheet = sheet.sheet1

	worksheet.update_value('A1', 'Имя пользователя')
	worksheet.update_value('B1', 'Дата отчета')
	worksheet.update_value('C1', 'Текст отчета')
	worksheet.update_value('D1', 'Время, затраченное на выполнение')

	return worksheet


def translate_hours(hours: float) -> str:
	words = ('час', 'часа', 'часов')

	if 0 < hours < 1:
		return words[1]

	last_two_digits = hours % 100
	tens = last_two_digits // 10
	ones = last_two_digits % 10

	if tens == 1:
		return words[2]
	if ones == 1:
		return words[0]
	if 2 <= ones <= 4:
		return words[1]
	return words[2]


new_time_converter = lambda new_time: new_time if new_time not in range(0, 10) else f'0{new_time}'
insert_value_to_google_sheets = lambda sheet, value: sheet.append_table(value)