from typing import List, Dict, Any
import copy

class Process:
    def __init__(self, pid: str, arrival_time: int, burst_time: int, priority: int = 0):
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.priority = priority
        self.remaining_time = burst_time
        self.completion_time = 0
        self.waiting_time = 0
        self.turnaround_time = 0
        self.start_time = None

    def __repr__(self):
        return f"Process(pid={self.pid}, arrival={self.arrival_time}, burst={self.burst_time})"

class Scheduler:
    @staticmethod
    def fcfs(processes: List[Process]) -> Dict[str, Any]:
        """First Come First Served scheduling."""
        sorted_processes = sorted(processes, key=lambda p: p.arrival_time)
        current_time = 0
        gantt_chart = []
        completed_processes = []

        for process in sorted_processes:
            if current_time < process.arrival_time:
                current_time = process.arrival_time

            process.start_time = current_time
            process.completion_time = current_time + process.burst_time
            process.turnaround_time = process.completion_time - process.arrival_time
            process.waiting_time = process.turnaround_time - process.burst_time

            gantt_chart.append((process.pid, current_time, process.completion_time))
            current_time = process.completion_time
            completed_processes.append(process)

        avg_waiting = sum(p.waiting_time for p in completed_processes) / len(completed_processes)
        avg_turnaround = sum(p.turnaround_time for p in completed_processes) / len(completed_processes)

        return {
            'processes': completed_processes,
            'gantt_chart': gantt_chart,
            'avg_waiting_time': avg_waiting,
            'avg_turnaround_time': avg_turnaround
        }

    @staticmethod
    def sjf(processes: List[Process]) -> Dict[str, Any]:
        """Shortest Job First scheduling (non-preemptive)."""
        processes_copy = copy.deepcopy(processes)
        current_time = 0
        completed = []
        gantt_chart = []
        ready_queue = []

        while len(completed) < len(processes_copy):
            # Add arrived processes to ready queue
            arrived = [p for p in processes_copy if p.arrival_time <= current_time and p not in completed and p not in ready_queue]
            ready_queue.extend(arrived)

            if not ready_queue:
                current_time += 1
                continue

            # Select shortest job
            ready_queue.sort(key=lambda p: p.burst_time)
            process = ready_queue.pop(0)

            process.start_time = current_time
            process.completion_time = current_time + process.burst_time
            process.turnaround_time = process.completion_time - process.arrival_time
            process.waiting_time = process.turnaround_time - process.burst_time

            gantt_chart.append((process.pid, current_time, process.completion_time))
            current_time = process.completion_time
            completed.append(process)

        avg_waiting = sum(p.waiting_time for p in completed) / len(completed)
        avg_turnaround = sum(p.turnaround_time for p in completed) / len(completed)

        return {
            'processes': completed,
            'gantt_chart': gantt_chart,
            'avg_waiting_time': avg_waiting,
            'avg_turnaround_time': avg_turnaround
        }

    @staticmethod
    def round_robin(processes: List[Process], time_quantum: int) -> Dict[str, Any]:
        """Round Robin scheduling."""
        processes_copy = copy.deepcopy(processes)
        current_time = 0
        gantt_chart = []
        ready_queue = []

        while any(p.remaining_time > 0 for p in processes_copy):
            # Add arrived processes
            arrived = [p for p in processes_copy if p.arrival_time <= current_time and p.remaining_time > 0 and p not in ready_queue]
            ready_queue.extend(arrived)

            if not ready_queue:
                current_time += 1
                continue

            process = ready_queue.pop(0)
            start_time = current_time
            execute_time = min(time_quantum, process.remaining_time)
            current_time += execute_time
            process.remaining_time -= execute_time

            gantt_chart.append((process.pid, start_time, current_time))

            if process.remaining_time > 0:
                # Re-add to queue if not finished
                later_arrivals = [p for p in processes_copy if p.arrival_time <= current_time and p.remaining_time > 0 and p != process and p not in ready_queue]
                ready_queue.extend(later_arrivals)
                ready_queue.append(process)
            else:
                process.completion_time = current_time
                process.turnaround_time = current_time - process.arrival_time
                process.waiting_time = process.turnaround_time - process.burst_time

        completed_processes = [p for p in processes_copy if p.remaining_time == 0]
        avg_waiting = sum(p.waiting_time for p in completed_processes) / len(completed_processes)
        avg_turnaround = sum(p.turnaround_time for p in completed_processes) / len(completed_processes)

        return {
            'processes': completed_processes,
            'gantt_chart': gantt_chart,
            'avg_waiting_time': avg_waiting,
            'avg_turnaround_time': avg_turnaround
        }

    @staticmethod
    def priority_scheduling(processes: List[Process]) -> Dict[str, Any]:
        """Priority scheduling (non-preemptive)."""
        processes_copy = copy.deepcopy(processes)
        current_time = 0
        completed = []
        gantt_chart = []
        ready_queue = []

        while len(completed) < len(processes_copy):
            # Add arrived processes
            arrived = [p for p in processes_copy if p.arrival_time <= current_time and p not in completed and p not in ready_queue]
            ready_queue.extend(arrived)

            if not ready_queue:
                current_time += 1
                continue

            # Select highest priority (lowest number)
            ready_queue.sort(key=lambda p: p.priority)
            process = ready_queue.pop(0)

            process.start_time = current_time
            process.completion_time = current_time + process.burst_time
            process.turnaround_time = process.completion_time - process.arrival_time
            process.waiting_time = process.turnaround_time - process.burst_time

            gantt_chart.append((process.pid, current_time, process.completion_time))
            current_time = process.completion_time
            completed.append(process)

        avg_waiting = sum(p.waiting_time for p in completed) / len(completed)
        avg_turnaround = sum(p.turnaround_time for p in completed) / len(completed)

        return {
            'processes': completed,
            'gantt_chart': gantt_chart,
            'avg_waiting_time': avg_waiting,
            'avg_turnaround_time': avg_turnaround
        }