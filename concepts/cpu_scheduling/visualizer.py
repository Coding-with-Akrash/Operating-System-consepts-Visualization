from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QSpinBox,
    QLineEdit, QMessageBox, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QFont, QPen
from gui.components.base_visualizer import BaseVisualizer
from .algorithms import Process, Scheduler

class GanttChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.gantt_data = []  # List of (pid, start, end)
        self.max_time = 0
        self.setMinimumHeight(200)

    def set_data(self, gantt_data):
        self.gantt_data = gantt_data
        self.max_time = max((end for _, _, end in gantt_data), default=0)
        self.update()

    def paintEvent(self, event):
        if not self.gantt_data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        chart_height = height - 60  # Leave space for labels

        if self.max_time == 0:
            return

        # Draw time axis
        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        painter.drawLine(50, chart_height, width - 20, chart_height)

        # Draw time labels
        painter.setFont(QFont("Arial", 8))
        for t in range(0, self.max_time + 1, max(1, self.max_time // 10)):
            x = 50 + (t / self.max_time) * (width - 70)
            painter.drawLine(int(x), chart_height - 5, int(x), chart_height + 5)
            painter.drawText(int(x) - 10, chart_height + 20, str(t))

        # Draw processes
        colors = [QColor(255, 100, 100), QColor(100, 255, 100), QColor(100, 100, 255),
                 QColor(255, 255, 100), QColor(255, 100, 255), QColor(100, 255, 255)]

        y_offset = 20
        process_y = {}
        current_y = y_offset

        for pid, start, end in self.gantt_data:
            if pid not in process_y:
                process_y[pid] = current_y
                current_y += 40

            y = process_y[pid]
            x_start = 50 + (start / self.max_time) * (width - 70)
            x_end = 50 + (end / self.max_time) * (width - 70)
            rect_width = x_end - x_start

            color = colors[hash(pid) % len(colors)]
            painter.fillRect(int(x_start), y, int(rect_width), 30, color)
            painter.setPen(QPen(Qt.GlobalColor.black, 1))
            painter.drawRect(int(x_start), y, int(rect_width), 30)

            # Draw process label
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.drawText(int(x_start + rect_width/2 - 10), y + 20, pid)

        # Draw process labels on left
        painter.setPen(QPen(Qt.GlobalColor.black))
        for pid, y in process_y.items():
            painter.drawText(10, y + 20, pid)

class CPUSchedulingVisualizer(BaseVisualizer):
    def __init__(self):
        self.gantt_chart = GanttChartWidget()  # Create before super().__init__
        super().__init__("CPU Scheduling")
        self.processes = []
        self.current_algorithm = "FCFS"
        self.time_quantum = 2
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_step)
        self.animation_index = 0
        self.setup_specific_ui()

    def setup_specific_ui(self):
        # Algorithm selection
        algo_group = QGroupBox("Algorithm Selection")
        algo_layout = QHBoxLayout()
        self.algo_combo = QComboBox()
        self.algo_combo.addItems(["FCFS", "SJF", "Round Robin", "Priority"])
        self.algo_combo.currentTextChanged.connect(self.on_algorithm_changed)
        algo_layout.addWidget(QLabel("Algorithm:"))
        algo_layout.addWidget(self.algo_combo)

        self.time_quantum_spin = QSpinBox()
        self.time_quantum_spin.setValue(2)
        self.time_quantum_spin.setRange(1, 10)
        self.time_quantum_spin.valueChanged.connect(self.on_time_quantum_changed)
        algo_layout.addWidget(QLabel("Time Quantum:"))
        algo_layout.addWidget(self.time_quantum_spin)
        algo_layout.addStretch()
        algo_group.setLayout(algo_layout)
        self.layout().insertWidget(1, algo_group)

        # Process input
        input_group = QGroupBox("Process Input")
        input_layout = QFormLayout()

        self.pid_edit = QLineEdit("P1")
        self.arrival_edit = QSpinBox()
        self.arrival_edit.setRange(0, 100)
        self.burst_edit = QSpinBox()
        self.burst_edit.setRange(1, 100)
        self.priority_edit = QSpinBox()
        self.priority_edit.setRange(0, 10)

        input_layout.addRow("Process ID:", self.pid_edit)
        input_layout.addRow("Arrival Time:", self.arrival_edit)
        input_layout.addRow("Burst Time:", self.burst_edit)
        input_layout.addRow("Priority:", self.priority_edit)

        add_btn = QPushButton("Add Process")
        add_btn.clicked.connect(self.add_process)
        input_layout.addRow(add_btn)

        input_group.setLayout(input_layout)
        self.layout().insertWidget(2, input_group)

        # Process table
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(4)
        self.process_table.setHorizontalHeaderLabels(["PID", "Arrival", "Burst", "Priority"])
        self.layout().insertWidget(3, self.process_table)

        # Gantt chart is added in create_visualization_widget

        # Results
        self.results_label = QLabel()
        self.layout().addWidget(self.results_label)

    def create_visualization_widget(self):
        # Return a container widget
        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.gantt_chart)
        widget.setLayout(layout)
        return widget

    def on_algorithm_changed(self, algorithm):
        self.current_algorithm = algorithm
        self.time_quantum_spin.setEnabled(algorithm == "Round Robin")

    def on_time_quantum_changed(self, value):
        self.time_quantum = value

    def add_process(self):
        try:
            pid = self.pid_edit.text().strip()
            if not pid:
                raise ValueError("Process ID cannot be empty")

            arrival = self.arrival_edit.value()
            burst = self.burst_edit.value()
            priority = self.priority_edit.value()

            # Check for duplicate PID
            if any(p.pid == pid for p in self.processes):
                QMessageBox.warning(self, "Error", f"Process {pid} already exists")
                return

            process = Process(pid, arrival, burst, priority)
            self.processes.append(process)
            self.update_process_table()

            # Clear inputs
            self.pid_edit.setText(f"P{len(self.processes) + 1}")

        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def update_process_table(self):
        self.process_table.setRowCount(len(self.processes))
        for i, process in enumerate(self.processes):
            self.process_table.setItem(i, 0, QTableWidgetItem(process.pid))
            self.process_table.setItem(i, 1, QTableWidgetItem(str(process.arrival_time)))
            self.process_table.setItem(i, 2, QTableWidgetItem(str(process.burst_time)))
            self.process_table.setItem(i, 3, QTableWidgetItem(str(process.priority)))

    def on_play(self):
        if not self.processes:
            QMessageBox.warning(self, "Error", "No processes to schedule")
            return

        self.run_scheduling()
        self.animation_index = 0
        self.animate_step()
        self.animation_timer.start(1000)  # 1 second per step

    def on_pause(self):
        self.animation_timer.stop()

    def on_reset(self):
        self.animation_timer.stop()
        self.gantt_chart.set_data([])
        self.results_label.setText("")
        self.update_status("Reset")

    def run_scheduling(self):
        try:
            if self.current_algorithm == "FCFS":
                result = Scheduler.fcfs(self.processes)
            elif self.current_algorithm == "SJF":
                result = Scheduler.sjf(self.processes)
            elif self.current_algorithm == "Round Robin":
                result = Scheduler.round_robin(self.processes, self.time_quantum)
            elif self.current_algorithm == "Priority":
                result = Scheduler.priority_scheduling(self.processes)
            else:
                raise ValueError("Unknown algorithm")

            self.gantt_chart.set_data(result['gantt_chart'])
            self.display_results(result)
            self.update_status("Scheduling completed")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Scheduling failed: {str(e)}")

    def animate_step(self):
        # For now, just show the full chart
        # TODO: Implement step-by-step animation
        pass

    def display_results(self, result):
        text = f"Average Waiting Time: {result['avg_waiting_time']:.2f}\nAverage Turnaround Time: {result['avg_turnaround_time']:.2f}"
        self.results_label.setText(text)