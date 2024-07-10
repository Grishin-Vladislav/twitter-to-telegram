from os import getenv


def configure_variable(var_name, default=None):
    variable = getenv(var_name, default=default)

    if variable is None:  #dev-mode patch, needs soluion
        try:
            with open(".env", "r") as f:
                for line in f.readlines():
                    if line.startswith(var_name):
                        variable = line[line.find("=") + 1 :].strip("\n")
        except:
            raise ValueError(f"{var_name} variable is not set")

    return variable


BOT_TOKEN = configure_variable("BOT_TOKEN")
PG_NAME = configure_variable("PG_NAME")
PG_USER = configure_variable("PG_USER")
PG_PASS = configure_variable("PG_PASS")
DEV_MODE = configure_variable("DEV_MODE", False).lower() in ('true', '1', 't')
DB_URL = f"postgresql+psycopg2://{PG_USER}:{PG_PASS}@postgres_db/{PG_NAME}"
LOCAL_DB_URL = f"postgresql+psycopg2://{PG_USER}:{PG_PASS}@127.0.0.1:5432/{PG_NAME}"
