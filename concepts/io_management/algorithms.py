from typing import List, Dict, Any, Optional
from enum import Enum
import time
import threading
import queue

class IORequestType(Enum):
    READ = "read"
    WRITE = "write"

class IORequest:
    def __init__(self, request_id: str, process_id: str, request_type: IORequestType,
                 block_number: int, arrival_time: float = None):
        self.request_id = request_id
        self.process_id = process_id
        self.request_type = request_type
        self.block_number = block_number
        self.arrival_time = arrival_time or time.time()
        self.start_time = None
        self.completion_time = None
        self.waiting_time = 0
        self.service_time = 0

    def __repr__(self):
        return f"IORequest(id={self.request_id}, process={self.process_id}, type={self.request_type.value}, block={self.block_number})"

class DeviceDriver:
    def __init__(self, device_name: str, seek_time_per_track: float = 1.0,
                 rotational_latency: float = 0.5, transfer_time_per_block: float = 0.1):
        self.device_name = device_name
        self.seek_time_per_track = seek_time_per_track
        self.rotational_latency = rotational_latency
        self.transfer_time_per_block = transfer_time_per_block
        self.current_position = 0
        self.is_busy = False

    def calculate_seek_time(self, target_block: int) -> float:
        """Calculate seek time based on distance"""
        distance = abs(target_block - self.current_position)
        return distance * self.seek_time_per_track

    def process_request(self, request: IORequest) -> float:
        """Process an I/O request and return total time"""
        seek_time = self.calculate_seek_time(request.block_number)
        total_time = seek_time + self.rotational_latency + self.transfer_time_per_block

        request.start_time = time.time()
        time.sleep(total_time / 1000)  # Simulate processing time (scaled down)
        request.completion_time = time.time()

        self.current_position = request.block_number
        return total_time

class Buffer:
    def __init__(self, size: int):
        self.size = size
        self.data = []
        self.mutex = threading.Lock()
        self.not_empty = threading.Condition(self.mutex)
        self.not_full = threading.Condition(self.mutex)

    def put(self, item):
        with self.not_full:
            while len(self.data) >= self.size:
                self.not_full.wait()
            self.data.append(item)
            self.not_empty.notify()

    def get(self):
        with self.not_empty:
            while not self.data:
                self.not_empty.wait()
            item = self.data.pop(0)
            self.not_full.notify()
            return item

    def is_empty(self):
        return len(self.data) == 0

    def is_full(self):
        return len(self.data) >= self.size

class Spooler:
    def __init__(self, device_driver: DeviceDriver):
        self.device_driver = device_driver
        self.spool_queue = queue.Queue()
        self.is_running = False
        self.thread = None

    def start(self):
        self.is_running = True
        self.thread = threading.Thread(target=self._process_spool)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join()

    def add_request(self, request: IORequest):
        self.spool_queue.put(request)

    def _process_spool(self):
        while self.is_running:
            try:
                request = self.spool_queue.get(timeout=1)
                self.device_driver.process_request(request)
                self.spool_queue.task_done()
            except queue.Empty:
                continue

class InterruptController:
    def __init__(self):
        self.interrupts = queue.Queue()
        self.handlers = {}

    def register_handler(self, interrupt_type: str, handler):
        self.handlers[interrupt_type] = handler

    def trigger_interrupt(self, interrupt_type: str, data=None):
        self.interrupts.put((interrupt_type, data))

    def process_interrupts(self):
        while not self.interrupts.empty():
            interrupt_type, data = self.interrupts.get()
            if interrupt_type in self.handlers:
                self.handlers[interrupt_type](data)

