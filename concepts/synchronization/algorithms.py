from typing import List, Dict, Any, Optional
import threading
import time
import random
from enum import Enum

class ProcessState(Enum):
    READY = "ready"
    RUNNING = "running"
    WAITING = "waiting"
    TERMINATED = "terminated"

class SynchronizationProcess:
    def __init__(self, pid: str, name: str = ""):
        self.pid = pid
        self.name = name or pid
        self.state = ProcessState.READY
        self.waiting_for = None  # Resource or semaphore waiting for
        self.held_resources = []  # List of held resources
        self.program_counter = 0
        self.instructions = []  # List of operations

    def __repr__(self):
        return f"Process({self.pid}, state={self.state.value})"

class Semaphore:
    def __init__(self, value: int, name: str = ""):
        self.value = value
        self.name = name or f"Semaphore({value})"
        self.waiting_queue = []  # Processes waiting for this semaphore

    def wait(self, process: SynchronizationProcess) -> bool:
        """P operation - returns True if successful, False if blocked"""
        if self.value > 0:
            self.value -= 1
            return True
        else:
            self.waiting_queue.append(process)
            process.state = ProcessState.WAITING
            process.waiting_for = self.name
            return False

    def signal(self) -> Optional[SynchronizationProcess]:
        """V operation - returns unblocked process if any"""
        self.value += 1
        if self.waiting_queue:
            process = self.waiting_queue.pop(0)
            process.state = ProcessState.READY
            process.waiting_for = None
            return process
        return None

    def __repr__(self):
        return f"Semaphore({self.name}, value={self.value}, waiting={len(self.waiting_queue)})"

class Mutex:
    def __init__(self, name: str = ""):
        self.name = name or "Mutex"
        self.locked = False
        self.owner = None
        self.waiting_queue = []

    def lock(self, process: SynchronizationProcess) -> bool:
        """Try to acquire the mutex"""
        if not self.locked:
            self.locked = True
            self.owner = process
            return True
        else:
            self.waiting_queue.append(process)
            process.state = ProcessState.WAITING
            process.waiting_for = self.name
            return False

    def unlock(self) -> Optional[SynchronizationProcess]:
        """Release the mutex - returns unblocked process if any"""
        if self.locked:
            self.locked = False
            self.owner = None
            if self.waiting_queue:
                process = self.waiting_queue.pop(0)
                process.state = ProcessState.READY
                process.waiting_for = None
                return process
        return None

    def __repr__(self):
        owner_id = self.owner.pid if self.owner else "None"
        return f"Mutex({self.name}, locked={self.locked}, owner={owner_id}, waiting={len(self.waiting_queue)})"

class Monitor:
    def __init__(self, name: str = ""):
        self.name = name or "Monitor"
        self.mutex = Mutex(f"{name}_mutex")
        self.condition_vars = {}  # Dict of condition variables
        self.waiting_processes = {}  # Processes waiting on conditions

    def enter(self, process: SynchronizationProcess) -> bool:
        """Enter the monitor"""
        return self.mutex.lock(process)

    def exit(self):
        """Exit the monitor"""
        return self.mutex.unlock()

    def wait(self, condition_name: str, process: SynchronizationProcess):
        """Wait on a condition variable"""
        if condition_name not in self.condition_vars:
            self.condition_vars[condition_name] = []
        self.condition_vars[condition_name].append(process)
        if condition_name not in self.waiting_processes:
            self.waiting_processes[condition_name] = []
        self.waiting_processes[condition_name].append(process)
        process.state = ProcessState.WAITING
        process.waiting_for = f"{self.name}.{condition_name}"
        self.mutex.unlock()

    def signal(self, condition_name: str) -> Optional[SynchronizationProcess]:
        """Signal a condition variable"""
        if condition_name in self.condition_vars and self.condition_vars[condition_name]:
            process = self.condition_vars[condition_name].pop(0)
            self.waiting_processes[condition_name].remove(process)
            # Move to urgent queue (simplified - just make ready)
            process.state = ProcessState.READY
            process.waiting_for = None
            return process
        return None

