from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QSpinBox,
    QLineEdit, QMessageBox, QGroupBox, QFormLayout, QTextEdit,
    QSplitter, QFrame, QProgressBar
)
from PyQt6.QtCore import Qt, QPointF, QTimer
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from gui.components.base_visualizer import BaseVisualizer
from .algorithms import Process, Resource, ResourceAllocationAlgorithms, AllocationPolicy
import math
import random

class AllocationMatrixWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.processes = []
        self.resources = []
        self.setMinimumSize(400, 300)

    def set_data(self, processes, resources):
        self.processes = processes
        self.resources = resources
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self.processes or not self.resources:
            painter.drawText(10, 30, "No data to display")
            return

        # Draw header
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.drawText(10, 30, "Allocation Matrix")

        # Draw table
        cell_width = 80
        cell_height = 30
        start_x = 10
        start_y = 50

        # Resource headers
        for i, resource in enumerate(self.resources):
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.setBrush(QBrush(QColor(200, 200, 200)))
            painter.drawRect(start_x + i * cell_width, start_y, cell_width, cell_height)
            painter.drawText(start_x + i * cell_width + 5, start_y + 20, resource.rid)

        # Process rows
        for i, process in enumerate(self.processes):
            row_y = start_y + (i + 1) * cell_height

            # Process ID
            painter.setBrush(QBrush(QColor(200, 200, 200)))
            painter.drawRect(start_x - cell_width, row_y, cell_width, cell_height)
            painter.drawText(start_x - cell_width + 5, row_y + 20, process.pid)

            # Allocated resources
            for j, alloc in enumerate(process.allocated_resources):
                painter.setBrush(QBrush(QColor(100, 200, 100)))
                painter.drawRect(start_x + j * cell_width, row_y, cell_width, cell_height)
                painter.drawText(start_x + j * cell_width + 5, row_y + 20, str(alloc))

class ResourceGraphWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.processes = []
        self.resources = []
        self.allocations = {}  # pid -> [alloc amounts]
        self.setMinimumSize(400, 300)

    def set_data(self, processes, resources):
        self.processes = processes
        self.resources = resources
        self.allocations = {p.pid: p.allocated_resources[:] for p in processes}
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self.processes or not self.resources:
            painter.drawText(10, 30, "No data to display")
            return

        center_x, center_y = self.width() / 2, self.height() / 2
        radius = min(center_x, center_y) - 50

        # Draw resources in circle
        num_resources = len(self.resources)
        for i, resource in enumerate(self.resources):
            angle = 2 * math.pi * i / num_resources
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)

            # Resource node
            painter.setPen(QPen(Qt.GlobalColor.black, 2))
            painter.setBrush(QBrush(QColor(200, 100, 100)))
            painter.drawEllipse(int(x - 20), int(y - 20), 40, 40)
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.drawText(int(x - 10), int(y + 5), resource.rid)

            # Available count
            painter.setFont(QFont("Arial", 8))
            painter.drawText(int(x - 15), int(y + 25), f"A:{resource.available_instances}")

        # Draw processes and allocation edges
        process_positions = {}
        num_processes = len(self.processes)
        inner_radius = radius * 0.6

        for i, process in enumerate(self.processes):
            angle = 2 * math.pi * i / num_processes
            x = center_x + inner_radius * math.cos(angle)
            y = center_y + inner_radius * math.sin(angle)
            process_positions[process.pid] = (x, y)

            # Process node
            painter.setPen(QPen(Qt.GlobalColor.black, 2))
            painter.setBrush(QBrush(QColor(100, 200, 100)))
            painter.drawEllipse(int(x - 15), int(y - 15), 30, 30)
            painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            painter.drawText(int(x - 8), int(y + 4), process.pid)

        # Draw allocation edges
        for process in self.processes:
            px, py = process_positions[process.pid]
            for i, alloc in enumerate(process.allocated_resources):
                if alloc > 0:
                    angle = 2 * math.pi * i / num_resources
                    rx = center_x + radius * math.cos(angle)
                    ry = center_y + radius * math.sin(angle)

                    # Draw edge
                    painter.setPen(QPen(QColor(0, 100, 200), 2))
                    painter.drawLine(int(px), int(py), int(rx), int(ry))

                    # Label
                    mid_x = (px + rx) / 2
                    mid_y = (py + ry) / 2
                    painter.setFont(QFont("Arial", 8))
                    painter.drawText(int(mid_x - 10), int(mid_y - 5), f"{alloc}")

