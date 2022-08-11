from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

from configs.admin_bot_config import ADMIN_BOT_TOKEN
from sql_funcs import update_report_time
from keyboards import change_keyboard, report_start_keyboard

bot = Bot(ADMIN_BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


class ChangeReportTime(StatesGroup):
	waiting_for_new_report_time = State()

@dp.message_handler(commands='start')
async def say_hello(message: types.Message):
	await message.answer('Это Админ бот', reply_markup=change_keyboard)


@dp.message_handler(Text(equals='Изменить время, до которого необходимо сдать отчет'))
async def change_time(message: types.Message):
	await message.answer('Введите новое время, до которого необходимо сдать отчет в формате xx:xx', reply_markup=report_start_keyboard)
	await ChangeReportTime.waiting_for_new_report_time.set()


@dp.message_handler(state=ChangeReportTime.waiting_for_new_report_time)
async def time_chosen(message: types.Message, state: FSMContext):
	if message.text == 'Отмена':
		await message.answer('Это Админ бот', reply_markup=change_keyboard)

	else:
		try:
			time = message.text.split(':')
			hour, minute = list(map(int, time))

		except Exception:
			await message.answer('Неверный формат')

		else:
			await message.answer('Новое время будет установлено после 00:00', reply_markup=change_keyboard)
			update_report_time(message.text)
			await state.finish()


if __name__ == '__main__':
	executor.start_polling(dp)