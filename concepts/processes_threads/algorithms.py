from typing import List, Dict, Any, Optional
from enum import Enum
import threading
import time
import random

class ProcessState(Enum):
    NEW = "New"
    READY = "Ready"
    RUNNING = "Running"
    WAITING = "Waiting"
    TERMINATED = "Terminated"

class ThreadState(Enum):
    NEW = "New"
    READY = "Ready"
    RUNNING = "Running"
    BLOCKED = "Blocked"
    TERMINATED = "Terminated"

class ThreadModel(Enum):
    USER_LEVEL = "User-Level Threads"
    KERNEL_LEVEL = "Kernel-Level Threads"
    HYBRID = "Hybrid Model"

class PCB:
    """Process Control Block"""
    def __init__(self, pid: str):
        self.pid = pid
        self.state = ProcessState.NEW
        self.priority = 0
        self.program_counter = 0
        self.cpu_registers = {}
        self.memory_limits = {}
        self.open_files = []
        self.creation_time = time.time()
        self.cpu_time_used = 0
        self.parent_pid = None
        self.children_pids = []

    def __repr__(self):
        return f"PCB(pid={self.pid}, state={self.state.value})"

class TCB:
    """Thread Control Block"""
    def __init__(self, tid: str, pid: str):
        self.tid = tid
        self.pid = pid
        self.state = ThreadState.NEW
        self.stack_pointer = 0
        self.cpu_registers = {}
        self.priority = 0
        self.creation_time = time.time()
        self.cpu_time_used = 0

    def __repr__(self):
        return f"TCB(tid={self.tid}, pid={self.pid}, state={self.state.value})"

class Process:
    def __init__(self, pid: str, arrival_time: int = 0, burst_time: int = 10):
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.remaining_time = burst_time
        self.state = ProcessState.NEW
        self.pcb = PCB(pid)
        self.threads: List[Thread] = []
        self.resources = []
        self.messages = []  # For IPC

    def add_thread(self, thread: 'Thread'):
        self.threads.append(thread)

    def change_state(self, new_state: ProcessState):
        self.state = new_state
        self.pcb.state = new_state

    def __repr__(self):
        return f"Process(pid={self.pid}, state={self.state.value}, threads={len(self.threads)})"

class Thread:
    def __init__(self, tid: str, pid: str, model: ThreadModel = ThreadModel.USER_LEVEL):
        self.tid = tid
        self.pid = pid
        self.model = model
        self.state = ThreadState.NEW
        self.tcb = TCB(tid, pid)
        self.function = None
        self.args = ()

    def change_state(self, new_state: ThreadState):
        self.state = new_state
        self.tcb.state = new_state

    def __repr__(self):
        return f"Thread(tid={self.tid}, pid={self.pid}, state={self.state.value})"

class ProcessScheduler:
    """Simulates process scheduling and lifecycle"""

    @staticmethod
    def simulate_process_lifecycle(processes: List[Process], max_time: int = 100) -> Dict[str, Any]:
        """Simulate process lifecycle with state transitions"""
        current_time = 0
        ready_queue = []
        running_process = None
        completed_processes = []
        timeline = []  # List of (time, pid, state)

        # Sort processes by arrival time
        processes = sorted(processes, key=lambda p: p.arrival_time)

        while current_time < max_time and len(completed_processes) < len(processes):
            # Add arrived processes to ready queue
            arrived = [p for p in processes if p.arrival_time <= current_time and p not in ready_queue and p not in completed_processes]
            for p in arrived:
                p.change_state(ProcessState.READY)
                ready_queue.append(p)
                timeline.append((current_time, p.pid, ProcessState.READY))

            # If no running process, schedule one
            if not running_process and ready_queue:
                running_process = ready_queue.pop(0)
                running_process.change_state(ProcessState.RUNNING)
                timeline.append((current_time, running_process.pid, ProcessState.RUNNING))

            # Simulate execution
            if running_process:
                running_process.remaining_time -= 1
                running_process.pcb.cpu_time_used += 1

                if running_process.remaining_time <= 0:
                    # Process completed
                    running_process.change_state(ProcessState.TERMINATED)
                    timeline.append((current_time, running_process.pid, ProcessState.TERMINATED))
                    completed_processes.append(running_process)
                    running_process = None
                elif random.random() < 0.1:  # 10% chance of I/O wait
                    # Simulate I/O operation
                    running_process.change_state(ProcessState.WAITING)
                    timeline.append((current_time, running_process.pid, ProcessState.WAITING))
                    # Will be moved back to ready after some time
                    running_process.io_wait_time = current_time + random.randint(2, 5)
                    running_process = None

            # Check for processes finishing I/O
            waiting_processes = [p for p in processes if p.state == ProcessState.WAITING and hasattr(p, 'io_wait_time') and current_time >= p.io_wait_time]
            for p in waiting_processes:
                p.change_state(ProcessState.READY)
                ready_queue.append(p)
                timeline.append((current_time, p.pid, ProcessState.READY))
                delattr(p, 'io_wait_time')

            current_time += 1

            # Context switch if needed (simple round-robin)
            if running_process and random.random() < 0.2:  # 20% chance of preemption
                running_process.change_state(ProcessState.READY)
                timeline.append((current_time, running_process.pid, ProcessState.READY))
                ready_queue.append(running_process)
                running_process = None

        return {
            'timeline': timeline,
            'completed_processes': completed_processes,
            'total_time': current_time
        }

