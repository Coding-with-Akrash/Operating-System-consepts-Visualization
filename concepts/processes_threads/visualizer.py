import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QSpinBox,
    QLineEdit, QMessageBox, QGroupBox, QFormLayout, QTabWidget,
    QTextEdit, QListWidget, QListWidgetItem, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from gui.components.base_visualizer import BaseVisualizer
from .algorithms import (
    Process, Thread, ProcessState, ThreadState, ThreadModel,
    ProcessScheduler, ThreadManager, IPCManager, PCB, TCB
)

class ProcessStateDiagram(QWidget):
    """Visual representation of process states and transitions"""

    def __init__(self):
        super().__init__()
        self.processes = []
        self.setMinimumHeight(300)

    def set_processes(self, processes):
        self.processes = processes
        self.update()

    def paintEvent(self, event):
        if not self.processes:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        # Define state positions
        states = {
            ProcessState.NEW: (width * 0.1, height * 0.5),
            ProcessState.READY: (width * 0.3, height * 0.3),
            ProcessState.RUNNING: (width * 0.5, height * 0.5),
            ProcessState.WAITING: (width * 0.3, height * 0.7),
            ProcessState.TERMINATED: (width * 0.9, height * 0.5)
        }

        # Draw state circles
        state_colors = {
            ProcessState.NEW: QColor(200, 200, 255),
            ProcessState.READY: QColor(200, 255, 200),
            ProcessState.RUNNING: QColor(255, 255, 150),
            ProcessState.WAITING: QColor(255, 200, 200),
            ProcessState.TERMINATED: QColor(200, 200, 200)
        }

        for state, (x, y) in states.items():
            color = state_colors[state]
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.GlobalColor.black, 2))
            painter.drawEllipse(int(x - 40), int(y - 20), 80, 40)

            # Draw state label
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.drawText(int(x - 30), int(y + 5), state.value)

        # Draw transitions
        transitions = [
            (ProcessState.NEW, ProcessState.READY),
            (ProcessState.READY, ProcessState.RUNNING),
            (ProcessState.RUNNING, ProcessState.TERMINATED),
            (ProcessState.RUNNING, ProcessState.WAITING),
            (ProcessState.WAITING, ProcessState.READY)
        ]

        painter.setPen(QPen(Qt.GlobalColor.blue, 2))
        for from_state, to_state in transitions:
            x1, y1 = states[from_state]
            x2, y2 = states[to_state]
            painter.drawLine(int(x1 + 40), int(y1), int(x2 - 40), int(y2))

        # Draw processes as small circles at their current states
        process_colors = [QColor(255, 100, 100), QColor(100, 255, 100), QColor(100, 100, 255),
                         QColor(255, 255, 100), QColor(255, 100, 255)]

        for i, process in enumerate(self.processes):
            if process.state in states:
                x, y = states[process.state]
                color = process_colors[i % len(process_colors)]
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(Qt.GlobalColor.black, 1))
                painter.drawEllipse(int(x - 45 + (i % 3) * 15), int(y - 25 + (i // 3) * 15), 10, 10)

                # Draw PID
                painter.setFont(QFont("Arial", 8))
                painter.drawText(int(x - 50 + (i % 3) * 15), int(y - 30 + (i // 3) * 15), process.pid)

class PCBViewer(QWidget):
    """Display Process Control Block information"""

    def __init__(self):
        super().__init__()
        self.pcb = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Field", "Value"])
        self.table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(self.table)
        self.setLayout(layout)

    def set_pcb(self, pcb: PCB):
        self.pcb = pcb
        self.update_table()

    def update_table(self):
        if not self.pcb:
            return

        fields = [
            ("PID", self.pcb.pid),
            ("State", self.pcb.state.value),
            ("Priority", str(self.pcb.priority)),
            ("Program Counter", str(self.pcb.program_counter)),
            ("CPU Time Used", ".2f"),
            ("Creation Time", time.strftime("%H:%M:%S", time.localtime(self.pcb.creation_time))),
            ("Parent PID", self.pcb.parent_pid or "None"),
            ("Children", ", ".join(self.pcb.children_pids) if self.pcb.children_pids else "None")
        ]

        self.table.setRowCount(len(fields))
        for i, (field, value) in enumerate(fields):
            self.table.setItem(i, 0, QTableWidgetItem(field))
            self.table.setItem(i, 1, QTableWidgetItem(str(value)))

class ThreadVisualizer(QWidget):
    """Visualize threads within processes"""

    def __init__(self):
        super().__init__()
        self.processes = []
        self.setMinimumHeight(250)

    def set_processes(self, processes):
        self.processes = processes
        self.update()

    def paintEvent(self, event):
        if not self.processes:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        # Draw processes as rectangles
        process_height = height / len(self.processes) if self.processes else height
        colors = [QColor(255, 200, 200), QColor(200, 255, 200), QColor(200, 200, 255)]

        for i, process in enumerate(self.processes):
            y = i * process_height
            color = colors[i % len(colors)]

            # Draw process box
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.GlobalColor.black, 2))
            painter.drawRect(50, int(y + 10), int(width - 100), int(process_height - 20))

            # Process label
            painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            painter.drawText(60, int(y + 30), f"Process {process.pid}")

            # Draw threads as smaller rectangles inside
            if process.threads:
                thread_width = (width - 120) / len(process.threads)
                thread_colors = [QColor(255, 150, 150), QColor(150, 255, 150), QColor(150, 150, 255)]

                for j, thread in enumerate(process.threads):
                    tx = 60 + j * thread_width
                    thread_color = thread_colors[j % len(thread_colors)]
                    if thread.state == ThreadState.RUNNING:
                        thread_color = QColor(255, 255, 150)  # Yellow for running
                    elif thread.state == ThreadState.BLOCKED:
                        thread_color = QColor(255, 150, 150)  # Red for blocked

                    painter.setBrush(QBrush(thread_color))
                    painter.setPen(QPen(Qt.GlobalColor.black, 1))
                    painter.drawRect(int(tx), int(y + 40), int(thread_width - 5), int(process_height - 50))

                    # Thread label
                    painter.setFont(QFont("Arial", 8))
                    painter.drawText(int(tx + 5), int(y + 55), thread.tid)

class ContextSwitchVisualizer(QWidget):
    """Animate context switching"""

    def __init__(self):
        super().__init__()
        self.timeline = []
        self.current_step = 0
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.next_step)
        self.setMinimumHeight(200)

    def set_timeline(self, timeline):
        self.timeline = timeline
        self.current_step = 0
        self.update()

    def start_animation(self):
        self.current_step = 0
        self.animation_timer.start(500)  # 500ms per step

    def stop_animation(self):
        self.animation_timer.stop()

    def next_step(self):
        if self.current_step < len(self.timeline) - 1:
            self.current_step += 1
            self.update()
        else:
            self.animation_timer.stop()

    def paintEvent(self, event):
        if not self.timeline:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        # Draw timeline
        max_time = max((t[0] for t in self.timeline), default=0) + 1
        if max_time == 0:
            return

        # Time axis
        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        painter.drawLine(50, height - 50, width - 20, height - 50)

        # Time labels
        painter.setFont(QFont("Arial", 8))
        for t in range(0, max_time, max(1, max_time // 10)):
            x = 50 + (t / max_time) * (width - 70)
            painter.drawLine(int(x), height - 45, int(x), height - 55)
            painter.drawText(int(x) - 10, height - 30, str(t))

        # Draw process states up to current step
        colors = {
            ProcessState.NEW: QColor(200, 200, 255),
            ProcessState.READY: QColor(200, 255, 200),
            ProcessState.RUNNING: QColor(255, 255, 150),
            ProcessState.WAITING: QColor(255, 200, 200),
            ProcessState.TERMINATED: QColor(200, 200, 200)
        }

        process_tracks = {}
        track_height = 20
        current_y = 20

        for time, pid, state in self.timeline[:self.current_step + 1]:
            if pid not in process_tracks:
                process_tracks[pid] = current_y
                current_y += track_height + 5

            y = process_tracks[pid]
            x = 50 + (time / max_time) * (width - 70)

            color = colors.get(state, QColor(150, 150, 150))
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.GlobalColor.black, 1))
            painter.drawRect(int(x - 5), y, 10, track_height)

            # Label
            painter.setFont(QFont("Arial", 8))
            painter.drawText(int(x - 5), y - 5, f"{pid}:{state.value[0]}")

class IPCVisualizer(QWidget):
    """Visualize Inter-Process Communication"""

    def __init__(self):
        super().__init__()
        self.ipc_manager = IPCManager()
        self.processes = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Message sending controls
        send_group = QGroupBox("Send Message")
        send_layout = QHBoxLayout()

        self.from_combo = QComboBox()
        self.to_combo = QComboBox()
        self.message_edit = QLineEdit()
        self.send_btn = QPushButton("Send")

        send_layout.addWidget(QLabel("From:"))
        send_layout.addWidget(self.from_combo)
        send_layout.addWidget(QLabel("To:"))
        send_layout.addWidget(self.to_combo)
        send_layout.addWidget(QLabel("Message:"))
        send_layout.addWidget(self.message_edit)
        send_layout.addWidget(self.send_btn)

        send_group.setLayout(send_layout)
        layout.addWidget(send_group)

        # Message queues display
        self.queues_text = QTextEdit()
        self.queues_text.setReadOnly(True)
        self.queues_text.setMaximumHeight(150)
        layout.addWidget(self.queues_text)

        self.setLayout(layout)

        self.send_btn.clicked.connect(self.send_message)

    def set_processes(self, processes):
        self.processes = processes
        self.from_combo.clear()
        self.to_combo.clear()
        for p in processes:
            self.from_combo.addItem(p.pid)
            self.to_combo.addItem(p.pid)
        self.update_queues()

    def send_message(self):
        from_pid = self.from_combo.currentText()
        to_pid = self.to_combo.currentText()
        message = self.message_edit.text().strip()

        if not message:
            QMessageBox.warning(self, "Error", "Please enter a message")
            return

        self.ipc_manager.send_message(from_pid, to_pid, message)
        self.message_edit.clear()
        self.update_queues()

    def update_queues(self):
        text = "Message Queues:\n\n"
        for process in self.processes:
            queue_size = self.ipc_manager.get_queue_size(process.pid)
            text += f"Process {process.pid}: {queue_size} messages\n"

            # Show messages
            for i in range(queue_size):
                msg = self.ipc_manager.receive_message(process.pid)
                if msg:
                    from_pid, content, timestamp = msg
                    time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
                    text += f"  [{time_str}] From {from_pid}: {content}\n"
                    # Put it back
                    self.ipc_manager.send_message(from_pid, process.pid, content)

        self.queues_text.setText(text)

class ProcessesThreadsVisualizer(BaseVisualizer):
    def __init__(self):
        self.state_diagram = ProcessStateDiagram()
        self.pcb_viewer = PCBViewer()
        self.thread_viz = ThreadVisualizer()
        self.context_switch_viz = ContextSwitchVisualizer()
        self.ipc_viz = IPCVisualizer()

        # Create tab widget before super() since create_visualization_widget needs it
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.state_diagram, "State Diagram")
        self.tab_widget.addTab(self.pcb_viewer, "PCB Viewer")
        self.tab_widget.addTab(self.thread_viz, "Thread View")
        self.tab_widget.addTab(self.context_switch_viz, "Context Switching")
        self.tab_widget.addTab(self.ipc_viz, "IPC")

        super().__init__("Processes and Threads")
        self.processes = []
        self.threads = []
        self.current_demo = "process_lifecycle"

    def setup_specific_ui(self):
        # Demo selection
        demo_group = QGroupBox("Demonstration")
        demo_layout = QHBoxLayout()
        self.demo_combo = QComboBox()
        self.demo_combo.addItems([
            "Process Lifecycle",
            "Process Control Block",
            "Thread Management",
            "Context Switching",
            "Inter-Process Communication"
        ])
        self.demo_combo.currentTextChanged.connect(self.on_demo_changed)
        demo_layout.addWidget(QLabel("Demo:"))
        demo_layout.addWidget(self.demo_combo)
        demo_layout.addStretch()
        demo_group.setLayout(demo_layout)
        self.layout().insertWidget(1, demo_group)

        # Process input
        input_group = QGroupBox("Process Management")
        input_layout = QFormLayout()

        self.pid_edit = QLineEdit("P1")
        self.arrival_edit = QSpinBox()
        self.arrival_edit.setRange(0, 100)
        self.burst_edit = QSpinBox()
        self.burst_edit.setRange(1, 50)
        self.burst_edit.setValue(10)

        input_layout.addRow("Process ID:", self.pid_edit)
        input_layout.addRow("Arrival Time:", self.arrival_edit)
        input_layout.addRow("Burst Time:", self.burst_edit)

        add_process_btn = QPushButton("Add Process")
        add_process_btn.clicked.connect(self.add_process)
        input_layout.addRow(add_process_btn)

        # Thread input
        self.tid_edit = QLineEdit("T1")
        self.thread_model_combo = QComboBox()
        self.thread_model_combo.addItems([model.value for model in ThreadModel])

        input_layout.addRow("Thread ID:", self.tid_edit)
        input_layout.addRow("Thread Model:", self.thread_model_combo)

        add_thread_btn = QPushButton("Add Thread to Process")
        add_thread_btn.clicked.connect(self.add_thread)
        input_layout.addRow(add_thread_btn)

        input_group.setLayout(input_layout)
        self.layout().insertWidget(2, input_group)

        # Process table
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(4)
        self.process_table.setHorizontalHeaderLabels(["PID", "State", "Threads", "Burst Left"])
        self.layout().insertWidget(3, self.process_table)

        # Tab widget for different visualizations
        self.tab_widget = QTabWidget()
        self.layout().addWidget(self.tab_widget)

        # Add visualization tabs
        self.tab_widget.addTab(self.state_diagram, "State Diagram")
        self.tab_widget.addTab(self.pcb_viewer, "PCB Viewer")
        self.tab_widget.addTab(self.thread_viz, "Thread View")
        self.tab_widget.addTab(self.context_switch_viz, "Context Switching")
        self.tab_widget.addTab(self.ipc_viz, "IPC")

        # Results area
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(100)
        self.layout().addWidget(self.results_text)

    def create_visualization_widget(self):
        # Return the tab widget as the main visualization
        return self.tab_widget

    def on_demo_changed(self, demo):
        demo_map = {
            "Process Lifecycle": "process_lifecycle",
            "Process Control Block": "pcb",
            "Thread Management": "threads",
            "Context Switching": "context_switching",
            "Inter-Process Communication": "ipc"
        }
        self.current_demo = demo_map.get(demo, "process_lifecycle")
        self.update_visualizations()

    def add_process(self):
        try:
            pid = self.pid_edit.text().strip()
            if not pid:
                raise ValueError("Process ID cannot be empty")

            arrival = self.arrival_edit.value()
            burst = self.burst_edit.value()

            # Check for duplicate PID
            if any(p.pid == pid for p in self.processes):
                QMessageBox.warning(self, "Error", f"Process {pid} already exists")
                return

            process = Process(pid, arrival, burst)
            self.processes.append(process)
            self.update_process_table()
            self.update_visualizations()

            # Clear inputs
            self.pid_edit.setText(f"P{len(self.processes) + 1}")

        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def add_thread(self):
        if not self.processes:
            QMessageBox.warning(self, "Error", "Create a process first")
            return

        try:
            tid = self.tid_edit.text().strip()
            if not tid:
                raise ValueError("Thread ID cannot be empty")

            model_name = self.thread_model_combo.currentText()
            model = ThreadModel.USER_LEVEL
            for m in ThreadModel:
                if m.value == model_name:
                    model = m
                    break

            # Add to last process
            process = self.processes[-1]
            thread = Thread(tid, process.pid, model)
            process.add_thread(thread)
            self.threads.append(thread)
            self.update_process_table()
            self.update_visualizations()

            # Clear inputs
            self.tid_edit.setText(f"T{len(self.threads) + 1}")

        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def update_process_table(self):
        self.process_table.setRowCount(len(self.processes))
        for i, process in enumerate(self.processes):
            self.process_table.setItem(i, 0, QTableWidgetItem(process.pid))
            self.process_table.setItem(i, 1, QTableWidgetItem(process.state.value))
            self.process_table.setItem(i, 2, QTableWidgetItem(str(len(process.threads))))
            self.process_table.setItem(i, 3, QTableWidgetItem(str(process.remaining_time)))

    def update_visualizations(self):
        self.state_diagram.set_processes(self.processes)
        self.thread_viz.set_processes(self.processes)
        self.ipc_viz.set_processes(self.processes)

        if self.processes:
            self.pcb_viewer.set_pcb(self.processes[0].pcb)

    def on_play(self):
        if not self.processes:
            QMessageBox.warning(self, "Error", "No processes to simulate")
            return

        if self.current_demo == "process_lifecycle":
            result = ProcessScheduler.simulate_process_lifecycle(self.processes.copy())
            self.context_switch_viz.set_timeline(result['timeline'])
            self.context_switch_viz.start_animation()
            self.display_results(result)
        elif self.current_demo == "threads":
            if self.threads:
                result = ThreadManager.simulate_thread_execution(self.threads.copy())
                self.context_switch_viz.set_timeline(result['timeline'])
                self.context_switch_viz.start_animation()
                self.display_results(result)
        elif self.current_demo == "context_switching":
            result = ProcessScheduler.simulate_process_lifecycle(self.processes.copy())
            self.context_switch_viz.set_timeline(result['timeline'])
            self.context_switch_viz.start_animation()
            self.display_results(result)

        self.update_visualizations()
        self.update_status("Simulation running")

    def on_pause(self):
        self.context_switch_viz.stop_animation()
        self.update_status("Simulation paused")

    def on_reset(self):
        self.context_switch_viz.stop_animation()
        self.processes = []
        self.threads = []
        self.update_process_table()
        self.update_visualizations()
        self.results_text.clear()
        self.update_status("Reset")

    def display_results(self, result):
        if 'timeline' in result:
            text = f"Simulation completed in {result.get('total_time', 0)} time units\n"
            text += f"Timeline events: {len(result['timeline'])}\n"
            if 'completed_processes' in result:
                text += f"Completed processes: {len(result['completed_processes'])}\n"
            if 'completed_threads' in result:
                text += f"Completed threads: {len(result['completed_threads'])}\n"
        else:
            text = "Simulation completed"

        self.results_text.setText(text)