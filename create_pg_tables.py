import asyncio
import asyncpg
from bot.config.dependencies.postgres import DATABASE_ADDRESS


async def create_pg_tables(connection):
    chats = (f"""
        CREATE TABLE chats (
            chat_id int PRIMARY KEY,
            member_count int NOT NULL,
            ffa_commands boolean NOT NULL DEFAULT true
        );
    """)
    users = (f"""
        CREATE TABLE users (
            user_id int PRIMARY KEY,
            first_name varchar(50) NOT NULL,
            last_name varchar(50) NOT NULL,
            autocorrect boolean NOT NULL DEFAULT false,
            CONSTRAINT is_user CHECK (user_id >= 0)
        );
    """)
    users_in_chats = (f"""
        CREATE TABLE users_in_chats (
            user_id int REFERENCES users(user_id),
            chat_id int REFERENCES chats(chat_id),
            join_date timestamptz NOT NULL,
            invited_by int NOT NULL,
            resin_notifications boolean NOT NULL DEFAULT false,
            PRIMARY KEY (user_id, chat_id)
        );
    """)
    genshin_accounts = (f"""
        CREATE TABLE genshin_accounts (
            user_id int PRIMARY KEY REFERENCES users(user_id),
            uid int NOT NULL,
            ltuid int NOT NULL,
            ltoken varchar(50) NOT NULL,
            cookie_token varchar(50) NOT NULL
        );
    """)
    custom_commands = (f"""
        CREATE TABLE custom_commands (
            name text,
            chat_id int NOT NULL REFERENCES chats(chat_id),
            creator_id int NOT NULL REFERENCES users(user_id),
            date_added timestamptz DEFAULT CURRENT_TIMESTAMP,
            times_used int  NOT NULL DEFAULT 0,
            message text,
            document_id varchar(40),
            audio_id varchar(40),
            has_photo boolean NOT NULL,
            PRIMARY KEY (name, chat_id),
            CONSTRAINT correctness 
            CHECK (message IS NOT NULL OR document_id IS NOT NULL OR audio_id IS NOT NULL OR has_photo IS TRUE)
        );
    """)
    group_posts = (f"""
        CREATE TABLE group_posts (
            post_id int PRIMARY KEY,
            sankaku_post_id int UNIQUE,
            danbooru_post_id int UNIQUE,
            post_type varchar(8) NOT NULL,
            is_donut boolean NOT NULL
        );
    """)

    for table in (chats, users, users_in_chats, genshin_accounts, custom_commands, group_posts):
        await connection.execute(table)


async def main():
    postgres = await asyncpg.connect(DATABASE_ADDRESS)
    await create_pg_tables(postgres)

asyncio.run(main())
