import asyncio
import logging
import time
import uuid

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class RateLimitExceededError(Exception):
    pass


ONE_SECOND = 1


def ratelimit(rate: int):
    calls: list[float] = []

    def decorator(func):
        def wrapper(*args, **kwargs):
            current_time = time.time()
            one_second_ago = current_time - ONE_SECOND

            # Remove calls older than 1 second:
            calls[:] = [call for call in calls if call > one_second_ago]

            if len(calls) >= rate:
                raise RateLimitExceededError()

            # Add current call:
            calls.append(current_time)

            # Call the wrapped funciton
            return func(*args, **kwargs)

        return wrapper

    return decorator


class CloudAPI:
    def __init__(self):
        self.vms_pending_queue: list[uuid.UUID] = []
        self.vms: list[uuid.UUID] = []

        # Start background task:
        asyncio.create_task(self.start_background_service())

    async def start_background_service(self):
        while True:
            if not self.vms_pending_queue:
                await asyncio.sleep(0)
                continue

            vm_id = self.vms_pending_queue.pop()
            await asyncio.sleep(6 * ONE_SECOND)
            self.vms.append(vm_id)
            logger.info("Started VM %s", vm_id)

    @ratelimit(3)
    async def start(self) -> uuid.UUID:
        vm_id = uuid.uuid4()
        logger.info("Starting VM %s", vm_id)
        self.vms_pending_queue.append(vm_id)
        return vm_id

    @ratelimit(3)
    async def end(self, vm_id: uuid.UUID):
        logger.info("Stopping VM %s", vm_id)
        self.vms.remove(vm_id)
