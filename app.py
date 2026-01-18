from flask import Flask, render_template, request, jsonify
import os
from concepts.cpu_scheduling.algorithms import Scheduler as CPUScheduler, Process as CPUProcess
from concepts.deadlock.algorithms import *
from concepts.memory_management.algorithms import *
from concepts.synchronization.algorithms import SynchronizationProcess, Semaphore, Mutex, ProducerConsumer, DiningPhilosophers, ReadersWriters
from concepts.file_systems.algorithms import *
from concepts.processes_threads.algorithms import Process as PTProcess, Thread, ThreadModel, ProcessScheduler, ThreadManager, IPCManager
from concepts.io_management.algorithms import *
from concepts.resource_allocation.algorithms import *

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cpu_scheduling')
def cpu_scheduling():
    return render_template('cpu_scheduling.html')

@app.route('/cpu_scheduling/run', methods=['POST'])
def run_cpu_scheduling():
    data = request.json
    algorithm = data['algorithm']
    time_quantum = int(data.get('time_quantum', 2))
    processes_data = data['processes']

    processes = []
    for p in processes_data:
        processes.append(CPUProcess(p['pid'], int(p['arrival']), int(p['burst']), int(p['priority'])))
    
    if algorithm == 'FCFS':
        result = CPUScheduler.fcfs(processes)
    elif algorithm == 'SJF':
        result = CPUScheduler.sjf(processes)
    elif algorithm == 'Round Robin':
        result = CPUScheduler.round_robin(processes, time_quantum)
    elif algorithm == 'Priority':
        result = CPUScheduler.priority_scheduling(processes)

    # Serialize processes for JSON
    result['processes'] = [{'pid': p.pid, 'waiting_time': p.waiting_time, 'turnaround_time': p.turnaround_time} for p in result['processes']]
    result['order'] = [p[0] for p in result['gantt_chart']]  # Extract order from gantt chart

    return jsonify(result)

@app.route('/deadlock/bankers', methods=['POST'])
def run_bankers_algorithm():
    data = request.json
    processes_data = data['processes']
    resources_data = data['resources']

    processes = []
    for p in processes_data:
        processes.append(Process(p['pid'], [int(x) for x in p['max_resources']], [int(x) for x in p['allocated_resources']]))

    resources = []
    for r in resources_data:
        resources.append(Resource(r['rid'], int(r['total_instances'])))

    result = DeadlockAlgorithms.bankers_algorithm(processes, resources)
    return jsonify(result)

@app.route('/deadlock/detect', methods=['POST'])
def detect_deadlock():
    data = request.json
    method = data['method']

    if method == 'wait_for_graph':
        wait_for_graph = data['wait_for_graph']
        result = DeadlockAlgorithms.detect_deadlock_wait_for_graph(wait_for_graph)
    elif method == 'resource_allocation':
        processes_data = data['processes']
        resources_data = data['resources']
        processes = [Process(p['pid'], p['max_resources'], p['allocated_resources']) for p in processes_data]
        resources = [Resource(r['rid'], r['total_instances']) for r in resources_data]
        result = DeadlockAlgorithms.detect_deadlock_resource_allocation(processes, resources)
    else:
        result = {'error': 'Invalid method'}

    return jsonify(result)

@app.route('/deadlock/request', methods=['POST'])
def simulate_resource_request():
    data = request.json
    processes_data = data['processes']
    resources_data = data['resources']
    process_id = data['process_id']
    req = [int(x) for x in data['request']]

    processes = [Process(p['pid'], [int(x) for x in p['max_resources']], [int(x) for x in p['allocated_resources']]) for p in processes_data]
    resources = [Resource(r['rid'], int(r['total_instances'])) for r in resources_data]

    result = DeadlockAlgorithms.simulate_request(processes, resources, process_id, req)
    return jsonify(result)