class ResourceAllocationVisualizer(BaseVisualizer):
    def __init__(self):
        self.allocation_matrix = AllocationMatrixWidget()
        self.resource_graph = ResourceGraphWidget()
        self.processes = []
        self.resources = []
        self.requests_queue = []
        self.current_policy = AllocationPolicy.FCFS
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_step)
        self.animation_step = 0
        super().__init__("Resource Allocation Visualization")
        self.setup_specific_ui()

    def setup_specific_ui(self):
        # Policy selection
        policy_group = QGroupBox("Allocation Policy")
        policy_layout = QHBoxLayout()
        self.policy_combo = QComboBox()
        self.policy_combo.addItems([p.value for p in AllocationPolicy])
        self.policy_combo.currentTextChanged.connect(self.on_policy_changed)
        policy_layout.addWidget(QLabel("Policy:"))
        policy_layout.addWidget(self.policy_combo)
        policy_layout.addStretch()
        policy_group.setLayout(policy_layout)
        self.layout().insertWidget(1, policy_group)

        # Input panels
        input_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Resource/Process input
        input_widget = QWidget()
        input_layout = QVBoxLayout()

        # Resource input
        resource_group = QGroupBox("Resources")
        resource_layout = QFormLayout()
        self.resource_id_edit = QLineEdit("R1")
        self.resource_total_edit = QSpinBox()
        self.resource_total_edit.setRange(1, 20)
        self.resource_total_edit.setValue(3)
        resource_layout.addRow("Resource ID:", self.resource_id_edit)
        resource_layout.addRow("Total Instances:", self.resource_total_edit)
        add_resource_btn = QPushButton("Add Resource")
        add_resource_btn.clicked.connect(self.add_resource)
        resource_layout.addRow(add_resource_btn)
        resource_group.setLayout(resource_layout)
        input_layout.addWidget(resource_group)

        # Process input
        process_group = QGroupBox("Processes")
        process_layout = QFormLayout()
        self.process_id_edit = QLineEdit("P1")
        self.max_resources_edit = QLineEdit("1,1,1")  # Comma-separated
        self.priority_edit = QSpinBox()
        self.priority_edit.setRange(0, 10)
        self.priority_edit.setValue(0)
        process_layout.addRow("Process ID:", self.process_id_edit)
        process_layout.addRow("Max Resources:", self.max_resources_edit)
        process_layout.addRow("Priority:", self.priority_edit)
        add_process_btn = QPushButton("Add Process")
        add_process_btn.clicked.connect(self.add_process)
        process_layout.addRow(add_process_btn)
        process_group.setLayout(process_layout)
        input_layout.addWidget(process_group)

        # Request/Deallocation input
        action_group = QGroupBox("Actions")
        action_layout = QFormLayout()
        self.action_process_edit = QLineEdit("P1")
        self.request_resources_edit = QLineEdit("1,0,0")
        action_layout.addRow("Process ID:", self.action_process_edit)
        action_layout.addRow("Resources:", self.request_resources_edit)

        request_btn = QPushButton("Make Request")
        request_btn.clicked.connect(self.make_request)
        action_layout.addRow(request_btn)

        release_btn = QPushButton("Release Resources")
        release_btn.clicked.connect(self.release_resources)
        action_layout.addRow(release_btn)

        action_group.setLayout(action_layout)
        input_layout.addWidget(action_group)

        input_widget.setLayout(input_layout)
        input_splitter.addWidget(input_widget)

        # Tables
        tables_widget = QWidget()
        tables_layout = QVBoxLayout()

        self.resource_table = QTableWidget()
        self.resource_table.setColumnCount(3)
        self.resource_table.setHorizontalHeaderLabels(["RID", "Total", "Available"])
        tables_layout.addWidget(QLabel("Resources:"))
        tables_layout.addWidget(self.resource_table)

        self.process_table = QTableWidget()
        self.process_table.setColumnCount(5)
        self.process_table.setHorizontalHeaderLabels(["PID", "Max", "Allocated", "Need", "Priority"])
        tables_layout.addWidget(QLabel("Processes:"))
        tables_layout.addWidget(self.process_table)

        tables_widget.setLayout(tables_layout)
        input_splitter.addWidget(tables_widget)

        self.layout().insertWidget(2, input_splitter)

        # Results
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(100)
        self.layout().addWidget(self.results_text)

        # Progress bar for animations
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.layout().addWidget(self.progress_bar)

    def create_visualization_widget(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # Visualization selection
        vis_layout = QHBoxLayout()
        self.vis_combo = QComboBox()
        self.vis_combo.addItems(["Allocation Matrix", "Resource Graph"])
        self.vis_combo.currentTextChanged.connect(self.on_vis_changed)
        vis_layout.addWidget(QLabel("Visualization:"))
        vis_layout.addWidget(self.vis_combo)
        vis_layout.addStretch()
        layout.addLayout(vis_layout)

        # Visualization display
        self.vis_container = QWidget()
        vis_cont_layout = QVBoxLayout()
        vis_cont_layout.addWidget(self.allocation_matrix)
        vis_cont_layout.addWidget(self.resource_graph)
        self.vis_container.setLayout(vis_cont_layout)
        layout.addWidget(self.vis_container)

        self.on_vis_changed("Allocation Matrix")  # Default

        widget.setLayout(layout)
        return widget

    def on_policy_changed(self, policy_name):
        self.current_policy = next(p for p in AllocationPolicy if p.value == policy_name)
        self.update_status(f"Policy changed to {policy_name}")

    def on_vis_changed(self, vis):
        if vis == "Allocation Matrix":
            self.allocation_matrix.show()
            self.resource_graph.hide()
        else:
            self.allocation_matrix.hide()
            self.resource_graph.show()
        self.update_visualizations()

    def add_resource(self):
        try:
            rid = self.resource_id_edit.text().strip()
            if not rid:
                raise ValueError("Resource ID cannot be empty")

            total = self.resource_total_edit.value()

            if any(r.rid == rid for r in self.resources):
                QMessageBox.warning(self, "Error", f"Resource {rid} already exists")
                return

            resource = Resource(rid, total)
            self.resources.append(resource)
            self.update_tables()

            self.resource_id_edit.setText(f"R{len(self.resources) + 1}")

        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def add_process(self):
        try:
            pid = self.process_id_edit.text().strip()
            if not pid:
                raise ValueError("Process ID cannot be empty")

            max_str = self.max_resources_edit.text().strip()
            max_resources = [int(x.strip()) for x in max_str.split(',')]

            if len(max_resources) != len(self.resources):
                raise ValueError(f"Number of max resources ({len(max_resources)}) must match number of resources ({len(self.resources)})")

            priority = self.priority_edit.value()

            if any(p.pid == pid for p in self.processes):
                QMessageBox.warning(self, "Error", f"Process {pid} already exists")
                return

            process = Process(pid, max_resources, priority=priority)
            self.processes.append(process)
            self.update_tables()

            self.process_id_edit.setText(f"P{len(self.processes) + 1}")

        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def make_request(self):
        try:
            pid = self.action_process_edit.text().strip()
            request_str = self.request_resources_edit.text().strip()
            request = [int(x.strip()) for x in request_str.split(',')]

            if len(request) != len(self.resources):
                raise ValueError("Request length must match number of resources")

            if self.current_policy == AllocationPolicy.BANKERS:
                result = ResourceAllocationAlgorithms.simulate_request_bankers(self.processes, self.resources, pid, request)
            else:
                # For other policies, just check availability
                available = [r.available_instances for r in self.resources]
                can_grant = all(req <= avail for req, avail in zip(request, available))
                if can_grant:
                    process = next((p for p in self.processes if p.pid == pid), None)
                    if process:
                        for i, req in enumerate(request):
                            process.allocated_resources[i] += req
                            process.need_resources[i] -= req
                            self.resources[i].available_instances -= req
                        result = {'granted': True, 'message': f"Request by {pid} granted"}
                    else:
                        result = {'granted': False, 'message': f"Process {pid} not found"}
                else:
                    result = {'granted': False, 'message': f"Request by {pid} denied - insufficient resources"}

            self.results_text.append(f"Request: {result['message']}")
            if result['granted']:
                self.update_tables()
                self.update_visualizations()

        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def release_resources(self):
        try:
            pid = self.action_process_edit.text().strip()
            release_str = self.request_resources_edit.text().strip()
            release = [int(x.strip()) for x in release_str.split(',')]

            result = ResourceAllocationAlgorithms.deallocate_resources(self.processes, self.resources, pid, release)
            self.results_text.append(f"Release: {result['message']}")

            if result['success']:
                self.update_tables()
                self.update_visualizations()

        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def update_tables(self):
        # Update resource table
        self.resource_table.setRowCount(len(self.resources))
        for i, resource in enumerate(self.resources):
            self.resource_table.setItem(i, 0, QTableWidgetItem(resource.rid))
            self.resource_table.setItem(i, 1, QTableWidgetItem(str(resource.total_instances)))
            self.resource_table.setItem(i, 2, QTableWidgetItem(str(resource.available_instances)))

        # Update process table
        self.process_table.setRowCount(len(self.processes))
        for i, process in enumerate(self.processes):
            self.process_table.setItem(i, 0, QTableWidgetItem(process.pid))
            self.process_table.setItem(i, 1, QTableWidgetItem(str(process.max_resources)))
            self.process_table.setItem(i, 2, QTableWidgetItem(str(process.allocated_resources)))
            self.process_table.setItem(i, 3, QTableWidgetItem(str(process.need_resources)))
            self.process_table.setItem(i, 4, QTableWidgetItem(str(process.priority)))

    def update_visualizations(self):
        self.allocation_matrix.set_data(self.processes, self.resources)
        self.resource_graph.set_data(self.processes, self.resources)

    def on_play(self):
        if self.current_policy == AllocationPolicy.BANKERS:
            result = ResourceAllocationAlgorithms.bankers_algorithm(self.processes, self.resources)
            self.results_text.append(f"Banker's Algorithm: {result['message']}")
            if result['safe_sequence']:
                self.results_text.append(f"Safe sequence: {' -> '.join(result['safe_sequence'])}")
        elif self.current_policy == AllocationPolicy.FAIR_SHARE:
            result = ResourceAllocationAlgorithms.fair_share_allocation(self.processes, self.resources)
            self.results_text.append(f"Fair Share: {result['message']}")
            self.update_tables()
            self.update_visualizations()
        else:
            # For other policies, simulate some requests
            self.start_animation()

        self.update_status("Analysis completed")

    def start_animation(self):
        self.animation_step = 0
        self.progress_bar.setValue(0)
        self.animation_timer.start(1000)  # 1 second intervals

    def animate_step(self):
        if self.animation_step >= 10:  # Stop after 10 steps
            self.animation_timer.stop()
            self.progress_bar.setValue(100)
            return

        # Simulate random requests
        if self.processes and self.resources:
            pid = random.choice(self.processes).pid
            request = [random.randint(0, 1) for _ in self.resources]
            self.action_process_edit.setText(pid)
            self.request_resources_edit.setText(','.join(map(str, request)))
            self.make_request()

        self.animation_step += 1
        self.progress_bar.setValue((self.animation_step / 10) * 100)

    def on_reset(self):
        self.processes = []
        self.resources = []
        self.requests_queue = []
        self.update_tables()
        self.update_visualizations()
        self.results_text.clear()
        self.progress_bar.setValue(0)
        self.animation_timer.stop()
        self.update_status("Reset")