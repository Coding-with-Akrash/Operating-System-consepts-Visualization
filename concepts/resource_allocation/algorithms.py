from typing import List, Dict, Set, Tuple, Any
import copy
from enum import Enum

class AllocationPolicy(Enum):
    FCFS = "First Come First Served"
    PRIORITY = "Priority Based"
    ROUND_ROBIN = "Round Robin"
    FAIR_SHARE = "Fair Share"
    BANKERS = "Banker's Algorithm"

class Process:
    def __init__(self, pid: str, max_resources: List[int], allocated_resources: List[int] = None, priority: int = 0, arrival_time: int = 0):
        self.pid = pid
        self.max_resources = max_resources  # Maximum resources needed
        self.allocated_resources = allocated_resources or [0] * len(max_resources)  # Currently allocated
        self.need_resources = [max_r - alloc for max_r, alloc in zip(max_resources, self.allocated_resources)]
        self.priority = priority
        self.arrival_time = arrival_time
        self.wait_time = 0
        self.finish_time = None

    def __repr__(self):
        return f"Process(pid={self.pid}, max={self.max_resources}, allocated={self.allocated_resources}, need={self.need_resources})"

class Resource:
    def __init__(self, rid: str, total_instances: int):
        self.rid = rid
        self.total_instances = total_instances
        self.available_instances = total_instances

    def __repr__(self):
        return f"Resource(rid={self.rid}, total={self.total_instances}, available={self.available_instances})"

