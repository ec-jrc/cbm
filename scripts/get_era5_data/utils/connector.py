import psycopg2
from utils import config


def connect(db_name):
    try:
        return psycopg2.connect(
            host=config.host,
            port=config.port,
            dbname=db_name,
            user=config.user,
            password=config.password
        )

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)


# if __name__ == "__main__":
#     db = connect('outreach')