class ThreadManager:
    """Manages thread creation and scheduling"""

    @staticmethod
    def create_thread(pid: str, tid: str, model: ThreadModel = ThreadModel.USER_LEVEL) -> Thread:
        """Create a new thread"""
        thread = Thread(tid, pid, model)
        return thread

    @staticmethod
    def simulate_thread_execution(threads: List[Thread], max_time: int = 50) -> Dict[str, Any]:
        """Simulate thread execution with different models"""
        current_time = 0
        ready_queue = []
        running_thread = None
        completed_threads = []
        timeline = []

        # Initialize threads
        for thread in threads:
            thread.change_state(ThreadState.READY)
            ready_queue.append(thread)
            timeline.append((current_time, thread.tid, ThreadState.READY))

        while current_time < max_time and len(completed_threads) < len(threads):
            # Schedule thread based on model
            if not running_thread and ready_queue:
                if threads[0].model == ThreadModel.USER_LEVEL:
                    # User-level: simple FCFS
                    running_thread = ready_queue.pop(0)
                elif threads[0].model == ThreadModel.KERNEL_LEVEL:
                    # Kernel-level: priority-based
                    ready_queue.sort(key=lambda t: t.tcb.priority)
                    running_thread = ready_queue.pop(0)
                else:  # Hybrid
                    running_thread = ready_queue.pop(0)

                running_thread.change_state(ThreadState.RUNNING)
                timeline.append((current_time, running_thread.tid, ThreadState.RUNNING))

            # Simulate execution
            if running_thread:
                running_thread.tcb.cpu_time_used += 1

                if random.random() < 0.15:  # 15% chance of blocking
                    running_thread.change_state(ThreadState.BLOCKED)
                    timeline.append((current_time, running_thread.tid, ThreadState.BLOCKED))
                    running_thread.block_time = current_time + random.randint(1, 3)
                    running_thread = None
                elif running_thread.tcb.cpu_time_used >= 5:  # Thread completes after 5 time units
                    running_thread.change_state(ThreadState.TERMINATED)
                    timeline.append((current_time, running_thread.tid, ThreadState.TERMINATED))
                    completed_threads.append(running_thread)
                    running_thread = None

            # Check for unblocked threads
            blocked_threads = [t for t in threads if t.state == ThreadState.BLOCKED and hasattr(t, 'block_time') and current_time >= t.block_time]
            for t in blocked_threads:
                t.change_state(ThreadState.READY)
                ready_queue.append(t)
                timeline.append((current_time, t.tid, ThreadState.READY))
                delattr(t, 'block_time')

            current_time += 1

            # Context switch for kernel-level threads
            if running_thread and threads[0].model == ThreadModel.KERNEL_LEVEL and random.random() < 0.3:
                running_thread.change_state(ThreadState.READY)
                timeline.append((current_time, running_thread.tid, ThreadState.READY))
                ready_queue.append(running_thread)
                running_thread = None

        return {
            'timeline': timeline,
            'completed_threads': completed_threads,
            'total_time': current_time
        }

class IPCManager:
    """Inter-Process Communication simulation"""

    def __init__(self):
        self.message_queues = {}  # pid -> list of messages

    def send_message(self, from_pid: str, to_pid: str, message: str):
        """Send message between processes"""
        if to_pid not in self.message_queues:
            self.message_queues[to_pid] = []
        self.message_queues[to_pid].append((from_pid, message, time.time()))

    def receive_message(self, pid: str) -> Optional[tuple]:
        """Receive message for a process"""
        if pid in self.message_queues and self.message_queues[pid]:
            return self.message_queues[pid].pop(0)
        return None

    def get_queue_size(self, pid: str) -> int:
        """Get number of messages in queue for a process"""
        return len(self.message_queues.get(pid, []))