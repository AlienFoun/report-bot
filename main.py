import datetime

from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from configs.bot_config import BOT_TOKEN
from keyboards import main_keyboard_menu, back_keyboard_menu, report_start_keyboard, send_keyboard, yesorno_keyboard, \
	yesorno_keyboard_cancel_out
from sql_funcs import SQLfuncs
from helper import time_converter, date_converter, send_to_admin_bot, new_time_converter, report_time_converter, \
	insert_value_to_google_sheets, open_sheet, translate_hours
from constants import emoji_tuple, time_tuple

bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

scheduler = AsyncIOScheduler()


async def on_startup(_):
	"""
	Функция запускается 1 раз вместе со стартом бота, получает значение времени, до которого необходимо сдать отчет
	и выставляет программе задачи:
		1) Запуск функции для возобновления отправки уведомлений
		2) Запуск функции корректировки времени корректировки времени для функции возобновления отправки уведомлений
		3) Выставляет уведомления каждому пользователю из базы данных
	"""
	report_time = SQLfuncs.get_report_time()
	# report_time = '18:00'
	hour, minute = report_time_converter(report_time)
	scheduler.add_job(resume_notify, 'cron', day_of_week='mon-fri', hour=hour, minute=minute, id='resume_notify')

	scheduler.add_job(return_report_param, 'cron', day_of_week='mon-fri', hour=0, minute=0, id='return_report_params')
	users_with_time = SQLfuncs.select_users_with_time()
	for user in users_with_time:
		for time in (user.time1, user.time2, user.time3, user.time4):
			emoji = time[0]
			hours, minutes = list(map(int, time[1:].split(':')))
			scheduler.add_job(send_notify, 'cron', day_of_week='mon-fri', args=(user.user_id,), hour=hours, minute=minutes,
							  id=f'{user.user_id}-{emoji}')


def create_jobs(user_id: int):
	"""
	Функция создает задачи на отправку уведомлений новому пользователю
	"""
	time_zip = list(zip(time_tuple, emoji_tuple))
	for time in time_zip:
		scheduler.add_job(send_notify, 'cron', day_of_week='mon-fri', args=(user_id,), hour=time[0], minute=0,
						  id=f'{user_id}-{time[1]}')


def return_report_param():
	"""
	Функция изменяет время запуска функции запуска уведомлений в соответствии со значением из базы данных
	"""
	report_time = SQLfuncs.get_report_time()
	# report_time = '19:00'
	hour, minute = report_time_converter(report_time)
	trigger = CronTrigger(hour=hour, minute=minute)
	scheduler.modify_job('resume_notify', trigger=trigger)
	SQLfuncs.set_default_report()


def stop_notify(user_id: int):
	"""
	Функция для остановки напоминаний для пользователя, который заполнил отчет
			Параметры:
					user_id (int): telegram-id пользователя, заполнившего отчет
	"""
	for job in range(4):
		scheduler.get_job(f'{user_id}-{emoji_tuple[job]}').pause()


def resume_notify():
	"""
	Функция для запуска напоминаний, если отчет не был заполнен вовремя
	"""
	user_ids = SQLfuncs.check_report()
	for user in user_ids:
		for job in range(4):
			scheduler.get_job(f'{user.user_id}-{emoji_tuple[job]}').resume()


async def send_notify(user_id):
	await bot.send_message(user_id, 'Вы еще не заполнили отчет!')


@dp.message_handler(commands='start')
async def say_hello(message: types.Message):
	"""
	Приветственная функция, в случае, если пользователь обратился к боту в 1 раз, просит его ввести его имя пользователя.
	Если пользователь обращается к боту не в первый раз и уже есть в базе, то просит его выбрать одно из действий.
	"""
	user_id = message["from"]["id"]

	if not SQLfuncs.check_user(user_id):
		await message.answer('Добро пожаловать! Введите, пожалуйста Ваше имя пользователя!')
		await SetUserName.waiting_for_name.set()
	else:
		await message.answer("Выберите действие: ", reply_markup=main_keyboard_menu)


class CreateReport(StatesGroup):  # Создание машины состояний для отправки отчета
	waiting_for_date = State()
	waiting_for_report_text = State()
	waiting_for_report_time = State()
	waiting_for_agree = State()


