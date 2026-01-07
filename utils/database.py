
import aiomysql
from aiomysql import Connection

from config.settings import settings


_db_connection: Connection | None = None


def get_connection() -> Connection:
    if _db_connection is None:
        raise RuntimeError("Database connection not initialized. Call get_connection_pool() first.")
    return _db_connection


async def get_connection_pool() -> Connection:
    global _db_connection
    if _db_connection is None:
        db_url = settings.DATABASE_URL.replace("mysql://", "")

        credentials, host_info = db_url.split("@")
        user, password = credentials.split(":")
        host_port, database = host_info.split("/")
        host, port = host_port.split(":")

        _db_connection = await aiomysql.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            db=database,
            autocommit=True,
            connect_timeout=10,
        )
    return _db_connection


async def close_connection_pool() -> None:
    global _db_connection
    if _db_connection is not None:
        _db_connection.close()
        _db_connection = None
