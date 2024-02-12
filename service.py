import asyncio
import datetime as dt
import itertools
import logging
import os
import uuid
from dataclasses import dataclass

import psycopg

from api import CloudAPI
from init_db import CONNECTION_STR

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO").upper())


@dataclass
class Exam:
    id: int
    name: str
    start: dt.datetime
    end: dt.datetime
    students: int
    vms_created: int = 0


@dataclass
class CreatedVM:
    id: uuid.UUID
    exam: Exam


@dataclass
class VmSchedule:
    start: dt.datetime
    exam: Exam


async def get_exams(aconn: psycopg.AsyncConnection) -> list[Exam]:
    async with aconn.cursor() as acur:
        await acur.execute(
            """SELECT id, name, start, "end", students, (SELECT COUNT(*) FROM exam_vm AS evm WHERE evm.exam_id = e.id) 
               FROM exam AS e 
               ORDER BY start DESC;"""
        )
        return [Exam(*exam) for exam in await acur.fetchall()]


async def create_vms(aconn: psycopg.AsyncConnection, created_vms: list[CreatedVM]):
    async with aconn.cursor() as acur:
        exam_vms = [(vm.id, vm.exam.id) for vm in created_vms]
        await acur.executemany(
            """INSERT INTO exam_vm ("id", "exam_id") VALUES(%s, %s);""",
            exam_vms,
        )


async def end_vms(aconn: psycopg.AsyncConnection, vms_to_end: list[uuid.UUID]):
    async with aconn.cursor() as acur:
        await acur.execute(
            """UPDATE exam_vm SET ended = NOW() WHERE id = any(%s);""",
            ([(vm) for vm in vms_to_end],),
        )


async def get_vms_to_end(aconn: psycopg.AsyncConnection) -> list[uuid.UUID]:
    async with aconn.cursor() as acur:
        await acur.execute(
            """SELECT evm.id FROM exam_vm AS evm
               JOIN exam e ON e.id = evm.exam_id
               WHERE e.end < NOW() AND evm.ended IS NULL;"""
        )
        return [vm_uuid for (vm_uuid,) in await acur.fetchall()]


def get_vm_create_schedule(exams: list[Exam]) -> list[VmSchedule]:
    exam_schedule: list[VmSchedule] = []
    for exam in sorted(exams, key=lambda x: x.start, reverse=True):
        if exam.students < 1:
            # nothing to schedule
            continue
        if exam.students <= exam.vms_created:
            # all VMs already created
            continue
        if not exam_schedule:
            # No overlapping exam so set max date that should never be greater than any exam start
            prev_start_creating_at = dt.datetime.max
        else:
            prev_start_creating_at = exam_schedule[0].start

        time_to_create = (
            exam.students - exam.vms_created
        ) * 6  # Create 1 VM in 6 seconds
        if prev_start_creating_at < exam.start:
            # Overlapping exam so start creating VMs before the previous exam starts
            start_creating_at = prev_start_creating_at - dt.timedelta(
                seconds=time_to_create
            )
        else:
            # No overlapping exam so start creating VMs before the current exam starts
            start_creating_at = exam.start - dt.timedelta(seconds=time_to_create)

        exam_schedule.insert(0, VmSchedule(start_creating_at, exam))

    return exam_schedule


async def ender_service(api: CloudAPI, aconn: psycopg.AsyncConnection):
    while True:
        vms_to_end = await get_vms_to_end(aconn)
        if not vms_to_end:
            logging.info("Nothing to end")
            await asyncio.sleep(1)
            continue

        for batch in itertools.batched(vms_to_end, 3):
            await asyncio.gather(*[api.end(vm) for vm in batch])
            await end_vms(aconn, list(batch))
            await asyncio.sleep(1)


async def creator_service(api: CloudAPI, aconn: psycopg.AsyncConnection):
    while True:
        exams = await get_exams(aconn)
        schedule = get_vm_create_schedule(exams)
        if not schedule:
            logging.info("Nothing to schedule")
            await asyncio.sleep(1)
            continue

        logging.debug(
            "Create Schedule:\n    Date                ID\n%s",
            "\n".join(f"    {s.start} {s.exam.id}" for s in schedule),
        )

        next_schedule = schedule.pop(0)
        now = dt.datetime.now()
        if next_schedule.start > now:
            diff = next_schedule.start - now
            logging.info("Next action in %s, sleeping for 1s", diff)
            await asyncio.sleep(1)
            continue

        if next_schedule.start < now - dt.timedelta(seconds=6):
            logging.warning(
                "Cretion of VMs for exam %s is delayed", next_schedule.exam.id
            )

        for batch in itertools.batched(range(next_schedule.exam.students), 3):
            # Call api.create_vm concurrently up to 3 times
            results = await asyncio.gather(*[api.start() for _ in batch])
            # Create VMs in the DB
            await create_vms(
                aconn,
                [CreatedVM(result, next_schedule.exam) for result in results],
            )
            # Sleep for 1s to avoid rate limit
            await asyncio.sleep(1)


async def start_services():
    logging.info("Starting services")
    api = CloudAPI()
    aconn = await psycopg.AsyncConnection.connect(CONNECTION_STR, autocommit=True)
    logging.info("Starting background tasks")
    background_tasks = set(
        [
            creator_service(api, aconn),
            ender_service(api, aconn),
        ]
    )
    logging.info("Service started")
    try:
        await asyncio.gather(
            *background_tasks,
        )
    except KeyboardInterrupt:
        logging.info("Shutting down services")
        await aconn.close()
        asyncio.gather(*background_tasks).cancel()


if __name__ == "__main__":
    try:
        asyncio.run(start_services())
    except KeyboardInterrupt:
        logging.info("Shutting down")
