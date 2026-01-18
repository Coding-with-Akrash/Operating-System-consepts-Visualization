from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QSpinBox,
    QGroupBox, QFormLayout, QProgressBar, QTextEdit,
    QSplitter, QListWidget, QListWidgetItem, QMessageBox, QCheckBox, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from gui.components.base_visualizer import BaseVisualizer
from .algorithms import (
    IORequest, IORequestType, DeviceDriver, Buffer, Spooler,
    InterruptController, IOScheduler
)
import random
import time

class DiskVisualizationWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.requests = []
        self.current_position = 0
        self.max_blocks = 100
        self.setMinimumHeight(200)

    def set_data(self, requests, current_position):
        self.requests = requests
        self.current_position = current_position
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        # Draw disk tracks
        track_height = height - 60
        painter.setPen(QPen(Qt.GlobalColor.gray, 1))
        for i in range(0, self.max_blocks + 1, 10):
            x = 50 + (i / self.max_blocks) * (width - 100)
            painter.drawLine(int(x), 20, int(x), track_height)

        # Draw block numbers
        painter.setFont(QFont("Arial", 8))
        for i in range(0, self.max_blocks + 1, 20):
            x = 50 + (i / self.max_blocks) * (width - 100)
            painter.drawText(int(x) - 10, track_height + 15, str(i))

        # Draw requests as dots
        painter.setPen(QPen(Qt.GlobalColor.red, 3))
        painter.setBrush(QBrush(Qt.GlobalColor.red))
        for request in self.requests:
            x = 50 + (request.block_number / self.max_blocks) * (width - 100)
            y = track_height / 2
            painter.drawEllipse(int(x) - 3, int(y) - 3, 6, 6)

        # Draw disk head
        painter.setPen(QPen(Qt.GlobalColor.blue, 3))
        painter.setBrush(QBrush(Qt.GlobalColor.blue))
        head_x = 50 + (self.current_position / self.max_blocks) * (width - 100)
        painter.drawRect(int(head_x) - 5, track_height - 10, 10, 10)

        # Draw head position label
        painter.setPen(QPen(Qt.GlobalColor.black))
        painter.drawText(int(head_x) - 15, track_height - 15, f"Head: {self.current_position}")

class BufferVisualizationWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.buffer = None
        self.setMinimumHeight(100)

    def set_buffer(self, buffer):
        self.buffer = buffer
        self.update()

    def paintEvent(self, event):
        if not self.buffer:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        # Draw buffer slots
        slot_width = width / self.buffer.size
        for i in range(self.buffer.size):
            x = i * slot_width
            color = QColor(200, 200, 200) if i >= len(self.buffer.data) else QColor(100, 200, 100)
            painter.fillRect(int(x), 10, int(slot_width) - 2, height - 20, color)
            painter.setPen(QPen(Qt.GlobalColor.black, 1))
            painter.drawRect(int(x), 10, int(slot_width) - 2, height - 20)

            # Draw data if present
            if i < len(self.buffer.data):
                painter.setPen(QPen(Qt.GlobalColor.black))
                painter.drawText(int(x + slot_width/2 - 10), height/2 + 5, str(self.buffer.data[i]))