class ChangeTime(StatesGroup):  # Создание машины состояний для изменения времени уведомлений
	waiting_for_choose_time = State()
	waiting_for_time = State()
	waiting_for_agree = State()


class SetUserName(StatesGroup):  # Создание машины состояний для установки имени пользователя
	waiting_for_name = State()
	waiting_for_agree = State()


class ChangeUserName(StatesGroup):  # Создание машины состояний для изменения имени пользователя
	waiting_for_name = State()
	waiting_for_agree = State()


@dp.message_handler(Text(equals=['Составить отчет!', 'Посмотреть прошлые отчеты', 'Изменить время для уведомлений',
								 'Изменить имя пользователя']))
async def choose_action(message: types.Message):
	"""
	Функция обрабатывает выбор действий от пользователя, а также вызывает функцию для получения настроек времени
	уведомлений пользователя, чтобы потом отобразить их в клавиатуре.
	В случае выбора пользователем действия "Составить отчет" - машина состояний для отправки отчета переходит в
	режим ожидания ввода даты отчета
	В случае выбора пользователем действия "Изменить время для уведомлений" - машина состояний для изменения времени
	уведомлений переходит в режим ожидания выбора времени, которое пользователь хочет изменить
				Параметры:
					message (types.Message): сообщение от пользователя в Telegram
	"""
	user_id = message["from"]["id"]
	user_times = SQLfuncs.get_user_time(user_id)

	if message.text == 'Составить отчет!':
		await message.answer('Введите дату отчета', reply_markup=report_start_keyboard)
		await CreateReport.waiting_for_date.set()

	elif message.text == 'Посмотреть прошлые отчеты':
		await message.answer('В разработке...')

	elif message.text == 'Изменить время для уведомлений':
		await message.answer('Выберите время, которое хотите изменить', reply_markup=send_keyboard(user_times))
		await ChangeTime.waiting_for_choose_time.set()

	elif message.text == 'Изменить имя пользователя':
		await message.answer('Введите новое имя пользователя', reply_markup=report_start_keyboard)
		await ChangeUserName.waiting_for_name.set()
# ------- Функции для установки имени пользователя -------

@dp.message_handler(state=SetUserName.waiting_for_name)
async def name_entered(message: types.Message, state: FSMContext):
	"""
	Функция вызывается в случае если пользователь первый раз обратился к боту и ему необходимо установить свое имя
	пользователя, по окончанию выполнения функции, машина состояний переходит в режим ожидания подтверждения
	введенного имени пользователя.
				Параметры:
					message (types.Message): сообщение от пользователя в Telegram
					state (FSMContext): состояние машины состояний на данный момент
	"""
	await message.answer(f'Ваше имя пользователя: {message.text}.\nПодтвердить?',
						 reply_markup=yesorno_keyboard_cancel_out)
	await state.update_data(user_name=message.text)
	await SetUserName.next()


@dp.message_handler(state=SetUserName.waiting_for_agree)
async def agree_wait(message: types.Message, state: FSMContext):
	"""
	Функция вызывается после введения пользователем его имени пользователя, в случае если пользователь подтвердит
	установку имени пользователя, пользователь будет добавлен в базу данных, по окончанию выполнения функции,
	машина состояний будет закрыта. Функция так же выставляет задачи на отправку уведомлений данному пользователю.
				Параметры:
					message (types.Message): сообщение от пользователя в Telegram
					state (FSMContext): состояние машины состояний на данный момент
	"""
	user_id = message["from"]["id"]

	if message.text == 'Да':
		user_data = await state.get_data()
		SQLfuncs.add_user(user_id, user_data["user_name"])
		create_jobs(user_id)
		await message.answer("Добро пожаловать! Выберите действие: ", reply_markup=main_keyboard_menu)
		await state.finish()
	elif message.text == 'Нет':
		await message.answer('Введите, пожалуйста Ваше имя пользователя!')
		await SetUserName.previous()
	else:
		await message.answer('Не могу распознать ваше сообщение, пожалуйста, выберите ввод с клавиатуры')


# ------- Функции для изменения имени пользователя -------

