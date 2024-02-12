import asyncio
import datetime as dt

import psycopg


def tomorrow(hour: int, minutes: int) -> dt.datetime:
    tomorrow = dt.date.today() + dt.timedelta(days=1)
    return dt.datetime(tomorrow.year, tomorrow.month, tomorrow.day, hour, minutes)


async def create_exam_table():
    async with await psycopg.AsyncConnection.connect(
        "dbname=postgres user=postgres"
    ) as aconn:
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
                    "exam_id" integer references exam(id)
                );

                TRUNCATE TABLE exam_vm, exam;
                """
            )
            exams = [
                ("Mathematics 101", tomorrow(10, 0), tomorrow(10, 45), 2400),
                ("Physics 101", tomorrow(10, 0), tomorrow(11, 0), 2400),
                ("Mathematics 201", tomorrow(11, 15), tomorrow(12, 0), 2400),
                ("Physics 102", tomorrow(12, 0), tomorrow(13, 0), 2400),
                ("History 102", tomorrow(15, 0), tomorrow(13, 0), 2400),
                ("History 103", tomorrow(17, 0), tomorrow(13, 0), 2400),
            ]
            await acur.executemany(
                """INSERT INTO exam ("name", "start", "end", "students") VALUES(%s, %s, %s, %s);""",
                exams,
            )


if __name__ == "__main__":
    asyncio.run(create_exam_table())
