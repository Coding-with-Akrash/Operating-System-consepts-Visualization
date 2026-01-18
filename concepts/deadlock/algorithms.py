from typing import List, Dict, Set, Tuple, Any
import copy

class Process:
    def __init__(self, pid: str, max_resources: List[int], allocated_resources: List[int] = None):
        self.pid = pid
        self.max_resources = max_resources  # Maximum resources needed
        self.allocated_resources = allocated_resources or [0] * len(max_resources)  # Currently allocated
        self.need_resources = [max_r - alloc for max_r, alloc in zip(max_resources, self.allocated_resources)]

    def __repr__(self):
        return f"Process(pid={self.pid}, max={self.max_resources}, allocated={self.allocated_resources}, need={self.need_resources})"

class Resource:
    def __init__(self, rid: str, total_instances: int):
        self.rid = rid
        self.total_instances = total_instances
        self.available_instances = total_instances

    def __repr__(self):
        return f"Resource(rid={self.rid}, total={self.total_instances}, available={self.available_instances})"

class DeadlockAlgorithms:
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
    def detect_deadlock_wait_for_graph(wait_for_graph: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Detect deadlock using wait-for graph.
        wait_for_graph: {process: [processes it waits for]}
        """
        # Simple cycle detection using DFS
        def has_cycle(node, visited, rec_stack):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in wait_for_graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, visited, rec_stack):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        visited = set()
        rec_stack = set()
        deadlocked_processes = []

        for process in wait_for_graph:
            if process not in visited:
                if has_cycle(process, visited, rec_stack):
                    # Find the cycle (simplified)
                    deadlocked_processes = list(rec_stack)
                    break

        return {
            'deadlock_detected': len(deadlocked_processes) > 0,
            'deadlocked_processes': deadlocked_processes,
            'message': f"Deadlock detected among processes: {deadlocked_processes}" if deadlocked_processes else "No deadlock detected"
        }

    @staticmethod
    def detect_deadlock_resource_allocation(processes: List[Process], resources: List[Resource]) -> Dict[str, Any]:
        """
        Detect deadlock using resource allocation graph.
        Simplified: check if any process needs more than available.
        """
        available = [r.available_instances for r in resources]
        deadlocked = []

        for process in processes:
            if any(need > avail for need, avail in zip(process.need_resources, available)):
                deadlocked.append(process.pid)

        return {
            'deadlock_detected': len(deadlocked) > 0,
            'deadlocked_processes': deadlocked,
            'message': f"Potential deadlock: processes {deadlocked} cannot proceed" if deadlocked else "No deadlock detected"
        }

    @staticmethod
    def simulate_request(processes: List[Process], resources: List[Resource], process_id: str, request: List[int]) -> Dict[str, Any]:
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
        result = DeadlockAlgorithms.bankers_algorithm(temp_processes, temp_resources)
        if result['safe']:
            # Actually allocate
            for i, req in enumerate(request):
                process.allocated_resources[i] += req
                process.need_resources[i] -= req
                resources[i].available_instances -= req
            return {'granted': True, 'message': "Request granted"}
        else:
            return {'granted': False, 'message': "Request would lead to unsafe state"}