@app.route('/memory_management/allocate', methods=['POST'])
def allocate_memory():
    data = request.json
    algorithm = data['algorithm']
    blocks_data = data['blocks']
    process_size = data['process_size']
    process_id = data['process_id']

    blocks = []
    for b in blocks_data:
        blocks.append(MemoryBlock(b['start'], b['size'], b.get('process_id')))

    if algorithm == 'first_fit':
        result = MemoryManager.first_fit(blocks, process_size, process_id)
    elif algorithm == 'best_fit':
        result = MemoryManager.best_fit(blocks, process_size, process_id)
    elif algorithm == 'worst_fit':
        result = MemoryManager.worst_fit(blocks, process_size, process_id)
    else:
        return jsonify({'error': 'Invalid algorithm'})

    return jsonify({
        'allocated_address': result,
        'blocks': [{'start': b.start, 'size': b.size, 'process_id': b.process_id, 'is_free': b.is_free} for b in blocks]
    })

@app.route('/memory_management/deallocate', methods=['POST'])
def deallocate_memory():
    data = request.json
    blocks_data = data['blocks']
    process_id = data['process_id']

    blocks = []
    for b in blocks_data:
        blocks.append(MemoryBlock(b['start'], b['size'], b.get('process_id')))

    result = MemoryManager.deallocate_memory(blocks, process_id)

    return jsonify({
        'deallocated': result,
        'blocks': [{'start': b.start, 'size': b.size, 'process_id': b.process_id, 'is_free': b.is_free} for b in blocks]
    })

@app.route('/memory_management/page_replacement', methods=['POST'])
def page_replacement():
    data = request.json
    algorithm = data['algorithm']
    page_sequence = data['page_sequence']
    num_frames = data['num_frames']

    if algorithm == 'fifo':
        result = PageReplacement.fifo(page_sequence, num_frames)
    elif algorithm == 'lru':
        result = PageReplacement.lru(page_sequence, num_frames)
    elif algorithm == 'optimal':
        result = PageReplacement.optimal(page_sequence, num_frames)
    else:
        return jsonify({'error': 'Invalid algorithm'})

    return jsonify(result)

@app.route('/memory_management/virtual_memory', methods=['POST'])
def virtual_memory():
    data = request.json
    action = data['action']
    num_frames = data.get('num_frames', 4)
    page_size = data.get('page_size', 4096)

    simulator = VirtualMemorySimulator(num_frames, page_size)

    if action == 'translate':
        virtual_address = data['virtual_address']
        result = simulator.translate_address(virtual_address)
        return jsonify({'physical_address': result})
    elif action == 'allocate':
        page_number = data['page_number']
        result = simulator.allocate_page(page_number)
        return jsonify({'allocated': result})
    else:
        return jsonify({'error': 'Invalid action'})

@app.route('/memory_management/segmentation', methods=['POST'])
def segmentation():
    data = request.json
    action = data['action']

    simulator = SegmentationSimulator()

    if action == 'translate':
        segment_number = data['segment_number']
        offset = data['offset']
        result = simulator.translate_address(segment_number, offset)
        return jsonify({'physical_address': result})
    elif action == 'allocate':
        segment_number = data['segment_number']
        size = data['size']
        base_address = data['base_address']
        result = simulator.allocate_segment(segment_number, size, base_address)
        return jsonify({'allocated': result})
    else:
        return jsonify({'error': 'Invalid action'})

@app.route('/synchronization/semaphore', methods=['POST'])
def semaphore_operation():
    data = request.json
    operation = data['operation']
    semaphore_name = data['semaphore_name']
    initial_value = data.get('initial_value', 1)
    process_id = data.get('process_id')

    # For simplicity, create a new semaphore each time
    semaphore = Semaphore(initial_value, semaphore_name)
    process = SynchronizationProcess(process_id, process_id) if process_id else None

    if operation == 'wait':
        success = semaphore.wait(process)
        return jsonify({'success': success, 'value': semaphore.value, 'waiting': len(semaphore.waiting_queue)})
    elif operation == 'signal':
        unblocked = semaphore.signal()
        return jsonify({'value': semaphore.value, 'unblocked': unblocked.pid if unblocked else None})
    else:
        return jsonify({'error': 'Invalid operation'})