class IOManagementVisualizer(BaseVisualizer):
    def __init__(self):
        self.disk_widget = DiskVisualizationWidget()
        self.buffer_widget = BufferVisualizationWidget()
        super().__init__("I/O Management")
        self.requests = []
        self.device_driver = DeviceDriver("Disk1")
        self.buffer = Buffer(5)
        self.spooler = Spooler(self.device_driver)
        self.interrupt_controller = InterruptController()
        self.current_algorithm = "FCFS"
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_step)
        self.animation_index = 0
        self.schedule_result = None
        self.setup_specific_ui()

        # Setup interrupt handlers
        self.interrupt_controller.register_handler("io_complete", self.on_io_complete)
        self.interrupt_controller.register_handler("buffer_full", self.on_buffer_full)

    def setup_specific_ui(self):
        # Algorithm selection
        algo_group = QGroupBox("I/O Scheduling Algorithm")
        algo_layout = QHBoxLayout()
        self.algo_combo = QComboBox()
        self.algo_combo.addItems(["FCFS", "SSTF", "SCAN"])
        self.algo_combo.currentTextChanged.connect(self.on_algorithm_changed)
        algo_layout.addWidget(QLabel("Algorithm:"))
        algo_layout.addWidget(self.algo_combo)
        algo_layout.addStretch()
        algo_group.setLayout(algo_layout)
        self.layout().insertWidget(1, algo_group)

        # Request input
        input_group = QGroupBox("I/O Request Input")
        input_layout = QFormLayout()

        self.request_id_edit = QLineEdit("R1")
        self.process_id_edit = QLineEdit("P1")
        self.request_type_combo = QComboBox()
        self.request_type_combo.addItems(["read", "write"])
        self.block_number_spin = QSpinBox()
        self.block_number_spin.setRange(0, 99)

        input_layout.addRow("Request ID:", self.request_id_edit)
        input_layout.addRow("Process ID:", self.process_id_edit)
        input_layout.addRow("Type:", self.request_type_combo)
        input_layout.addRow("Block Number:", self.block_number_spin)

        add_btn = QPushButton("Add Request")
        add_btn.clicked.connect(self.add_request)
        input_layout.addRow(add_btn)

        # Generate random requests button
        random_btn = QPushButton("Generate Random Requests")
        random_btn.clicked.connect(self.generate_random_requests)
        input_layout.addRow(random_btn)

        input_group.setLayout(input_layout)
        self.layout().insertWidget(2, input_group)

        # Request queue display
        queue_group = QGroupBox("I/O Request Queue")
        queue_layout = QVBoxLayout()
        self.request_table = QTableWidget()
        self.request_table.setColumnCount(4)
        self.request_table.setHorizontalHeaderLabels(["ID", "Process", "Type", "Block"])
        queue_layout.addWidget(self.request_table)
        queue_group.setLayout(queue_layout)
        self.layout().insertWidget(3, queue_group)

        # Simulation controls
        sim_group = QGroupBox("Simulation Controls")
        sim_layout = QHBoxLayout()

        self.buffer_size_spin = QSpinBox()
        self.buffer_size_spin.setRange(1, 10)
        self.buffer_size_spin.setValue(5)
        self.buffer_size_spin.valueChanged.connect(self.on_buffer_size_changed)
        sim_layout.addWidget(QLabel("Buffer Size:"))
        sim_layout.addWidget(self.buffer_size_spin)

        self.spooling_check = QCheckBox("Enable Spooling")
        sim_layout.addWidget(self.spooling_check)

        sim_layout.addStretch()
        sim_group.setLayout(sim_layout)
        self.layout().insertWidget(4, sim_group)

        # Interrupt log
        interrupt_group = QGroupBox("Interrupt Log")
        interrupt_layout = QVBoxLayout()
        self.interrupt_log = QTextEdit()
        self.interrupt_log.setMaximumHeight(100)
        self.interrupt_log.setReadOnly(True)
        interrupt_layout.addWidget(self.interrupt_log)
        interrupt_group.setLayout(interrupt_layout)
        self.layout().insertWidget(5, interrupt_group)

        # Visualization area
        viz_splitter = QSplitter(Qt.Orientation.Vertical)
        viz_splitter.addWidget(self.disk_widget)
        viz_splitter.addWidget(self.buffer_widget)
        viz_splitter.setSizes([300, 100])

        self.layout().insertWidget(6, viz_splitter)

        # Results
        self.results_label = QLabel()
        self.layout().addWidget(self.results_label)

    def create_visualization_widget(self):
        # Return a container widget
        widget = QWidget()
        layout = QVBoxLayout()
        # Visualization is handled in setup_specific_ui
        widget.setLayout(layout)
        return widget

    def on_algorithm_changed(self, algorithm):
        self.current_algorithm = algorithm

    def on_buffer_size_changed(self, size):
        self.buffer = Buffer(size)
        self.buffer_widget.set_buffer(self.buffer)

    def add_request(self):
        try:
            request_id = self.request_id_edit.text().strip()
            if not request_id:
                raise ValueError("Request ID cannot be empty")

            process_id = self.process_id_edit.text().strip()
            if not process_id:
                raise ValueError("Process ID cannot be empty")

            request_type = IORequestType.READ if self.request_type_combo.currentText() == "read" else IORequestType.WRITE
            block_number = self.block_number_spin.value()

            # Check for duplicate request ID
            if any(r.request_id == request_id for r in self.requests):
                QMessageBox.warning(self, "Error", f"Request {request_id} already exists")
                return

            request = IORequest(request_id, process_id, request_type, block_number)
            self.requests.append(request)
            self.update_request_table()

            # Clear inputs
            self.request_id_edit.setText(f"R{len(self.requests) + 1}")

        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def generate_random_requests(self):
        self.requests.clear()
        for i in range(8):
            request_id = f"R{i+1}"
            process_id = f"P{random.randint(1, 3)}"
            request_type = random.choice([IORequestType.READ, IORequestType.WRITE])
            block_number = random.randint(0, 99)
            request = IORequest(request_id, process_id, request_type, block_number)
            self.requests.append(request)
        self.update_request_table()
        self.disk_widget.set_data(self.requests, self.device_driver.current_position)

    def update_request_table(self):
        self.request_table.setRowCount(len(self.requests))
        for i, request in enumerate(self.requests):
            self.request_table.setItem(i, 0, QTableWidgetItem(request.request_id))
            self.request_table.setItem(i, 1, QTableWidgetItem(request.process_id))
            self.request_table.setItem(i, 2, QTableWidgetItem(request.request_type.value))
            self.request_table.setItem(i, 3, QTableWidgetItem(str(request.block_number)))

    def on_play(self):
        if not self.requests:
            QMessageBox.warning(self, "Error", "No I/O requests to schedule")
            return

        self.run_scheduling()
        self.animation_index = 0
        self.animate_step()
        self.animation_timer.start(1500)  # 1.5 seconds per step

    def on_pause(self):
        self.animation_timer.stop()

    def on_reset(self):
        self.animation_timer.stop()
        self.requests.clear()
        self.update_request_table()
        self.disk_widget.set_data([], 0)
        self.buffer_widget.set_buffer(self.buffer)
        self.interrupt_log.clear()
        self.results_label.setText("")
        self.update_status("Reset")

    def run_scheduling(self):
        try:
            if self.current_algorithm == "FCFS":
                result = IOScheduler.fcfs(self.requests, self.device_driver)
            elif self.current_algorithm == "SSTF":
                result = IOScheduler.sstf(self.requests, self.device_driver)
            elif self.current_algorithm == "SCAN":
                result = IOScheduler.scan(self.requests, self.device_driver)
            else:
                raise ValueError("Unknown algorithm")

            self.schedule_result = result
            self.display_results(result)
            self.update_status("Scheduling completed")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Scheduling failed: {str(e)}")

    def animate_step(self):
        if not self.schedule_result or self.animation_index >= len(self.schedule_result['schedule']):
            self.animation_timer.stop()
            return

        step = self.schedule_result['schedule'][self.animation_index]
        request = step['request']

        # Update disk head position
        self.disk_widget.set_data(self.requests, request.block_number)
        self.device_driver.current_position = request.block_number

        # Simulate buffer operation
        if len(self.buffer.data) < self.buffer.size:
            self.buffer.put(f"Req:{request.request_id}")
        else:
            self.interrupt_controller.trigger_interrupt("buffer_full", f"Buffer full for {request.request_id}")

        self.buffer_widget.set_buffer(self.buffer)

        # Trigger completion interrupt
        self.interrupt_controller.trigger_interrupt("io_complete", request.request_id)

        # Process interrupts
        self.interrupt_controller.process_interrupts()

        self.animation_index += 1

    def on_io_complete(self, request_id):
        self.interrupt_log.append(f"I/O Complete: {request_id}")

    def on_buffer_full(self, data):
        self.interrupt_log.append(f"Buffer Full: {data}")

    def display_results(self, result):
        text = f"Total Seek Time: {result['total_seek_time']:.2f}\n"
        text += f"Average Waiting Time: {result['avg_waiting_time']:.2f}\n"
        text += f"Average Seek Time: {result['avg_seek_time']:.2f}\n"
        text += f"Total Time: {result['total_time']:.2f}"
        self.results_label.setText(text)