# VM Scheduling challenge

## Set up

1. Set up the dev environment:

```console
# Install Python 3.11 or newer
python -m venv .venv  
. .venv/bin/activate
pip install -r requirements.txt
```

2. Create the database tables:

```
python init_db.py
```

3. Run the scheduling service:

```
python service.py
```

4. Run the tests

```
pytest
```

## Instructions


For a portion of the exams scheduled in Schoolyear's application, a remote virtual desktop is required per student.
Teachers plan these exams ahead of time, so we can allocate a VM for each student before the exam starts.
Each exam may have up to 2500 participants, and there may be dozens of such exams planned on any given day.

This challenge is about scheduling the allocation and deletion of VMs at a cloud provider, such that there are exactly enough VMs allocated at the start of each exam.

## What's given:

- An "exams" table in a Postgres database with columns: (id, name, start timestamp, end timestamp, #students).
  - You must create this table yourself.
- A mock API to create & delete VMs at the cloud provider.
  - API
    - `start() -> uuid | rate-limit-exceeded-error`
    - `stop(uuid) -> void | rate-limit-exceeded-error`
  - You may mock this API in your own code.
- VMs cannot be reused between exams or students. For each student, a fresh VM must be allocated.


## Rate limit

An important limitation in this challenge is the rate limits imposed by the cloud provider:
- Each API endpoint is limited to 3 requests per second. 
- VMs are allocated at a rate of 10 per minute, meaning that if you call `start()` more often, the request will succeed, but the VM will be allocated once this rate limit allows it again.

Example: you call the `start()` endpoint 27 times over a span of 9 seconds (3 per second).
- After 1 minute: 10 VMs available
- After 2 minutes: 20 VMs available
- After 2m54s: 27 VMs available

Of course, this gets more complicated with multiple exams overlapping.


## Challenge

Implement a service that connects to the postgres database and calls the `start()` and `stop()` endpoints, such that there are exactly enough VMs allocated at the start of each exam.



