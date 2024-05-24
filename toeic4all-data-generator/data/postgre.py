from sqlalchemy import create_engine
import data.settings as settings

postgre_host = settings.POSTGRE_HOST
postgre_port = settings.POSTGRE_PORT
postgre_username = settings.POSTGRE_USERNAME
postgre_password = settings.POSTGRE_PASSWORD
postgre_database_answer4all = settings.POSTGRE_DATABASE_1
postgre_database_answer4all_g_p5 = settings.POSTGRE_DATABASE_2

database_url_answer4all = f"postgresql://{postgre_username}:{postgre_password}@{postgre_host}:{postgre_port}/{postgre_database_answer4all}"
database_url_answer4all_g_p5 = f"postgresql://{postgre_username}:{postgre_password}@{postgre_host}:{postgre_port}/{postgre_database_answer4all_g_p5}"

postgre_engine_answer4all = create_engine(database_url_answer4all)
postgre_engine_answer4all_g_p5 = create_engine(database_url_answer4all_g_p5)