@dp.message_handler(state=ChangeUserName.waiting_for_name)
async def name_entered(message: types.Message, state: FSMContext):
	"""
	Функция вызывается в случае если пользователь решил изменить свое имя пользователя,
	по окончанию выполнения функции, машина состояний переходит в режим ожидания подтверждения
	нового имени пользователя.
				Параметры:
					message (types.Message): сообщение от пользователя в Telegram
					state (FSMContext): состояние машины состояний на данный момент
	"""
	if message.text == 'Отмена':
		await message.answer('Изменение времени было прекращено. Выберите действие', reply_markup=main_keyboard_menu)
		await state.finish()
	else:
		await message.answer(f'Ваше новое имя пользователя: {message.text}. Подтвердить?',
							 reply_markup=yesorno_keyboard)
		await state.update_data(user_name=message.text)
		await ChangeUserName.next()


@dp.message_handler(state=ChangeUserName.waiting_for_agree)
async def agree_wait(message: types.Message, state: FSMContext):
	"""
	Функция вызывается после введения пользователем его имени пользователя, в случае если пользователь подтвердит
	изменение имени пользователя, новое имя пользователя будет добавлено в базу данных, а также будет отправлено
	уведомление об этом в Админ-бот, по окончанию выполнения функции, машина состояний будет закрыта.
				Параметры:
					message (types.Message): сообщение от пользователя в Telegram
					state (FSMContext): состояние машины состояний на данный момент
	"""
	user_id = message["from"]["id"]

	if message.text == 'Да':
		user_data = await state.get_data()
		old_user_name = SQLfuncs.check_user_name(user_id)
		SQLfuncs.update_user_name(user_id, user_data["user_name"])
		await message.answer("Ваше имя пользователя было успешно изменено", reply_markup=main_keyboard_menu)
		text_to_admin_bot = f'Пользователь с именем {old_user_name} изменил свое имя пользователя!\n' \
							f'Старое имя пользователя: {old_user_name}\n' \
							f'Новое имя пользователя: {user_data["user_name"]}'
		send_to_admin_bot(text_to_admin_bot)
		await state.finish()

	elif message.text == 'Нет':
		await message.answer('Введите, пожалуйста Ваше имя пользователя!')
		await SetUserName.previous()

	elif message.text == 'Отмена':
		await message.answer('Изменение имени было прекращено. Выберите действие', reply_markup=main_keyboard_menu)
		await state.finish()

	else:
		await message.answer('Не могу распознать ваше сообщение, пожалуйста, выберите ввод с клавиатуры')


# ------- Функции для изменения времени уведомлений -------


@dp.message_handler(state=ChangeTime.waiting_for_choose_time)
async def time_chosen(message: types.Message, state: FSMContext):
	"""
	Функция вызывается в случае выбора пользователем действия изменения времени уведомлений,
	по окончанию выполнения функции, машина состояний переходит в режим ожидания ввода нового времени для уведомлений.
				Параметры:
					message (types.Message): сообщение от пользователя в Telegram
					state (FSMContext): состояние машины состояний на данный момент
	"""
	if message.text == 'Отмена':
		await message.answer('Изменение времени было прекращено')
		await message.answer('Выберите действие', reply_markup=main_keyboard_menu)
		await state.finish()

	elif message.text[0] in emoji_tuple:
		await state.update_data(emoji=message.text[0])
		await state.update_data(previous_time=message.text[1:])
		await message.answer('Введите новое время в формате xx:xx')
		await ChangeTime.next()

	else:
		await message.answer('Некорректное время. Пожалуйста, выберите время с клавиатуры')


@dp.message_handler(state=ChangeTime.waiting_for_time)
async def time_chosen(message: types.Message, state: FSMContext):
	"""
	Функция вызывается после выбора пользователем времени, которое он хочет изменить, по окончанию выполнения функции,
	машина состояний переходит в режим ожидания подтверждения введенных данных
				Параметры:
					message (types.Message): сообщение от пользователя в Telegram
					state (FSMContext): состояние машины состояний на данный момент
	"""
	if message.text == 'Отмена':
		await message.answer('Изменение времени было прекращено')
		await state.finish()
	else:
		try:
			current_message_text = message.text.replace('.', ':')
			splited_message_text = current_message_text.split(':')
			hours, minutes = list(map(int, splited_message_text))
			await state.update_data(chosen_hour=hours)
			await state.update_data(chosen_minutes=minutes)
		except Exception:
			await message.answer('Вы ввели некорректное время. Введите время в формате xx:xx')
		else:
			minutes = new_time_converter(minutes)
			hours = new_time_converter(hours)
			await message.answer(f'Вы изменили время на {hours}:{minutes}. Подтвердить время?',
								 reply_markup=yesorno_keyboard)
			await ChangeTime.next()


