import asyncio
import logging
import os

import psycopg

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO").upper())

CONNECTION_STR = "dbname=postgres user=postgres"


async def create_tables():
    async with await psycopg.AsyncConnection.connect(CONNECTION_STR) as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(
                """
                CREATE TABLE IF NOT EXISTS exam (
                    "id" serial primary key,
                    "name" text,
                    "start" timestamp,
                    "end" timestamp,
                    "students" int,
                    PRIMARY KEY ("id")
                );

                -- Allocated VMs for each student
                CREATE TABLE IF NOT EXISTS exam_vm (
                    "id" uuid,
                    "exam_id" integer references exam(id),
                    created timestamp default now(),
                    ended timestamp default null
                );
                """
            )
    logging.info("Done!")


if __name__ == "__main__":
    asyncio.run(create_tables())
