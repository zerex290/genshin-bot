import asyncio

import asyncpg

from bot.src.config.dependencies.postgres import DATABASE_ADDRESS


async def create_pg_tables(connection: asyncpg.Connection):
    chats = (f"""
        CREATE TABLE chats (
            chat_id int PRIMARY KEY,
            ffa_commands boolean NOT NULL DEFAULT true
        );
    """)
    users = (f"""
        CREATE TABLE users (
            user_id int PRIMARY KEY,
            autocorrect boolean NOT NULL DEFAULT false,
            notes varchar(5) NOT NULL DEFAULT 'short',
            stats varchar(5) NOT NULL DEFAULT 'short',
            rewards varchar(5) NOT NULL DEFAULT 'short',
            diary varchar(5) NOT NULL DEFAULT 'short',
            CONSTRAINT is_user CHECK (user_id >= 0)
        );
    """)
    users_in_chats = (f"""
        CREATE TABLE users_in_chats (
            user_id int REFERENCES users(user_id),
            chat_id int REFERENCES chats(chat_id),
            resin_notifications boolean NOT NULL DEFAULT false,
            notification_number int NOT NULL DEFAULT 0,
            notification_value int NOT NULL DEFAULT 150,
            PRIMARY KEY (user_id, chat_id),
            CONSTRAINT notification_limit CHECK (notification_number <= 3),
            CONSTRAINT notification_value_threshold CHECK (notification_value >= 0 AND notification_value <= 160)
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
            date_added timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            times_used int  NOT NULL DEFAULT 0,
            message text,
            document_id text,
            audio_id text,
            photo_id text,
            edits_num int NOT NULL DEFAULT 0,
            date_edited timestamptz,
            editor_id int REFERENCES users(user_id),
            PRIMARY KEY (name, chat_id),
            CONSTRAINT correctness 
            CHECK (message IS NOT NULL OR document_id IS NOT NULL OR audio_id IS NOT NULL OR photo_id IS NOT NULL)
        );
    """)
    group_posts = (f"""
        CREATE TABLE group_posts (
            post_id int PRIMARY KEY,
            sankaku_post_id int UNIQUE,
            post_type varchar(8) NOT NULL,
            is_donut boolean NOT NULL
        );
    """)
    genshindb_shortcuts = (f"""
        CREATE TABLE genshindb_shortcuts (
            user_id int REFERENCES users(user_id),
            shortcut text,
            message text,
            photo_id varchar(40),
            keyboard text NOT NULL,
            PRIMARY KEY (user_id, shortcut)
        );
    """)
    genshindb_pages = (f"""
        CREATE TABLE genshindb_pages (
            name text,
            page int,
            photo_id text NOT NULL,
            token text NOT NULL,
            PRIMARY KEY (name, page),
            CONSTRAINT positive_page_value CHECK (page >= 0)
        );
    """)

    for table in list(locals().copy().values())[1:]:  #: Skip connection and table locals
        await connection.execute(table)


async def main():
    connection: asyncpg.Connection = await asyncpg.connect(DATABASE_ADDRESS)
    await create_pg_tables(connection)
    await connection.close()

asyncio.run(main())
