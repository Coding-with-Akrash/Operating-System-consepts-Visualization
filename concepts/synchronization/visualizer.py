from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QSpinBox,
    QGroupBox, QFormLayout, QTextEdit, QListWidget, QListWidgetItem,
    QSplitter, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem,
    QGraphicsRectItem, QGraphicsTextItem, QGraphicsLineItem
)
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from gui.components.base_visualizer import BaseVisualizer
from .algorithms import (
    SynchronizationSimulator, SynchronizationProcess,
    Semaphore, Mutex, Monitor, ProducerConsumer,
    DiningPhilosophers, ReadersWriters
)

class ProcessVisualizationWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.processes = []
        self.setMinimumHeight(200)

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
        process_height = 40
        spacing = 10

        for i, process in enumerate(self.processes):
            y = i * (process_height + spacing) + 10

            # Draw process box
            state_colors = {
                'ready': QColor(100, 255, 100),
                'running': QColor(255, 255, 100),
                'waiting': QColor(255, 100, 100),
                'terminated': QColor(200, 200, 200)
            }

            color = state_colors.get(process['state'], QColor(200, 200, 200))
            painter.fillRect(10, y, width - 20, process_height, color)
            painter.setPen(QPen(Qt.GlobalColor.black, 2))
            painter.drawRect(10, y, width - 20, process_height)

            # Draw process info
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.drawText(20, y + 15, f"{process['name']} ({process['pid']})")
            painter.setFont(QFont("Arial", 8))
            painter.drawText(20, y + 30, f"State: {process['state']}")
            if process['waiting_for']:
                painter.drawText(20, y + 45, f"Waiting for: {process['waiting_for']}")

class SynchronizationPrimitivesWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.primitives = {}
        self.setMinimumHeight(150)

    def set_primitives(self, semaphores, mutexes, monitors):
        self.primitives = {
            'semaphores': semaphores,
            'mutexes': mutexes,
            'monitors': monitors
        }
        self.update()

    def paintEvent(self, event):
        if not self.primitives:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        y_offset = 10

        # Draw semaphores
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.drawText(10, y_offset + 15, "Semaphores:")
        y_offset += 25

        for name, data in self.primitives['semaphores'].items():
            painter.setFont(QFont("Arial", 10))
            painter.drawText(20, y_offset + 15, f"{name}: value={data['value']}, waiting={data['waiting']}")
            y_offset += 20

        y_offset += 10

        # Draw mutexes
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.drawText(10, y_offset + 15, "Mutexes:")
        y_offset += 25

        for name, data in self.primitives['mutexes'].items():
            painter.setFont(QFont("Arial", 10))
            owner = data['owner'] or "None"
            painter.drawText(20, y_offset + 15, f"{name}: locked={data['locked']}, owner={owner}, waiting={data['waiting']}")
            y_offset += 20

        y_offset += 10

        # Draw monitors
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.drawText(10, y_offset + 15, "Monitors:")
        y_offset += 25

        for name, data in self.primitives['monitors'].items():
            painter.setFont(QFont("Arial", 10))
            cv_info = ", ".join([f"{cv}: {count}" for cv, count in data['condition_vars'].items()])
            painter.drawText(20, y_offset + 15, f"{name}: CVs={cv_info}")
            y_offset += 20

class ProducerConsumerVisualization(QWidget):
    def __init__(self):
        super().__init__()
        self.buffer = []
        self.buffer_size = 5
        self.setMinimumHeight(100)

    def set_data(self, buffer, buffer_size):
        self.buffer = buffer
        self.buffer_size = buffer_size
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        slot_width = (width - 40) / self.buffer_size
        slot_height = height - 40

        # Draw buffer slots
        for i in range(self.buffer_size):
            x = 20 + i * slot_width
            y = 20

            # Slot background
            painter.setPen(QPen(Qt.GlobalColor.black, 2))
            if i < len(self.buffer):
                painter.fillRect(int(x), y, int(slot_width - 5), slot_height, QColor(100, 200, 255))
                painter.drawText(int(x + slot_width/2 - 10), y + slot_height/2 + 5, str(self.buffer[i]))
            else:
                painter.fillRect(int(x), y, int(slot_width - 5), slot_height, QColor(240, 240, 240))

            painter.drawRect(int(x), y, int(slot_width - 5), slot_height)

        # Draw labels
        painter.setFont(QFont("Arial", 10))
        painter.drawText(10, 15, "Buffer:")
        painter.drawText(10, height - 5, f"Size: {len(self.buffer)}/{self.buffer_size}")

