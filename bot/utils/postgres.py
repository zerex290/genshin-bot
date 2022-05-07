import asyncpg

from bot.config.dependencies.postgres import DATABASE_ADDRESS


class PostgresConnection:
    __slots__ = ('connection',)

    async def __aenter__(self) -> asyncpg.Connection:
        self.connection = await asyncpg.connect(DATABASE_ADDRESS)
        return self.connection

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        await self.connection.close()
        if exc_type:
            print(f"{exc_type}: {exc_val}")
            print(exc_tb)
        return True


async def has_postgres_data(query: str) -> bool:
    """
    :param query: Str query to postgresql database
    :return: False if result of query doesn't exist in database, else True
    """
    async with PostgresConnection() as connection:
        data = await connection.fetch(query)
        return True if data else False