class ProducerConsumer:
    """Classic Producer-Consumer problem"""
    def __init__(self, buffer_size: int = 5):
        self.buffer_size = buffer_size
        self.buffer = []
        self.mutex = Mutex("buffer_mutex")
        self.empty = Semaphore(buffer_size, "empty_slots")
        self.full = Semaphore(0, "full_slots")
        self.producer_count = 0
        self.consumer_count = 0

    def produce(self, producer: SynchronizationProcess, item: Any) -> Dict[str, Any]:
        """Producer operation"""
        steps = []

        # Wait for empty slot
        if not self.empty.wait(producer):
            steps.append(f"{producer.name}: Waiting for empty slot")
            return {'success': False, 'steps': steps, 'buffer': self.buffer.copy()}

        steps.append(f"{producer.name}: Got empty slot")

        # Enter critical section
        if not self.mutex.lock(producer):
            steps.append(f"{producer.name}: Waiting for buffer access")
            return {'success': False, 'steps': steps, 'buffer': self.buffer.copy()}

        steps.append(f"{producer.name}: Entered critical section")

        # Add item to buffer
        self.buffer.append(item)
        self.producer_count += 1
        steps.append(f"{producer.name}: Produced item {item}, buffer: {self.buffer}")

        # Exit critical section
        self.mutex.unlock()
        steps.append(f"{producer.name}: Exited critical section")

        # Signal full slot
        unblocked = self.full.signal()
        if unblocked:
            steps.append(f"{producer.name}: Signaled consumer {unblocked.name}")

        return {'success': True, 'steps': steps, 'buffer': self.buffer.copy()}

    def consume(self, consumer: SynchronizationProcess) -> Dict[str, Any]:
        """Consumer operation"""
        steps = []

        # Wait for full slot
        if not self.full.wait(consumer):
            steps.append(f"{consumer.name}: Waiting for full slot")
            return {'success': False, 'steps': steps, 'buffer': self.buffer.copy()}

        steps.append(f"{consumer.name}: Got full slot")

        # Enter critical section
        if not self.mutex.lock(consumer):
            steps.append(f"{consumer.name}: Waiting for buffer access")
            return {'success': False, 'steps': steps, 'buffer': self.buffer.copy()}

        steps.append(f"{consumer.name}: Entered critical section")

        # Remove item from buffer
        item = self.buffer.pop(0)
        self.consumer_count += 1
        steps.append(f"{consumer.name}: Consumed item {item}, buffer: {self.buffer}")

        # Exit critical section
        self.mutex.unlock()
        steps.append(f"{consumer.name}: Exited critical section")

        # Signal empty slot
        unblocked = self.empty.signal()
        if unblocked:
            steps.append(f"{consumer.name}: Signaled producer {unblocked.name}")

        return {'success': True, 'steps': steps, 'buffer': self.buffer.copy()}

class DiningPhilosophers:
    """Classic Dining Philosophers problem"""
    def __init__(self, num_philosophers: int = 5):
        self.num_philosophers = num_philosophers
        self.philosophers = [SynchronizationProcess(f"P{i}", f"Philosopher {i}") for i in range(num_philosophers)]
        self.chopsticks = [Mutex(f"Chopstick {i}") for i in range(num_philosophers)]
        self.states = ["thinking"] * num_philosophers  # thinking, hungry, eating

    def pickup_chopsticks(self, philosopher_id: int) -> Dict[str, Any]:
        """Philosopher tries to pick up chopsticks"""
        steps = []
        philosopher = self.philosophers[philosopher_id]

        self.states[philosopher_id] = "hungry"
        steps.append(f"{philosopher.name}: Became hungry")

        # Try to pick up left chopstick
        left = philosopher_id
        if not self.chopsticks[left].lock(philosopher):
            steps.append(f"{philosopher.name}: Waiting for left chopstick")
            return {'success': False, 'steps': steps, 'states': self.states.copy()}

        steps.append(f"{philosopher.name}: Picked up left chopstick")

        # Try to pick up right chopstick
        right = (philosopher_id + 1) % self.num_philosophers
        if not self.chopsticks[right].lock(philosopher):
            # Put down left chopstick
            self.chopsticks[left].unlock()
            steps.append(f"{philosopher.name}: Waiting for right chopstick, put down left")
            return {'success': False, 'steps': steps, 'states': self.states.copy()}

        steps.append(f"{philosopher.name}: Picked up right chopstick")
        self.states[philosopher_id] = "eating"
        steps.append(f"{philosopher.name}: Started eating")

        return {'success': True, 'steps': steps, 'states': self.states.copy()}

    def putdown_chopsticks(self, philosopher_id: int) -> Dict[str, Any]:
        """Philosopher puts down chopsticks"""
        steps = []
        philosopher = self.philosophers[philosopher_id]

        left = philosopher_id
        right = (philosopher_id + 1) % self.num_philosophers

        # Put down chopsticks
        unblocked_left = self.chopsticks[left].unlock()
        unblocked_right = self.chopsticks[right].unlock()

        self.states[philosopher_id] = "thinking"
        steps.append(f"{philosopher.name}: Put down chopsticks and started thinking")

        if unblocked_left:
            steps.append(f"{philosopher.name}: Unblocked {unblocked_left.name} for left chopstick")
        if unblocked_right:
            steps.append(f"{philosopher.name}: Unblocked {unblocked_right.name} for right chopstick")

        return {'success': True, 'steps': steps, 'states': self.states.copy()}