class DiningPhilosophersVisualization(QWidget):
    def __init__(self):
        super().__init__()
        self.states = []
        self.num_philosophers = 5
        self.setMinimumHeight(200)

    def set_data(self, states):
        self.states = states
        self.num_philosophers = len(states)
        self.update()

    def paintEvent(self, event):
        if not self.states:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        center_x = width / 2
        center_y = height / 2
        radius = min(width, height) / 3

        # Draw table
        painter.setPen(QPen(Qt.GlobalColor.black, 3))
        painter.setBrush(QBrush(QColor(139, 69, 19)))  # Brown table
        painter.drawEllipse(int(center_x - radius), int(center_y - radius),
                          int(radius * 2), int(radius * 2))

        # Draw philosophers and chopsticks
        state_colors = {
            'thinking': QColor(200, 200, 200),
            'hungry': QColor(255, 255, 100),
            'eating': QColor(100, 255, 100)
        }

        for i in range(self.num_philosophers):
            angle = 2 * 3.14159 * i / self.num_philosophers
            x = center_x + radius * 1.5 * (i % 2 == 0 and 1 or -1) * (0.8 if i % 2 == 0 else 0.6)
            y = center_y + radius * 1.2 * (i // 2 == 0 and -1 or 1)

            # Draw philosopher
            color = state_colors.get(self.states[i], QColor(200, 200, 200))
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.GlobalColor.black, 2))
            painter.drawEllipse(int(x - 15), int(y - 15), 30, 30)

            # Draw chopsticks
            next_i = (i + 1) % self.num_philosophers
            angle_next = 2 * 3.14159 * next_i / self.num_philosophers

            # Position chopsticks between philosophers
            chopstick_x = center_x + radius * 0.9 * (0.8 if i % 2 == 0 else 0.6)
            chopstick_y = center_y + radius * 0.9 * (i // 2 == 0 and -1 or 1)

            painter.setPen(QPen(Qt.GlobalColor.black, 4))
            painter.drawLine(int(chopstick_x - 10), int(chopstick_y), int(chopstick_x + 10), int(chopstick_y))

            # Label philosopher
            painter.setFont(QFont("Arial", 8))
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.drawText(int(x - 10), int(y + 40), f"P{i}")
            painter.drawText(int(x - 20), int(y + 55), self.states[i])

class ReadersWritersVisualization(QWidget):
    def __init__(self):
        super().__init__()
        self.read_count = 0
        self.writer_active = False
        self.setMinimumHeight(100)

    def set_data(self, read_count, writer_active):
        self.read_count = read_count
        self.writer_active = writer_active
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        # Draw database/resource
        painter.setPen(QPen(Qt.GlobalColor.black, 3))
        painter.setBrush(QBrush(QColor(255, 255, 200)))
        painter.drawRect(width//2 - 50, height//2 - 25, 100, 50)

        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.drawText(width//2 - 30, height//2 + 5, "Database")

        # Draw status
        painter.setFont(QFont("Arial", 10))
        status_y = height//2 + 40
        painter.drawText(10, status_y, f"Readers active: {self.read_count}")
        painter.drawText(10, status_y + 15, f"Writer active: {self.writer_active}")

        # Draw access indicators
        if self.writer_active:
            painter.setPen(QPen(QColor(255, 100, 100), 3))
            painter.setBrush(QBrush(QColor(255, 100, 100, 100)))
            painter.drawRect(width//2 - 60, height//2 - 35, 120, 60)
            painter.drawText(width//2 - 25, height//2 - 40, "WRITING")

class SynchronizationVisualizer(BaseVisualizer):
    def __init__(self):
        self.simulator = SynchronizationSimulator()
        self.current_problem = "Semaphores"
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_step)
        self.animation_steps = []
        self.current_step = 0

        # Visualization widgets
        self.process_widget = ProcessVisualizationWidget()
        self.primitives_widget = SynchronizationPrimitivesWidget()
        self.problem_widget = None

        super().__init__("Process Synchronization")
        self.setup_specific_ui()

    def setup_specific_ui(self):
        # Problem selection
        problem_group = QGroupBox("Synchronization Problem")
        problem_layout = QHBoxLayout()
        self.problem_combo = QComboBox()
        self.problem_combo.addItems([
            "Semaphores", "Mutexes", "Monitors",
            "Producer-Consumer", "Dining Philosophers", "Readers-Writers"
        ])
        self.problem_combo.currentTextChanged.connect(self.on_problem_changed)
        problem_layout.addWidget(QLabel("Problem:"))
        problem_layout.addWidget(self.problem_combo)
        problem_layout.addStretch()
        problem_group.setLayout(problem_layout)
        self.layout().insertWidget(1, problem_group)

        # Controls for specific problems
        self.setup_problem_controls()

        # Visualization area
        self.setup_visualization_area()

        # Log area
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        self.layout().addWidget(QLabel("Execution Log:"))
        self.layout().addWidget(self.log_text)

    def setup_problem_controls(self):
        # Producer-Consumer controls
        pc_group = QGroupBox("Producer-Consumer Controls")
        pc_layout = QHBoxLayout()
        self.pc_buffer_size_spin = QSpinBox()
        self.pc_buffer_size_spin.setRange(3, 10)
        self.pc_buffer_size_spin.setValue(5)
        pc_layout.addWidget(QLabel("Buffer Size:"))
        pc_layout.addWidget(self.pc_buffer_size_spin)

        self.pc_producer_btn = QPushButton("Add Producer")
        self.pc_producer_btn.clicked.connect(self.add_producer)
        pc_layout.addWidget(self.pc_producer_btn)

        self.pc_consumer_btn = QPushButton("Add Consumer")
        self.pc_consumer_btn.clicked.connect(self.add_consumer)
        pc_layout.addWidget(self.pc_consumer_btn)

        pc_layout.addStretch()
        pc_group.setLayout(pc_layout)
        self.layout().insertWidget(2, pc_group)
        pc_group.hide()

        # Dining Philosophers controls
        dp_group = QGroupBox("Dining Philosophers Controls")
        dp_layout = QHBoxLayout()
        self.dp_philosopher_count_spin = QSpinBox()
        self.dp_philosopher_count_spin.setRange(3, 8)
        self.dp_philosopher_count_spin.setValue(5)
        dp_layout.addWidget(QLabel("Philosophers:"))
        dp_layout.addWidget(self.dp_philosopher_count_spin)

        self.dp_action_combo = QComboBox()
        self.dp_action_combo.addItems([f"Philosopher {i} Pickup" for i in range(5)] +
                                    [f"Philosopher {i} Putdown" for i in range(5)])
        dp_layout.addWidget(self.dp_action_combo)

        self.dp_execute_btn = QPushButton("Execute Action")
        self.dp_execute_btn.clicked.connect(self.execute_dp_action)
        dp_layout.addWidget(self.dp_execute_btn)

        dp_layout.addStretch()
        dp_group.setLayout(dp_layout)
        self.layout().insertWidget(3, dp_group)
        dp_group.hide()

        # Readers-Writers controls
        rw_group = QGroupBox("Readers-Writers Controls")
        rw_layout = QHBoxLayout()

        self.rw_action_combo = QComboBox()
        self.rw_action_combo.addItems([
            "Reader Start Read", "Reader End Read",
            "Writer Start Write", "Writer End Write"
        ])
        rw_layout.addWidget(self.rw_action_combo)

        self.rw_execute_btn = QPushButton("Execute Action")
        self.rw_execute_btn.clicked.connect(self.execute_rw_action)
        rw_layout.addWidget(self.rw_execute_btn)

        rw_layout.addStretch()
        rw_group.setLayout(rw_group)
        self.layout().insertWidget(4, rw_group)
        rw_group.hide()

        self.control_groups = {
            "Producer-Consumer": pc_group,
            "Dining Philosophers": dp_group,
            "Readers-Writers": rw_group
        }

    def setup_visualization_area(self):
        # Create splitter for visualization
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top part: Processes and Primitives
        top_widget = QWidget()
        top_layout = QVBoxLayout()
        top_layout.addWidget(QLabel("Processes:"))
        top_layout.addWidget(self.process_widget)
        top_layout.addWidget(QLabel("Synchronization Primitives:"))
        top_layout.addWidget(self.primitives_widget)
        top_widget.setLayout(top_layout)

        # Bottom part: Problem-specific visualization
        self.problem_container = QWidget()
        self.problem_layout = QVBoxLayout()
        self.problem_layout.addWidget(QLabel("Problem Visualization:"))
        self.problem_container.setLayout(self.problem_layout)

        splitter.addWidget(top_widget)
        splitter.addWidget(self.problem_container)
        splitter.setSizes([300, 200])

        self.layout().insertWidget(5, splitter)

    def create_visualization_widget(self):
        # This is handled in setup_visualization_area
        return QWidget()

    def on_problem_changed(self, problem):
        self.current_problem = problem
        self.reset_simulation()

        # Hide all control groups
        for group in self.control_groups.values():
            group.hide()

        # Show relevant control group
        if problem in self.control_groups:
            self.control_groups[problem].show()

        # Update problem-specific visualization
        self.update_problem_visualization()

    def reset_simulation(self):
        self.simulator = SynchronizationSimulator()
        self.animation_steps = []
        self.current_step = 0
        self.log_text.clear()

        if self.current_problem == "Producer-Consumer":
            buffer_size = self.pc_buffer_size_spin.value()
            self.simulator.setup_producer_consumer(buffer_size)
        elif self.current_problem == "Dining Philosophers":
            num_phil = self.dp_philosopher_count_spin.value()
            self.simulator.setup_dining_philosophers(num_phil)
            # Update combo box
            self.dp_action_combo.clear()
            self.dp_action_combo.addItems([f"Philosopher {i} Pickup" for i in range(num_phil)] +
                                        [f"Philosopher {i} Putdown" for i in range(num_phil)])
        elif self.current_problem == "Readers-Writers":
            self.simulator.setup_readers_writers()

        self.update_visualization()

    def update_visualization(self):
        state = self.simulator.get_state()
        self.process_widget.set_processes(state['processes'])
        self.primitives_widget.set_primitives(
            state['semaphores'], state['mutexes'], state['monitors']
        )
        self.update_problem_visualization()

    def update_problem_visualization(self):
        # Clear current problem widget
        if self.problem_widget:
            self.problem_layout.removeWidget(self.problem_widget)
            self.problem_widget.deleteLater()
            self.problem_widget = None

        state = self.simulator.get_state()

        if self.current_problem == "Producer-Consumer" and state['producer_consumer']:
            self.problem_widget = ProducerConsumerVisualization()
            pc_data = state['producer_consumer']
            self.problem_widget.set_data(pc_data['buffer'], pc_data['buffer_size'])
        elif self.current_problem == "Dining Philosophers" and state['dining_philosophers']:
            self.problem_widget = DiningPhilosophersVisualization()
            dp_data = state['dining_philosophers']
            self.problem_widget.set_data(dp_data['states'])
        elif self.current_problem == "Readers-Writers" and state['readers_writers']:
            self.problem_widget = ReadersWritersVisualization()
            rw_data = state['readers_writers']
            self.problem_widget.set_data(rw_data['read_count'], rw_data['writer_active'])
        else:
            self.problem_widget = QLabel("Select a synchronization problem to visualize")

        if self.problem_widget:
            self.problem_layout.addWidget(self.problem_widget)

    def add_producer(self):
        if self.simulator.producer_consumer:
            producer_id = len([p for p in self.simulator.processes if p.name.startswith("Producer")])
            producer = self.simulator.add_process(f"Producer{producer_id}", f"Producer {producer_id}")
            item = random.randint(1, 100)
            result = self.simulator.producer_consumer.produce(producer, item)
            self.log_steps(result['steps'])
            self.update_visualization()

    def add_consumer(self):
        if self.simulator.producer_consumer:
            consumer_id = len([p for p in self.simulator.processes if p.name.startswith("Consumer")])
            consumer = self.simulator.add_process(f"Consumer{consumer_id}", f"Consumer {consumer_id}")
            result = self.simulator.producer_consumer.consume(consumer)
            self.log_steps(result['steps'])
            self.update_visualization()

    def execute_dp_action(self):
        if not self.simulator.dining_philosophers:
            return

        action_text = self.dp_action_combo.currentText()
        parts = action_text.split()
        philosopher_id = int(parts[1])
        action = parts[2].lower()

        if action == "pickup":
            result = self.simulator.dining_philosophers.pickup_chopsticks(philosopher_id)
        else:  # putdown
            result = self.simulator.dining_philosophers.putdown_chopsticks(philosopher_id)

        self.log_steps(result['steps'])
        self.update_visualization()

    def execute_rw_action(self):
        if not self.simulator.readers_writers:
            return

        action_text = self.rw_action_combo.currentText()
        if action_text == "Reader Start Read":
            reader_id = len([p for p in self.simulator.processes if p.name.startswith("Reader") and p.state.value == "ready"])
            if reader_id < len([p for p in self.simulator.processes if p.name.startswith("Reader")]):
                reader = [p for p in self.simulator.processes if p.name.startswith("Reader")][reader_id]
                result = self.simulator.readers_writers.start_read(reader)
                self.log_steps(result['steps'])
        elif action_text == "Reader End Read":
            active_readers = [p for p in self.simulator.processes if p.name.startswith("Reader") and p.state.value == "running"]
            if active_readers:
                reader = active_readers[0]
                result = self.simulator.readers_writers.end_read(reader)
                self.log_steps(result['steps'])
        elif action_text == "Writer Start Write":
            writer_id = len([p for p in self.simulator.processes if p.name.startswith("Writer") and p.state.value == "ready"])
            if writer_id < len([p for p in self.simulator.processes if p.name.startswith("Writer")]):
                writer = [p for p in self.simulator.processes if p.name.startswith("Writer")][writer_id]
                result = self.simulator.readers_writers.start_write(writer)
                self.log_steps(result['steps'])
        elif action_text == "Writer End Write":
            active_writers = [p for p in self.simulator.processes if p.name.startswith("Writer") and p.state.value == "running"]
            if active_writers:
                writer = active_writers[0]
                result = self.simulator.readers_writers.end_write(writer)
                self.log_steps(result['steps'])

        self.update_visualization()

    def log_steps(self, steps):
        for step in steps:
            self.log_text.append(step)

    def on_play(self):
        self.reset_simulation()
        self.update_status("Simulation started")

    def on_pause(self):
        self.animation_timer.stop()
        self.update_status("Simulation paused")

    def on_reset(self):
        self.reset_simulation()
        self.update_status("Simulation reset")

    def animate_step(self):
        if self.current_step < len(self.animation_steps):
            # Execute next step
            self.current_step += 1
        else:
            self.animation_timer.stop()
            self.update_status("Animation completed")