class ResourceAllocationAlgorithms:
    @staticmethod
    def bankers_algorithm(processes: List[Process], resources: List[Resource]) -> Dict[str, Any]:
        """
        Banker's algorithm for deadlock avoidance.
        Returns whether the system is in safe state and a safe sequence if safe.
        """
        work = [r.available_instances for r in resources]
        finish = [False] * len(processes)
        safe_sequence = []

        while len(safe_sequence) < len(processes):
            found = False
            for i, process in enumerate(processes):
                if not finish[i] and all(need <= work[j] for j, need in enumerate(process.need_resources)):
                    # Can allocate
                    for j in range(len(work)):
                        work[j] += process.allocated_resources[j]
                    finish[i] = True
                    safe_sequence.append(process.pid)
                    found = True
                    break
            if not found:
                return {
                    'safe': False,
                    'safe_sequence': None,
                    'message': 'System is not in safe state - potential deadlock'
                }

        return {
            'safe': True,
            'safe_sequence': safe_sequence,
            'message': 'System is in safe state'
        }

    @staticmethod
    def simulate_request_bankers(processes: List[Process], resources: List[Resource], process_id: str, request: List[int]) -> Dict[str, Any]:
        """
        Simulate a resource request in Banker's algorithm.
        """
        process = next((p for p in processes if p.pid == process_id), None)
        if not process:
            return {'granted': False, 'message': f"Process {process_id} not found"}

        # Check if request <= need
        if any(req > need for req, need in zip(request, process.need_resources)):
            return {'granted': False, 'message': "Request exceeds maximum claim"}

        # Check if request <= available
        if any(req > avail for req, avail in zip(request, [r.available_instances for r in resources])):
            return {'granted': False, 'message': "Request exceeds available resources"}

        # Temporarily allocate
        temp_processes = copy.deepcopy(processes)
        temp_resources = copy.deepcopy(resources)
        temp_proc = next(p for p in temp_processes if p.pid == process_id)
        for i, req in enumerate(request):
            temp_proc.allocated_resources[i] += req
            temp_proc.need_resources[i] -= req
            temp_resources[i].available_instances -= req

        # Check if still safe
        result = ResourceAllocationAlgorithms.bankers_algorithm(temp_processes, temp_resources)
        if result['safe']:
            # Actually allocate
            for i, req in enumerate(request):
                process.allocated_resources[i] += req
                process.need_resources[i] -= req
                resources[i].available_instances -= req
            return {'granted': True, 'message': "Request granted"}
        else:
            return {'granted': False, 'message': "Request would lead to unsafe state"}

    @staticmethod
    def fcfs_allocation(processes: List[Process], resources: List[Resource], requests: List[Tuple[str, List[int]]]) -> List[Dict[str, Any]]:
        """
        First Come First Served allocation strategy.
        Processes are served in order of arrival.
        """
        results = []
        current_time = 0

        # Sort processes by arrival time
        sorted_processes = sorted(processes, key=lambda p: p.arrival_time)

        for pid, request in requests:
            process = next((p for p in sorted_processes if p.pid == pid), None)
            if not process:
                results.append({'granted': False, 'message': f"Process {pid} not found"})
                continue

            # Check if request can be satisfied
            can_grant = all(req <= avail for req, avail in zip(request, [r.available_instances for r in resources]))

            if can_grant:
                # Allocate
                for i, req in enumerate(request):
                    process.allocated_resources[i] += req
                    process.need_resources[i] -= req
                    resources[i].available_instances -= req
                results.append({'granted': True, 'message': f"Request by {pid} granted"})
            else:
                results.append({'granted': False, 'message': f"Request by {pid} denied - insufficient resources"})

        return results

    @staticmethod
    def priority_allocation(processes: List[Process], resources: List[Resource], requests: List[Tuple[str, List[int]]]) -> List[Dict[str, Any]]:
        """
        Priority-based allocation strategy.
        Higher priority processes are served first.
        """
        results = []

        # Sort requests by process priority (higher priority first)
        priority_requests = []
        for pid, request in requests:
            process = next((p for p in processes if p.pid == pid), None)
            if process:
                priority_requests.append((process.priority, pid, request))

        priority_requests.sort(reverse=True)  # Higher priority first

        for _, pid, request in priority_requests:
            process = next((p for p in processes if p.pid == pid), None)

            # Check if request can be satisfied
            can_grant = all(req <= avail for req, avail in zip(request, [r.available_instances for r in resources]))

            if can_grant:
                # Allocate
                for i, req in enumerate(request):
                    process.allocated_resources[i] += req
                    process.need_resources[i] -= req
                    resources[i].available_instances -= req
                results.append({'granted': True, 'message': f"Request by {pid} (priority {process.priority}) granted"})
            else:
                results.append({'granted': False, 'message': f"Request by {pid} (priority {process.priority}) denied - insufficient resources"})

        return results

    @staticmethod
    def round_robin_allocation(processes: List[Process], resources: List[Resource], requests: List[Tuple[str, List[int]]], time_quantum: int = 1) -> List[Dict[str, Any]]:
        """
        Round-robin allocation strategy for resources.
        Each process gets a time quantum for resource usage.
        """
        results = []
        current_time = 0
        queue = list(requests)  # Queue of (pid, request)

        while queue:
            pid, request = queue.pop(0)
            process = next((p for p in processes if p.pid == pid), None)
            if not process:
                results.append({'granted': False, 'message': f"Process {pid} not found"})
                continue

            # Check if request can be satisfied
            can_grant = all(req <= avail for req, avail in zip(request, [r.available_instances for r in resources]))

            if can_grant:
                # Allocate for time quantum
                allocated_time = min(time_quantum, max(request))  # Simplified
                # For demo, allocate partially or fully
                for i, req in enumerate(request):
                    alloc_amount = min(req, allocated_time)  # Simplified allocation
                    process.allocated_resources[i] += alloc_amount
                    process.need_resources[i] -= alloc_amount
                    resources[i].available_instances -= alloc_amount

                if all(need == 0 for need in process.need_resources):
                    results.append({'granted': True, 'message': f"Request by {pid} completed"})
                else:
                    # Re-queue if not finished
                    remaining_request = [max(0, need) for need in process.need_resources]
                    queue.append((pid, remaining_request))
                    results.append({'granted': True, 'message': f"Request by {pid} partially granted, re-queued"})
            else:
                # Re-queue
                queue.append((pid, request))
                results.append({'granted': False, 'message': f"Request by {pid} denied, re-queued"})

        return results

    @staticmethod
    def fair_share_allocation(processes: List[Process], resources: List[Resource]) -> Dict[str, Any]:
        """
        Fair share allocation strategy.
        Resources are allocated equally among processes.
        """
        if not processes:
            return {'allocations': {}, 'message': 'No processes'}

        num_processes = len(processes)
        allocations = {}

        for i, resource in enumerate(resources):
            fair_share = resource.total_instances // num_processes
            remainder = resource.total_instances % num_processes

            for j, process in enumerate(processes):
                alloc = fair_share + (1 if j < remainder else 0)
                alloc = min(alloc, process.max_resources[i])  # Don't exceed max claim

                if process.pid not in allocations:
                    allocations[process.pid] = [0] * len(resources)
                allocations[process.pid][i] = alloc

                # Update process allocation
                process.allocated_resources[i] = alloc
                process.need_resources[i] = process.max_resources[i] - alloc

                # Update available
                resource.available_instances -= alloc

        return {
            'allocations': allocations,
            'message': f"Fair share allocation completed for {num_processes} processes"
        }

    @staticmethod
    def deallocate_resources(processes: List[Process], resources: List[Resource], process_id: str, release: List[int]) -> Dict[str, Any]:
        """
        Deallocate resources from a process.
        """
        process = next((p for p in processes if p.pid == process_id), None)
        if not process:
            return {'success': False, 'message': f"Process {process_id} not found"}

        # Check if release <= allocated
        if any(rel > alloc for rel, alloc in zip(release, process.allocated_resources)):
            return {'success': False, 'message': "Cannot release more than allocated"}

        # Deallocate
        for i, rel in enumerate(release):
            process.allocated_resources[i] -= rel
            process.need_resources[i] += rel
            resources[i].available_instances += rel

        return {'success': True, 'message': f"Resources released from {process_id}"}

    @staticmethod
    def check_starvation(processes: List[Process], time_threshold: int = 100) -> List[str]:
        """
        Check for starvation - processes waiting too long.
        """
        starved = []
        for process in processes:
            if process.wait_time > time_threshold and any(need > 0 for need in process.need_resources):
                starved.append(process.pid)
        return starved