class IOScheduler:
    @staticmethod
    def fcfs(requests: List[IORequest], device_driver: DeviceDriver) -> Dict[str, Any]:
        """First Come First Served I/O scheduling"""
        sorted_requests = sorted(requests, key=lambda r: r.arrival_time)
        current_time = 0
        schedule = []
        total_seek_time = 0
        total_waiting_time = 0

        for request in sorted_requests:
            if current_time < request.arrival_time:
                current_time = request.arrival_time

            seek_time = device_driver.calculate_seek_time(request.block_number)
            service_time = seek_time + device_driver.rotational_latency + device_driver.transfer_time_per_block

            request.start_time = current_time
            request.completion_time = current_time + service_time
            request.waiting_time = current_time - request.arrival_time
            request.service_time = service_time

            schedule.append({
                'request': request,
                'start_time': current_time,
                'completion_time': request.completion_time
            })

            total_seek_time += seek_time
            total_waiting_time += request.waiting_time
            current_time = request.completion_time
            device_driver.current_position = request.block_number

        avg_waiting_time = total_waiting_time / len(requests) if requests else 0
        avg_seek_time = total_seek_time / len(requests) if requests else 0

        return {
            'schedule': schedule,
            'total_seek_time': total_seek_time,
            'avg_waiting_time': avg_waiting_time,
            'avg_seek_time': avg_seek_time,
            'total_time': current_time
        }

    @staticmethod
    def sstf(requests: List[IORequest], device_driver: DeviceDriver) -> Dict[str, Any]:
        """Shortest Seek Time First I/O scheduling"""
        requests_copy = requests.copy()
        current_time = 0
        current_position = device_driver.current_position
        schedule = []
        total_seek_time = 0
        total_waiting_time = 0

        while requests_copy:
            # Find request with minimum seek time
            min_seek = float('inf')
            next_request = None

            for request in requests_copy:
                if request.arrival_time <= current_time:
                    seek_time = abs(request.block_number - current_position)
                    if seek_time < min_seek:
                        min_seek = seek_time
                        next_request = request

            if next_request is None:
                # No requests ready, advance time
                current_time += 1
                continue

            requests_copy.remove(next_request)

            service_time = min_seek + device_driver.rotational_latency + device_driver.transfer_time_per_block

            next_request.start_time = current_time
            next_request.completion_time = current_time + service_time
            next_request.waiting_time = current_time - next_request.arrival_time
            next_request.service_time = service_time

            schedule.append({
                'request': next_request,
                'start_time': current_time,
                'completion_time': next_request.completion_time
            })

            total_seek_time += min_seek
            total_waiting_time += next_request.waiting_time
            current_time = next_request.completion_time
            current_position = next_request.block_number

        avg_waiting_time = total_waiting_time / len(requests) if requests else 0
        avg_seek_time = total_seek_time / len(requests) if requests else 0

        return {
            'schedule': schedule,
            'total_seek_time': total_seek_time,
            'avg_waiting_time': avg_waiting_time,
            'avg_seek_time': avg_seek_time,
            'total_time': current_time
        }

    @staticmethod
    def scan(requests: List[IORequest], device_driver: DeviceDriver, direction: int = 1) -> Dict[str, Any]:
        """SCAN (Elevator) I/O scheduling"""
        requests_copy = sorted(requests, key=lambda r: r.arrival_time)
        current_time = 0
        current_position = device_driver.current_position
        schedule = []
        total_seek_time = 0
        total_waiting_time = 0
        pending_requests = []

        for request in requests_copy:
            # Add request to pending when it arrives
            while current_time < request.arrival_time:
                current_time += 1

            pending_requests.append(request)

            # Process pending requests using SCAN
            while pending_requests:
                # Get requests in current direction
                direction_requests = [r for r in pending_requests if
                                    (direction > 0 and r.block_number >= current_position) or
                                    (direction < 0 and r.block_number <= current_position)]

                if not direction_requests:
                    # Reverse direction
                    direction = -direction
                    continue

                # Sort by block number in current direction
                direction_requests.sort(key=lambda r: r.block_number, reverse=(direction < 0))

                next_request = direction_requests[0]
                pending_requests.remove(next_request)

                seek_time = abs(next_request.block_number - current_position)
                service_time = seek_time + device_driver.rotational_latency + device_driver.transfer_time_per_block

                next_request.start_time = current_time
                next_request.completion_time = current_time + service_time
                next_request.waiting_time = current_time - next_request.arrival_time
                next_request.service_time = service_time

                schedule.append({
                    'request': next_request,
                    'start_time': current_time,
                    'completion_time': next_request.completion_time
                })

                total_seek_time += seek_time
                total_waiting_time += next_request.waiting_time
                current_time = next_request.completion_time
                current_position = next_request.block_number

        avg_waiting_time = total_waiting_time / len(requests) if requests else 0
        avg_seek_time = total_seek_time / len(requests) if requests else 0

        return {
            'schedule': schedule,
            'total_seek_time': total_seek_time,
            'avg_waiting_time': avg_waiting_time,
            'avg_seek_time': avg_seek_time,
            'total_time': current_time
        }