@app.route('/synchronization/mutex', methods=['POST'])
def mutex_operation():
    data = request.json
    operation = data['operation']
    mutex_name = data['mutex_name']
    process_id = data.get('process_id')

    mutex = Mutex(mutex_name)
    process = SynchronizationProcess(process_id, process_id) if process_id else None

    if operation == 'lock':
        success = mutex.lock(process)
        return jsonify({'success': success, 'locked': mutex.locked, 'owner': mutex.owner.pid if mutex.owner else None, 'waiting': len(mutex.waiting_queue)})
    elif operation == 'unlock':
        unblocked = mutex.unlock()
        return jsonify({'locked': mutex.locked, 'unblocked': unblocked.pid if unblocked else None})
    else:
        return jsonify({'error': 'Invalid operation'})

@app.route('/synchronization/producer_consumer', methods=['POST'])
def producer_consumer_operation():
    data = request.json
    operation = data['operation']
    buffer_size = data.get('buffer_size', 5)
    process_id = data['process_id']
    item = data.get('item')

    pc = ProducerConsumer(buffer_size)
    process = SynchronizationProcess(process_id, process_id)

    if operation == 'produce':
        result = pc.produce(process, item)
    elif operation == 'consume':
        result = pc.consume(process)
    else:
        return jsonify({'error': 'Invalid operation'})

    return jsonify(result)

@app.route('/synchronization/dining_philosophers', methods=['POST'])
def dining_philosophers_operation():
    data = request.json
    operation = data['operation']
    num_philosophers = data.get('num_philosophers', 5)
    philosopher_id = data['philosopher_id']

    dp = DiningPhilosophers(num_philosophers)

    if operation == 'pickup':
        result = dp.pickup_chopsticks(philosopher_id)
    elif operation == 'putdown':
        result = dp.putdown_chopsticks(philosopher_id)
    else:
        return jsonify({'error': 'Invalid operation'})

    return jsonify(result)

@app.route('/synchronization/readers_writers', methods=['POST'])
def readers_writers_operation():
    data = request.json
    operation = data['operation']
    process_id = data['process_id']

    rw = ReadersWriters()
    process = SynchronizationProcess(process_id, process_id)

    if operation == 'start_read':
        result = rw.start_read(process)
    elif operation == 'end_read':
        result = rw.end_read(process)
    elif operation == 'start_write':
        result = rw.start_write(process)
    elif operation == 'end_write':
        result = rw.end_write(process)
    else:
        return jsonify({'error': 'Invalid operation'})

    return jsonify(result)

@app.route('/file_systems/create_file', methods=['POST'])
def create_file():
    data = request.json
    path = data.get('path', '/')
    name = data['name']
    size = data['size']
    allocation_method = data.get('allocation_method', 'contiguous')
    total_blocks = data.get('total_blocks', 100)

    fs = FileSystem(total_blocks)
    fs.allocation_method = allocation_method

    success = fs.create_file(path, name, size)
    usage = fs.get_disk_usage()

    return jsonify({
        'success': success,
        'disk_usage': usage
    })

@app.route('/file_systems/delete_file', methods=['POST'])
def delete_file():
    data = request.json
    path = data.get('path', '/')
    name = data['name']
    allocation_method = data.get('allocation_method', 'contiguous')
    total_blocks = data.get('total_blocks', 100)

    fs = FileSystem(total_blocks)
    fs.allocation_method = allocation_method

    success = fs.delete_file(path, name)
    usage = fs.get_disk_usage()

    return jsonify({
        'success': success,
        'disk_usage': usage
    })

@app.route('/file_systems/create_directory', methods=['POST'])
def create_directory():
    data = request.json
    path = data.get('path', '/')
    name = data['name']
    total_blocks = data.get('total_blocks', 100)

    fs = FileSystem(total_blocks)

    success = fs.create_directory(path, name)

    return jsonify({
        'success': success
    })

@app.route('/file_systems/disk_usage', methods=['POST'])
def disk_usage():
    data = request.json
    total_blocks = data.get('total_blocks', 100)

    fs = FileSystem(total_blocks)
    usage = fs.get_disk_usage()

    return jsonify(usage)

@app.route('/processes_threads/simulate_processes', methods=['POST'])
def simulate_processes():
    data = request.json
    processes_data = data['processes']
    max_time = data.get('max_time', 100)

    processes = []
    for p in processes_data:
        processes.append(PTProcess(p['pid'], p['arrival_time'], p['burst_time']))

    result = ProcessScheduler.simulate_process_lifecycle(processes, max_time)
    return jsonify(result)