class ReadersWriters:
    """Classic Readers-Writers problem"""
    def __init__(self):
        self.mutex = Mutex("read_write_mutex")
        self.read_count_mutex = Mutex("read_count_mutex")
        self.read_count = 0
        self.writer_active = False
        self.readers = []
        self.writers = []

    def start_read(self, reader: SynchronizationProcess) -> Dict[str, Any]:
        """Reader tries to start reading"""
        steps = []

        # Enter read count critical section
        if not self.read_count_mutex.lock(reader):
            steps.append(f"{reader.name}: Waiting to update read count")
            return {'success': False, 'steps': steps, 'read_count': self.read_count, 'writer_active': self.writer_active}

        steps.append(f"{reader.name}: Entered read count section")

        self.read_count += 1
        steps.append(f"{reader.name}: Incremented read count to {self.read_count}")

        if self.read_count == 1:
            # First reader - try to get write lock
            self.read_count_mutex.unlock()
            steps.append(f"{reader.name}: Exited read count section")

            if not self.mutex.lock(reader):
                # Undo read count increment
                self.read_count -= 1
                steps.append(f"{reader.name}: Waiting for write lock, decremented read count")
                return {'success': False, 'steps': steps, 'read_count': self.read_count, 'writer_active': self.writer_active}

            self.writer_active = False
            steps.append(f"{reader.name}: Acquired write lock for reading")
        else:
            self.read_count_mutex.unlock()
            steps.append(f"{reader.name}: Exited read count section")

        steps.append(f"{reader.name}: Started reading")
        return {'success': True, 'steps': steps, 'read_count': self.read_count, 'writer_active': self.writer_active}

    def end_read(self, reader: SynchronizationProcess) -> Dict[str, Any]:
        """Reader finishes reading"""
        steps = []

        # Enter read count critical section
        if not self.read_count_mutex.lock(reader):
            steps.append(f"{reader.name}: Waiting to update read count")
            return {'success': False, 'steps': steps, 'read_count': self.read_count, 'writer_active': self.writer_active}

        steps.append(f"{reader.name}: Entered read count section")

        self.read_count -= 1
        steps.append(f"{reader.name}: Decremented read count to {self.read_count}")

        if self.read_count == 0:
            # Last reader - release write lock
            unblocked = self.mutex.unlock()
            steps.append(f"{reader.name}: Released write lock")
            if unblocked:
                steps.append(f"{reader.name}: Unblocked writer {unblocked.name}")

        self.read_count_mutex.unlock()
        steps.append(f"{reader.name}: Exited read count section")
        steps.append(f"{reader.name}: Finished reading")

        return {'success': True, 'steps': steps, 'read_count': self.read_count, 'writer_active': self.writer_active}

    def start_write(self, writer: SynchronizationProcess) -> Dict[str, Any]:
        """Writer tries to start writing"""
        steps = []

        if not self.mutex.lock(writer):
            steps.append(f"{writer.name}: Waiting for write lock")
            return {'success': False, 'steps': steps, 'read_count': self.read_count, 'writer_active': self.writer_active}

        self.writer_active = True
        steps.append(f"{writer.name}: Acquired write lock for writing")
        steps.append(f"{writer.name}: Started writing")

        return {'success': True, 'steps': steps, 'read_count': self.read_count, 'writer_active': self.writer_active}

    def end_write(self, writer: SynchronizationProcess) -> Dict[str, Any]:
        """Writer finishes writing"""
        steps = []

        unblocked = self.mutex.unlock()
        self.writer_active = False
        steps.append(f"{writer.name}: Released write lock")
        steps.append(f"{writer.name}: Finished writing")

        if unblocked:
            steps.append(f"{writer.name}: Unblocked reader/writer {unblocked.name}")

        return {'success': True, 'steps': steps, 'read_count': self.read_count, 'writer_active': self.writer_active}