@dp.message_handler(state=ChangeTime.waiting_for_agree)
async def agree_wait(message: types.Message, state: FSMContext):
	"""
	Функция вызывается после ввода пользователем нового времени для уведомлений, обновляет задачу уведомления
	пользователя, изменяя время срабатывания, а также вызывает функцию, которая изменяет время уведомления в базе данных
	Также функция отправляет сообщение об изменении времени в админ-бота и закрывает машину состояний
				Параметры:
					message (types.Message): сообщение от пользователя в Telegram
					state (FSMContext): состояние машины состояний на данный момент
	"""
	user_data = await state.get_data()
	user_id = message["from"]["id"]

	if message.text == 'Отмена':
		await message.answer('Изменение времени было прекращено')
		await state.finish()

	elif message.text == 'Да':
		minutes = new_time_converter(user_data["chosen_minutes"])
		hours = new_time_converter(user_data["chosen_hour"])

		trigger = CronTrigger(hour=int(hours), minute=int(minutes))
		scheduler.modify_job(f'{user_id}-{user_data["emoji"]}', trigger=trigger)

		SQLfuncs.change_user_time(user_id, user_data["emoji"], f'{user_data["emoji"]}{hours}:{minutes}')

		user_name = SQLfuncs.check_user_name(user_id)
		text_to_admin_bot = f'Пользователь {user_name} изменил время для уведомлений:\n' \
							f'Старое время для уведомлений: {user_data["previous_time"]}\n' \
							f'Новое время для уведомлений: {hours}:{minutes}'

		send_to_admin_bot(text_to_admin_bot)

		await message.answer('Время успешно изменено!')
		await message.answer('Выберите действие', reply_markup=main_keyboard_menu)
		await state.finish()

	elif message.text == 'Нет':
		await message.answer('Введите новое время')
		await ChangeTime.previous()
# ------- Функции для создания отчета -------

@dp.message_handler(state=CreateReport.waiting_for_date)
async def report_chosen(message: types.Message, state: FSMContext):
	"""
	Функция вызывается в случае выбора пользователем действия составления отчета, а также вызывает функцию, которая
	приводит введенную дату к единому формату, по окончанию выполнения функции, машина состояний переходит в
	режим ожидания ввода текста отчета.
				Параметры:
					message (types.Message): сообщение от пользователя в Telegram
					state (FSMContext): состояние машины состояний на данный момент
	"""
	if message.text == 'Отмена':
		await state.finish()
		await message.answer("Выберите действие: ", reply_markup=main_keyboard_menu)

	else:
		current_date = date_converter(message.text)
		await state.update_data(chosen_date=current_date)
		await CreateReport.next()
		await message.answer('Введите текст отчета', reply_markup=back_keyboard_menu)


@dp.message_handler(state=CreateReport.waiting_for_report_text)
async def text_chosen(message: types.Message, state: FSMContext):
	"""
	Функция вызывается после ввода пользователем даты отчета, по окончанию выполнения функции,
	машина состояний переходит в режим ожидания ввода времени, потраченого на выполнение задач из отчета
				Параметры:
					message (types.Message): сообщение от пользователя в Telegram
					state (FSMContext): состояние машины состояний на данный момент
	"""
	user_data = await state.get_data()

	if message.text == 'Назад':
		await message.answer(f'Вы ввели: {user_data["chosen_date"]}. Введите новую дату.')
		await CreateReport.previous()

	elif message.text == 'Посмотреть введенные значения':
		await message.answer(f'Дата: {user_data["chosen_date"]}')

	elif message.text == 'Отмена':
		await state.finish()
		await message.answer("Выберите действие: ", reply_markup=main_keyboard_menu)

	elif message.text == 'Начать сначала':
		await message.answer('Введите дату отчета', reply_markup=report_start_keyboard)
		await CreateReport.first()

	else:
		await state.update_data(chosen_text=message.text)
		await message.answer('Введите сколько времени было потрачено (в часах)')
		await CreateReport.next()


