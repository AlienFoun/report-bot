from peewee import *
from configs.sql_config import host, user, password, db_name, autocommit

db = PostgresqlDatabase(
    host=host,
    user=user,
    password=password,
    database=db_name,
    autocommit=autocommit
)


class BaseModel(Model):
    id = PrimaryKeyField(unique=True)

    class Meta:
        database = db
        order_by = 'id'


class UserBase(BaseModel):
    user_id = BigIntegerField()
    time1 = TextField()
    time2 = TextField()
    time3 = TextField()
    time4 = TextField()
    isreporttoday = TextField()
    user_name = TextField()

    class Meta:
        db_table = 'user_base'


class UserReport(BaseModel):
    user_id = BigIntegerField()
    report_date = TextField()
    report_text = TextField()
    report_time = TextField()

    class Meta:
        db_table = 'user_reports'


class AdminConfig(BaseModel):
    report_time = TextField()

    class Meta:
        db_table = 'admin_configs'