@app.route('/processes_threads/simulate_threads', methods=['POST'])
def simulate_threads():
    data = request.json
    threads_data = data['threads']
    model = data.get('model', 'USER_LEVEL')
    max_time = data.get('max_time', 50)

    threads = []
    for t in threads_data:
        thread_model = ThreadModel.USER_LEVEL if model == 'USER_LEVEL' else ThreadModel.KERNEL_LEVEL if model == 'KERNEL_LEVEL' else ThreadModel.HYBRID
        threads.append(Thread(t['tid'], t['pid'], thread_model))

    result = ThreadManager.simulate_thread_execution(threads, max_time)
    return jsonify(result)

@app.route('/processes_threads/ipc', methods=['POST'])
def ipc_operation():
    data = request.json
    operation = data['operation']
    from_pid = data.get('from_pid')
    to_pid = data.get('to_pid')
    message = data.get('message')

    ipc = IPCManager()

    if operation == 'send':
        ipc.send_message(from_pid, to_pid, message)
        return jsonify({'success': True})
    elif operation == 'receive':
        msg = ipc.receive_message(to_pid)
        return jsonify({'message': msg})
    elif operation == 'queue_size':
        size = ipc.get_queue_size(to_pid)
        return jsonify({'queue_size': size})
    else:
        return jsonify({'error': 'Invalid operation'})

@app.route('/io_management/schedule', methods=['POST'])
def io_schedule():
    data = request.json
    algorithm = data['algorithm']
    requests_data = data['requests']

    requests = []
    for r in requests_data:
        req_type = IORequestType.READ if r['type'] == 'read' else IORequestType.WRITE
        requests.append(IORequest(r['id'], r['process_id'], req_type, r['block_number'], r['arrival_time']))

    device = DeviceDriver("disk")

    if algorithm == 'fcfs':
        result = IOScheduler.fcfs(requests, device)
    elif algorithm == 'sstf':
        result = IOScheduler.sstf(requests, device)
    elif algorithm == 'scan':
        result = IOScheduler.scan(requests, device)
    else:
        return jsonify({'error': 'Invalid algorithm'})

    return jsonify(result)

@app.route('/resource_allocation/allocate', methods=['POST'])
def resource_allocate():
    data = request.json
    policy = data['policy']
    processes_data = data['processes']
    resources_data = data['resources']
    requests_data = data.get('requests', [])

    processes = []
    for p in processes_data:
        processes.append(Process(p['pid'], [int(x) for x in p['max_resources']], [int(x) for x in p['allocated_resources']], int(p.get('priority', 0)), int(p.get('arrival_time', 0))))

    resources = []
    for r in resources_data:
        resources.append(Resource(r['rid'], int(r['total_instances'])))

    requests = [(req['pid'], [int(x) for x in req['request']]) for req in requests_data]

    if policy == 'bankers':
        result = ResourceAllocationAlgorithms.bankers_algorithm(processes, resources)
    elif policy == 'fcfs':
        result = ResourceAllocationAlgorithms.fcfs_allocation(processes, resources, requests)
    elif policy == 'priority':
        result = ResourceAllocationAlgorithms.priority_allocation(processes, resources, requests)
    elif policy == 'round_robin':
        time_quantum = int(data.get('time_quantum', 1))
        result = ResourceAllocationAlgorithms.round_robin_allocation(processes, resources, requests, time_quantum)
    elif policy == 'fair_share':
        result = ResourceAllocationAlgorithms.fair_share_allocation(processes, resources)
    else:
        return jsonify({'error': 'Invalid policy'})

    return jsonify(result)

# Add routes for other concepts similarly
@app.route('/deadlock')
def deadlock():
    return render_template('deadlock.html')

@app.route('/memory_management')
def memory_management():
    return render_template('memory_management.html')

@app.route('/synchronization')
def synchronization():
    return render_template('synchronization.html')

@app.route('/file_systems')
def file_systems():
    return render_template('file_systems.html')

@app.route('/processes_threads')
def processes_threads():
    return render_template('processes_threads.html')

@app.route('/io_management')
def io_management():
    return render_template('io_management.html')

@app.route('/resource_allocation')
def resource_allocation():
    return render_template('resource_allocation.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