@dp.message_handler(state=CreateReport.waiting_for_report_time)
async def report_time_choose(message: types.Message, state: FSMContext):
	"""
	Функция вызывается после ввода пользователем времени, потраченого на выполнение задач из отчета,
	по окончанию выполнения функции, машина состояний переходит в режим ожидания подтверждения введенной информации.
				Параметры:
					message (types.Message): сообщение от пользователя в Telegram
					state (FSMContext): состояние машины состояний на данный момент
	"""
	user_data = await state.get_data()

	if message.text == 'Назад':
		await message.answer(f'Вы ввели: {user_data["chosen_text"]}. Введите новый текст.')
		await CreateReport.previous()

	elif message.text == 'Посмотреть введенные значения':
		await message.answer(f'Дата: {user_data["chosen_date"]}\n'
							 f'Текст: {user_data["chosen_text"]}')

	elif message.text == 'Начать сначала':
		await message.answer('Введите дату отчета', reply_markup=report_start_keyboard)
		await CreateReport.first()

	elif message.text == 'Отмена':
		await state.finish()
		await message.answer("Выберите действие: ", reply_markup=main_keyboard_menu)

	else:
		await message.answer(f'Ваш отчет:\n'
							 f'Дата: {user_data["chosen_date"]}\n'
							 f'Текст: {user_data["chosen_text"]}.\n'
							 f'Затраченное время (в часах): {message.text}')
		await state.update_data(time_spent=message.text)
		await message.answer('Отправить отчет?', reply_markup=yesorno_keyboard)
		await CreateReport.next()


@dp.message_handler(state=CreateReport.waiting_for_agree)
async def report_time_choose(message: types.Message, state: FSMContext):
	"""
	Функция вызывается после подтвеждения пользователем введенных им данных, функция добавляет отчет пользователя в
	базу данных и дублирует информацию в google-таблицу, а также вызывает функцию, которая преобразует введенное
	пользователем потраченное на отчет время к единому формату.
	В случае, если пользователь оставил отчет за текущий день, эта информация заносится в базу и пользователю
	не приходят уведомления за данный отчет.
	В случае, если пользователь оставил отчет за прошедший день, то ему не будут приходить уведомления за прошлые дни
	Также функция отправляет сообщение об изменении времени в админ-бота и закрывает машину состояний
				Параметры:
					message (types.Message): сообщение от пользователя в Telegram
					state (FSMContext): состояние машины состояний на данный момент
	"""
	if message.text == 'Отмена':
		await state.finish()
		await message.answer("Выберите действие: ", reply_markup=main_keyboard_menu)

	elif message.text == 'Нет':
		await message.answer('Введите сколько времени было потрачено (в часах)')
		await CreateReport.previous()

	elif message.text == 'Да':
		user_data = await state.get_data()
		user_id = message["from"]["id"]
		today = datetime.date.today().strftime('%d.%m.%Y')

		if user_data['chosen_date'] == today:
			stop_notify(user_id)
			SQLfuncs.set_report(user_id)
		else:
			stop_notify(user_id)
		SQLfuncs.add_report(user_id, user_data['chosen_date'], user_data['chosen_text'], user_data['time_spent'])
		await message.answer('Ваш отчет успешно записан.', reply_markup=main_keyboard_menu)
		sh = open_sheet()
		user_name = SQLfuncs.check_user_name(user_id)
		insert_value_to_google_sheets(sh, [user_name, user_data['chosen_date'], user_data['chosen_text'],
										   time_converter(user_data["time_spent"])])

		hour = time_converter(user_data["time_spent"])

		words = translate_hours(hour)

		text_to_admin_bot = f'Пользователь {user_name} оставил отчет:\n' \
							f'{user_data["chosen_date"]}\n' \
							f'{user_data["chosen_text"]}.\n' \
							f'Итого: {hour} {words}'

		send_to_admin_bot(text_to_admin_bot)

		await state.finish()


if __name__ == '__main__':
	scheduler.start()
	executor.start_polling(dp, on_startup=on_startup)