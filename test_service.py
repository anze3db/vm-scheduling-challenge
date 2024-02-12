import datetime as dt

from service import Exam, VmSchedule, get_vm_create_schedule


def test_get_vm_create_schedule_empty():
    assert get_vm_create_schedule([]) == []


def test_get_vm_create_schedule_zero_students():
    assert (
        get_vm_create_schedule(
            [
                Exam(
                    1,
                    "Math",
                    dt.datetime(2024, 2, 12, 9, 10),
                    dt.datetime(2024, 2, 12, 10, 10),
                    0,
                )
            ]
        )
        == []
    )


def test_get_vm_create_schedule_one_exam():
    exam = Exam(
        1,
        "Math",
        dt.datetime(2024, 2, 12, 9, 10),
        dt.datetime(2024, 2, 12, 10, 10),
        2400,
    )
    assert get_vm_create_schedule([exam]) == [
        VmSchedule(
            dt.datetime(2024, 2, 12, 5, 10),
            exam,
        )
    ]


def test_get_vm_create_schedule_no_overlap():
    exam1 = Exam(
        1,
        "Math",
        dt.datetime(2024, 2, 12, 9, 10),
        dt.datetime(2024, 2, 12, 10, 10),
        2400,
    )
    exam2 = Exam(
        2,
        "History",
        dt.datetime(2024, 2, 12, 14, 10),
        dt.datetime(2024, 2, 12, 15, 10),
        2400,
    )
    assert get_vm_create_schedule([exam2, exam1]) == [
        VmSchedule(
            dt.datetime(2024, 2, 12, 5, 10),
            exam1,
        ),
        VmSchedule(
            dt.datetime(2024, 2, 12, 10, 10),
            exam2,
        ),
    ]


def test_get_vm_create_schedule_not_sorted():
    exam1 = Exam(
        1,
        "Math",
        dt.datetime(2024, 2, 12, 9, 10),
        dt.datetime(2024, 2, 12, 10, 10),
        2400,
    )
    exam2 = Exam(
        2,
        "History",
        dt.datetime(2024, 2, 12, 14, 10),
        dt.datetime(2024, 2, 12, 15, 10),
        2400,
    )
    assert get_vm_create_schedule([exam1, exam2]) == [
        VmSchedule(
            dt.datetime(2024, 2, 12, 5, 10),
            exam1,
        ),
        VmSchedule(
            dt.datetime(2024, 2, 12, 10, 10),
            exam2,
        ),
    ]


def test_get_vm_create_schedule_overlap():
    exam1 = Exam(
        1,
        "Math",
        dt.datetime(2024, 2, 12, 9, 10),
        dt.datetime(2024, 2, 12, 10, 10),
        2400,
    )
    exam2 = Exam(
        2,
        "History",
        dt.datetime(2024, 2, 12, 10, 10),
        dt.datetime(2024, 2, 12, 11, 10),
        2400,
    )
    assert get_vm_create_schedule([exam1, exam2]) == [
        VmSchedule(
            dt.datetime(2024, 2, 12, 2, 10),
            exam1,
        ),
        VmSchedule(
            dt.datetime(2024, 2, 12, 6, 10),
            exam2,
        ),
    ]


def test_get_create_schedule_multiple_overlap():
    exam1 = Exam(
        1,
        "Math",
        dt.datetime(2024, 2, 12, 9, 10),
        dt.datetime(2024, 2, 12, 10, 10),
        2400,
    )
    exam2 = Exam(
        2,
        "History",
        dt.datetime(2024, 2, 12, 10, 10),
        dt.datetime(2024, 2, 12, 11, 10),
        2400,
    )
    exam3 = Exam(
        3,
        "Calculus",
        dt.datetime(2024, 2, 12, 13, 10),
        dt.datetime(2024, 2, 12, 14, 10),
        2400,
    )
    assert get_vm_create_schedule([exam1, exam2, exam3]) == [
        VmSchedule(
            dt.datetime(2024, 2, 12, 1, 10),
            exam1,
        ),
        VmSchedule(
            dt.datetime(2024, 2, 12, 5, 10),
            exam2,
        ),
        VmSchedule(
            dt.datetime(2024, 2, 12, 9, 10),
            exam3,
        ),
    ]


def test_get_create_schedule_multiple_overlap_an_no_overlap():
    exam1 = Exam(
        1,
        "Math",
        dt.datetime(2024, 2, 12, 8, 10),
        dt.datetime(2024, 2, 12, 9, 10),
        2400,
    )
    exam2 = Exam(
        2,
        "History",
        dt.datetime(2024, 2, 12, 10, 10),
        dt.datetime(2024, 2, 12, 11, 10),
        600,
    )
    exam3 = Exam(
        3,
        "Calculus",
        dt.datetime(2024, 2, 12, 13, 10),
        dt.datetime(2024, 2, 12, 14, 10),
        2400,
    )
    assert get_vm_create_schedule([exam1, exam2, exam3]) == [
        VmSchedule(
            dt.datetime(2024, 2, 12, 4, 10),
            exam1,
        ),
        VmSchedule(
            dt.datetime(2024, 2, 12, 8, 10),
            exam2,
        ),
        VmSchedule(
            dt.datetime(2024, 2, 12, 9, 10),
            exam3,
        ),
    ]
