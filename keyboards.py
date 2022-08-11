from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def send_keyboard(user_times) -> ReplyKeyboardMarkup:
	"""
	Функция создает клавиатуру для пользователей на основании времени для уведомлений из базы данных для конкретного
	пользователя
				Параметры:
					user_times (tuple): Кортеж времен для уведомлений конкретного пользователя
	"""

	times1 = KeyboardButton(f'🕐 {user_times.time1[1:]}')
	times2 = KeyboardButton(f'🕑 {user_times.time2[1:]}')
	times3 = KeyboardButton(f'🕒 {user_times.time3[1:]}')
	times4 = KeyboardButton(f'🕓 {user_times.time4[1:]}')
	cancel = KeyboardButton('Отмена')
	time_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
	time_keyboard.row(times1, times2).row(times3, times4).add(cancel)
	return time_keyboard


report = KeyboardButton('Составить отчет!')
last_reports = KeyboardButton('Посмотреть прошлые отчеты')
change_time = KeyboardButton('Изменить время для уведомлений')
change_user_name = KeyboardButton('Изменить имя пользователя')

main_keyboard_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard_menu.row(report, last_reports).row(change_time, change_user_name)

go_back = KeyboardButton('Назад')
check_last = KeyboardButton('Посмотреть введенные значения')
cancel = KeyboardButton('Отмена')
restart = KeyboardButton('Начать сначала')

back_keyboard_menu = ReplyKeyboardMarkup(resize_keyboard=True)
back_keyboard_menu.row(go_back, check_last).row(cancel, restart)

report_start_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
report_start_keyboard.add(cancel)

yes = KeyboardButton('Да')
no = KeyboardButton('Нет')

yesorno_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
yesorno_keyboard.row(yes, no).add(cancel)

yesorno_keyboard_cancel_out = ReplyKeyboardMarkup(resize_keyboard=True)
yesorno_keyboard_cancel_out.row(yes, no)

change_report_time = KeyboardButton('Изменить время, до которого необходимо сдать отчет')

change_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
change_keyboard.add(change_report_time)