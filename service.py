import asyncio
import datetime as dt
import itertools
import logging
import uuid
from dataclasses import dataclass

import psycopg

from api import CloudAPI

logging.basicConfig(level="INFO")


@dataclass
class Exam:
    id: int
    name: str
    start: dt.datetime
    end: dt.datetime
    students: int


@dataclass
class CreatedVM:
    id: uuid.UUID
    exam: Exam


@dataclass
class VmSchedule:
    start: dt.datetime
    exam: Exam


async def get_exams() -> list[Exam]:
    async with await psycopg.AsyncConnection.connect(
        "dbname=postgres user=postgres"
    ) as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(
                """SELECT id, name, start, "end", students FROM exam order by start desc;"""
            )
            return [Exam(*exam) for exam in await acur.fetchall()]


def get_vm_create_schedule(exams: list[Exam]) -> list[VmSchedule]:
    exam_schedule: list[VmSchedule] = []
    for exam in sorted(exams, key=lambda x: x.start, reverse=True):
        if exam.students < 1:
            # nothing to schedule
            continue
        if not exam_schedule:
            # No overlapping exam so set max date that should never be greater than any exam start
            prev_start_creating_at = dt.datetime.max
        else:
            prev_start_creating_at = exam_schedule[0].start

        time_to_create = exam.students * 6  # Create 1 VM in 6 seconds
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


async def create_vms(
    schedule: list[VmSchedule], api: CloudAPI, created_vms: list[CreatedVM]
):
    while schedule:
        next_schedule = schedule.pop(0)
        if next_schedule.start > dt.datetime.now():
            diff = next_schedule.start - dt.datetime.now()
            logging.info(
                "VM Starter sleeping for %s",
                diff,
            )
            await asyncio.sleep(diff.seconds)

        for triplet in itertools.batched(range(next_schedule.exam.students), 3):
            results = await asyncio.gather(*[api.start() for _ in triplet])
            for result in results:
                created_vms.append(CreatedVM(result, next_schedule.exam))

            await asyncio.sleep(1)


async def end_vms(
    schedule: list[VmSchedule], api: CloudAPI, created_vms: list[CreatedVM]
):
    while schedule or created_vms:
        now = dt.datetime.now()
        tasks_to_end = [vm for vm in created_vms if vm.exam.end < now]
        if not tasks_to_end:
            await asyncio.sleep(1)
            continue

        for vm_triplets in itertools.batched(tasks_to_end, 3):
            await asyncio.gather(*[api.end(vm.id) for vm in vm_triplets])
            for vm in vm_triplets:
                created_vms.remove(vm)
            await asyncio.sleep(1)


async def start_service():
    logging.info("Starting service")
    api = CloudAPI()
    created_vms: list[CreatedVM] = []
    logging.info("Fetching exams")
    exams = await get_exams()
    logging.info("Calculating schedule")
    vm_create_schedule = get_vm_create_schedule(exams)
    logging.info(
        "Create Schedule:\n    Date                ID\n%s",
        "\n".join(f"    {s.start} {s.exam.id}" for s in vm_create_schedule),
    )

    logging.info("Starting background tasks")
    background_tasks = set(
        [
            create_vms(vm_create_schedule, api, created_vms),
            end_vms(vm_create_schedule, api, created_vms),
        ]
    )
    logging.info("Service started")
    try:
        await asyncio.gather(
            *background_tasks,
        )
    except KeyboardInterrupt:
        asyncio.gather(*background_tasks).cancel()


if __name__ == "__main__":
    try:
        asyncio.run(start_service())
    except KeyboardInterrupt:
        logging.info("Shutting down")
