from typing import Any

import asyncpg

from ..config.dependencies.postgres import DATABASE_ADDRESS


class PostgresConnection:
    __slots__ = ('connection',)

    async def __aenter__(self) -> asyncpg.Connection:
        self.connection = await asyncpg.connect(DATABASE_ADDRESS)
        return self.connection

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        await self.connection.close()
        return False


async def has_postgres_data(query: str, *args: Any) -> bool:
    """
    :param query: Str query to postgresql database
    :param args: Query arguments
    :return: False if result of query doesn't exist in database, else True
    """
    async with PostgresConnection() as connection:
        data = await connection.fetch(query, *args)
        return True if data else False
