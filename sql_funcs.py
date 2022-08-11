from models import *

with db:
    db.create_tables([UserBase, UserReport, AdminConfig])


class SQLfuncs:

    @staticmethod
    def check_user(user_id: int) -> bool:
        """
		Функция проверяет, находится ли пользователь в базе данных на данный момент
				Параметры:
					user_id (int): Telegram-id пользователя
				Возвращаемое значение:
					True/False (bool): Информация о том, находится ли пользователь в базе данных
		"""
        rows = UserBase.select(UserBase.user_id).where(UserBase.user_id == user_id)
        for row in rows:
            if user_id == row.user_id:
                return True
        return False

    @staticmethod
    def add_user(user_id: int, user_name: str):
        """
		Функция добавляет пользователя в базу данных
				Параметры:
					user_id (int): Telegram-id пользователя
		"""
        UserBase.create(user_id=user_id, time1='🕐20:00', time2='🕑22:00', time3='🕒07:00', time4='🕓09:00',
                        isreporttoday='-', user_name=user_name)

    @staticmethod
    def select_users_with_time() -> list:
        """
		Функция получает информацию о всех пользователях из базы данных, а также о времени их уведомлений
				Возвращаемое значение:
					rows (list): Список пользователей и времен их уведомлений
		"""
        rows = UserBase.select(UserBase.user_id, UserBase.time1, UserBase.time2, UserBase.time3, UserBase.time4)
        return rows

    @staticmethod
    def get_user_time(user_id: int) -> tuple:
        """
		Функция получает информацию о всех временах уведомлений для конкретного пользователя
				Параметры:
					user_id (int): Telegram-id пользователя
				Возвращаемое значение:
					rows (tuple): Кортеж времен уведомлений для конкретного пользователя
		"""
        rows = UserBase.get(UserBase.user_id == user_id)
        return rows

    @staticmethod
    def change_user_time(user_id: int, emoji: str, time: str):
        """
		Функция изменяет конкретное время для уведомлений в базе данных для конкретного пользователя
				Параметры:
					user_id (int): Telegram-id пользователя
					emoji (str): Эмоджи, благодаря которому определяется, какое время будет изменено
					time (str): Новое время для уведомлений
		"""
        data = {
            '🕐': UserBase.update(time1=time),
            '🕑': UserBase.update(time2=time),
            '🕒': UserBase.update(time3=time),
            '🕓': UserBase.update(time4=time)
        }
        data[emoji].where(UserBase.user_id == user_id).execute()

    @staticmethod
    def get_report_time() -> str:
        """
		Функция-буфер, которая проверяет, есть ли информация о времени, до которого необходимо сдать отчет в базе данных
		В случае отсутствия такового, устанавливает его на стандартное значение - 19:00 и возвращает его
		В случае, если время есть в базе данных, то возвращает значение из базы
				Возвращаемое значение:
					report_time (str): Время, до которого необходимо сдать отчет
		"""
        try:
            rows = AdminConfig.get()
        except:
            rows = ()

        if rows != ():
            return rows.report_time
        AdminConfig.create(report_time='19:00')
        return '19:00'

    @staticmethod
    def set_report(user_id: int):
        """
		Функция устанавливает в базе данных информацию о том, что пользователь оставил отчет
				Параметры:
					user_id (int): Telegram-id пользователя
		"""
        UserBase.update(isreporttoday='+').where(UserBase.user_id == user_id).execute()

    @staticmethod
    def check_report() -> list:
        """
		Функция получает информацию из базы данных о всех пользователях, которые не оставили отчет за текущий день
		"""
        rows = UserBase.select(UserBase.user_id).where(UserBase.isreporttoday == '-')
        return rows

    @staticmethod
    def set_default_report():
        """
		Функция сбрасывает информацию о том, был ли загружен отчет за текущий день.
		"""
        UserBase.update(isreporttoday='-').execute()

    @staticmethod
    def add_report(user_id: int, date: str, text: str, time: str):
        """
		Функция добавляет в базу данных отчет пользователя
				Параметры:
					user_id (int): Telegram-id пользователя
					date (str): Дата, за которую оставлен отчет
					text (str): Текст отчета
					time (str): Время, потраченое на выполнение отчета
		"""
        UserReport.create(user_id=user_id, report_date=date, report_text=text, report_time=time)

    @staticmethod
    def update_user_name(user_id: int, user_name: str):
        """
		Функция обновляет в базе данных время, до которого необходимо сдать отчет
				Параметры:
					new_time (str): Новое время, до которого необходимо сдать отчет
		"""
        UserBase.update(user_name=user_name).where(UserBase.user_id == user_id).execute()

    @staticmethod
    def check_user_name(user_id: int) -> str:

        row = UserBase.get(UserBase.user_id == user_id)
        return row.user_name


def update_report_time(new_time: str):
    """
	Функция обновляет в базе данных время, до которого необходимо сдать отчет
			Параметры:
				new_time (str): Новое время, до которого необходимо сдать отчет
	"""
    AdminConfig.update(report_time=new_time).execute()
