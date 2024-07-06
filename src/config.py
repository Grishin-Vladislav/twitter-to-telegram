from os import getenv


def configure_variable(var_name, default=None):
    variable = getenv(var_name, default=default)

    if variable is None:
        raise ValueError(f"{var_name} variable is not set")

    return variable


BOT_TOKEN = configure_variable("BOT_TOKEN")

PG_NAME = configure_variable("PG_NAME")
PG_USER = configure_variable("PG_USER")
PG_PASS = configure_variable("PG_PASS")