class SynchronizationSimulator:
    """Main simulator for synchronization concepts"""

    def __init__(self):
        self.processes = []
        self.semaphores = {}
        self.mutexes = {}
        self.monitors = {}
        self.producer_consumer = None
        self.dining_philosophers = None
        self.readers_writers = None

    def add_process(self, pid: str, name: str = "") -> SynchronizationProcess:
        process = SynchronizationProcess(pid, name)
        self.processes.append(process)
        return process

    def add_semaphore(self, name: str, value: int) -> Semaphore:
        semaphore = Semaphore(value, name)
        self.semaphores[name] = semaphore
        return semaphore

    def add_mutex(self, name: str) -> Mutex:
        mutex = Mutex(name)
        self.mutexes[name] = mutex
        return mutex

    def add_monitor(self, name: str) -> Monitor:
        monitor = Monitor(name)
        self.monitors[name] = monitor
        return monitor

    def setup_producer_consumer(self, buffer_size: int = 5, num_producers: int = 2, num_consumers: int = 2):
        self.producer_consumer = ProducerConsumer(buffer_size)
        self.processes = []
        for i in range(num_producers):
            self.add_process(f"Producer{i}", f"Producer {i}")
        for i in range(num_consumers):
            self.add_process(f"Consumer{i}", f"Consumer {i}")

    def setup_dining_philosophers(self, num_philosophers: int = 5):
        self.dining_philosophers = DiningPhilosophers(num_philosophers)
        self.processes = self.dining_philosophers.philosophers.copy()

    def setup_readers_writers(self, num_readers: int = 3, num_writers: int = 2):
        self.readers_writers = ReadersWriters()
        self.processes = []
        for i in range(num_readers):
            self.add_process(f"Reader{i}", f"Reader {i}")
        for i in range(num_writers):
            self.add_process(f"Writer{i}", f"Writer {i}")

    def get_state(self) -> Dict[str, Any]:
        """Get current state of the synchronization system"""
        return {
            'processes': [{'pid': p.pid, 'name': p.name, 'state': p.state.value, 'waiting_for': p.waiting_for}
                         for p in self.processes],
            'semaphores': {name: {'value': s.value, 'waiting': len(s.waiting_queue)}
                          for name, s in self.semaphores.items()},
            'mutexes': {name: {'locked': m.locked, 'owner': m.owner.pid if m.owner else None,
                              'waiting': len(m.waiting_queue)}
                       for name, m in self.mutexes.items()},
            'monitors': {name: {'condition_vars': {cv: len(procs) for cv, procs in m.condition_vars.items()}}
                        for name, m in self.monitors.items()},
            'producer_consumer': {
                'buffer': self.producer_consumer.buffer.copy() if self.producer_consumer else [],
                'buffer_size': self.producer_consumer.buffer_size if self.producer_consumer else 0
            } if self.producer_consumer else None,
            'dining_philosophers': {
                'states': self.dining_philosophers.states.copy() if self.dining_philosophers else []
            } if self.dining_philosophers else None,
            'readers_writers': {
                'read_count': self.readers_writers.read_count if self.readers_writers else 0,
                'writer_active': self.readers_writers.writer_active if self.readers_writers else False
            } if self.readers_writers else None
        }