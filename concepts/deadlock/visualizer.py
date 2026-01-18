from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QSpinBox,
    QLineEdit, QMessageBox, QGroupBox, QFormLayout, QTextEdit,
    QSplitter, QFrame
)
from PyQt6.QtCore import Qt, QPointF, QTimer
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from gui.components.base_visualizer import BaseVisualizer
from .algorithms import Process, Resource, DeadlockAlgorithms
import math

class GraphWidget(QWidget):
    def __init__(self, graph_type="rag"):
        super().__init__()
        self.graph_type = graph_type  # "rag" or "wait_for"
        self.nodes = []  # List of (id, x, y, type) where type is 'process' or 'resource'
        self.edges = []  # List of (from_id, to_id, label)
        self.setMinimumSize(400, 300)

    def set_data(self, processes, resources, wait_for_graph=None):
        self.nodes = []
        self.edges = []

        if self.graph_type == "rag":
            # Resource Allocation Graph
            num_processes = len(processes)
            num_resources = len(resources)
            center_x, center_y = self.width() / 2, self.height() / 2
            radius = min(center_x, center_y) - 50

            # Place processes in a circle
            for i, process in enumerate(processes):
                angle = 2 * math.pi * i / num_processes
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                self.nodes.append((process.pid, x, y, 'process'))

            # Place resources in inner circle
            inner_radius = radius * 0.6
            for i, resource in enumerate(resources):
                angle = 2 * math.pi * i / num_resources
                x = center_x + inner_radius * math.cos(angle)
                y = center_y + inner_radius * math.sin(angle)
                self.nodes.append((resource.rid, x, y, 'resource'))

            # Add allocation edges (process -> resource)
            for process in processes:
                for i, alloc in enumerate(process.allocated_resources):
                    if alloc > 0:
                        resource_id = resources[i].rid
                        self.edges.append((process.pid, resource_id, f"alloc:{alloc}"))

            # Add request edges (process -> resource, dashed)
            for process in processes:
                for i, need in enumerate(process.need_resources):
                    if need > 0:
                        resource_id = resources[i].rid
                        self.edges.append((process.pid, resource_id, f"req:{need}"))

        elif self.graph_type == "wait_for" and wait_for_graph:
            # Wait-for Graph
            num_processes = len(wait_for_graph)
            center_x, center_y = self.width() / 2, self.height() / 2
            radius = min(center_x, center_y) - 50

            # Place processes in a circle
            for i, pid in enumerate(wait_for_graph.keys()):
                angle = 2 * math.pi * i / num_processes
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                self.nodes.append((pid, x, y, 'process'))

            # Add wait-for edges
            for pid, waits_for in wait_for_graph.items():
                for target in waits_for:
                    self.edges.append((pid, target, ""))

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw edges first
        for from_id, to_id, label in self.edges:
            from_node = next((n for n in self.nodes if n[0] == from_id), None)
            to_node = next((n for n in self.nodes if n[0] == to_id), None)
            if from_node and to_node:
                from_x, from_y = from_node[1], from_node[2]
                to_x, to_y = to_node[1], to_node[2]

                # Draw arrow
                painter.setPen(QPen(Qt.GlobalColor.blue, 2))
                if "req:" in label:
                    painter.setPen(QPen(Qt.GlobalColor.blue, 2, Qt.PenStyle.DashLine))

                # Calculate arrow
                dx = to_x - from_x
                dy = to_y - from_y
                length = math.sqrt(dx**2 + dy**2)
                if length > 0:
                    dx /= length
                    dy /= length

                # Shorten the line to not overlap nodes
                node_radius = 20
                start_x = from_x + dx * node_radius
                start_y = from_y + dy * node_radius
                end_x = to_x - dx * node_radius
                end_y = to_y - dy * node_radius

                painter.drawLine(int(start_x), int(start_y), int(end_x), int(end_y))

                # Draw arrowhead
                arrow_size = 10
                angle = math.atan2(dy, dx)
                painter.setBrush(QBrush(Qt.GlobalColor.blue))
                points = [
                    QPointF(end_x, end_y),
                    QPointF(end_x - arrow_size * math.cos(angle - math.pi/6), end_y - arrow_size * math.sin(angle - math.pi/6)),
                    QPointF(end_x - arrow_size * math.cos(angle + math.pi/6), end_y - arrow_size * math.sin(angle + math.pi/6))
                ]
                painter.drawPolygon(points)

                # Draw label
                if label:
                    mid_x = (start_x + end_x) / 2
                    mid_y = (start_y + end_y) / 2
                    painter.setPen(QPen(Qt.GlobalColor.black))
                    painter.drawText(int(mid_x - 20), int(mid_y - 5), label)

        # Draw nodes
        for node_id, x, y, node_type in self.nodes:
            painter.setPen(QPen(Qt.GlobalColor.black, 2))
            if node_type == 'process':
                painter.setBrush(QBrush(QColor(100, 200, 100)))
            else:
                painter.setBrush(QBrush(QColor(200, 100, 100)))

            painter.drawEllipse(int(x - 20), int(y - 20), 40, 40)
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.drawText(int(x - 10), int(y + 5), node_id)

class DeadlockVisualizer(BaseVisualizer):
    def __init__(self):
        self.rag_widget = GraphWidget("rag")
        self.wait_for_widget = GraphWidget("wait_for")
        self.processes = []
        self.resources = []
        self.wait_for_graph = {}
        self.current_mode = "bankers"  # bankers, detection, prevention
        super().__init__("Deadlock Visualization")
        self.setup_specific_ui()

    def setup_specific_ui(self):
        # Mode selection
        mode_group = QGroupBox("Mode Selection")
        mode_layout = QHBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Banker's Algorithm", "Deadlock Detection", "Deadlock Prevention"])
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(QLabel("Mode:"))
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        mode_group.setLayout(mode_layout)
        self.layout().insertWidget(1, mode_group)

        # Input panels
        input_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Process/Resource input
        input_widget = QWidget()
        input_layout = QVBoxLayout()

        # Resource input
        resource_group = QGroupBox("Resources")
        resource_layout = QFormLayout()
        self.resource_id_edit = QLineEdit("R1")
        self.resource_total_edit = QSpinBox()
        self.resource_total_edit.setRange(1, 10)
        self.resource_total_edit.setValue(1)
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
        self.max_resources_edit = QLineEdit("1,0")  # Comma-separated
        process_layout.addRow("Process ID:", self.process_id_edit)
        process_layout.addRow("Max Resources (comma-separated):", self.max_resources_edit)
        add_process_btn = QPushButton("Add Process")
        add_process_btn.clicked.connect(self.add_process)
        process_layout.addRow(add_process_btn)
        process_group.setLayout(process_layout)
        input_layout.addWidget(process_group)

        # Simulation controls
        sim_group = QGroupBox("Simulation")
        sim_layout = QFormLayout()
        self.request_process_edit = QLineEdit("P1")
        self.request_resources_edit = QLineEdit("1,0")
        sim_layout.addRow("Process ID:", self.request_process_edit)
        sim_layout.addRow("Request Resources:", self.request_resources_edit)
        request_btn = QPushButton("Make Request")
        request_btn.clicked.connect(self.make_request)
        sim_layout.addRow(request_btn)
        sim_group.setLayout(sim_layout)
        input_layout.addWidget(sim_group)

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
        self.process_table.setColumnCount(4)
        self.process_table.setHorizontalHeaderLabels(["PID", "Max", "Allocated", "Need"])
        tables_layout.addWidget(QLabel("Processes:"))
        tables_layout.addWidget(self.process_table)

        tables_widget.setLayout(tables_layout)
        input_splitter.addWidget(tables_widget)

        self.layout().insertWidget(2, input_splitter)

        # Results
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(100)
        self.layout().addWidget(self.results_text)

    def create_visualization_widget(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # Graph selection
        graph_layout = QHBoxLayout()
        self.graph_combo = QComboBox()
        self.graph_combo.addItems(["Resource Allocation Graph", "Wait-for Graph"])
        self.graph_combo.currentTextChanged.connect(self.on_graph_changed)
        graph_layout.addWidget(QLabel("Graph:"))
        graph_layout.addWidget(self.graph_combo)
        graph_layout.addStretch()
        layout.addLayout(graph_layout)

        # Graph display
        self.graph_container = QWidget()
        graph_cont_layout = QVBoxLayout()
        graph_cont_layout.addWidget(self.rag_widget)
        graph_cont_layout.addWidget(self.wait_for_widget)
        self.graph_container.setLayout(graph_cont_layout)
        layout.addWidget(self.graph_container)

        self.on_graph_changed("Resource Allocation Graph")  # Default

        widget.setLayout(layout)
        return widget

    def on_mode_changed(self, mode):
        self.current_mode = {
            "Banker's Algorithm": "bankers",
            "Deadlock Detection": "detection",
            "Deadlock Prevention": "prevention"
        }.get(mode, "bankers")
        self.update_graphs()

    def on_graph_changed(self, graph):
        if graph == "Resource Allocation Graph":
            self.rag_widget.show()
            self.wait_for_widget.hide()
        else:
            self.rag_widget.hide()
            self.wait_for_widget.show()
        self.update_graphs()

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

            if any(p.pid == pid for p in self.processes):
                QMessageBox.warning(self, "Error", f"Process {pid} already exists")
                return

            process = Process(pid, max_resources)
            self.processes.append(process)
            self.update_tables()

            self.process_id_edit.setText(f"P{len(self.processes) + 1}")

        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def make_request(self):
        try:
            pid = self.request_process_edit.text().strip()
            request_str = self.request_resources_edit.text().strip()
            request = [int(x.strip()) for x in request_str.split(',')]

            if len(request) != len(self.resources):
                raise ValueError("Request length must match number of resources")

            if self.current_mode == "bankers":
                result = DeadlockAlgorithms.simulate_request(self.processes, self.resources, pid, request)
                self.results_text.append(f"Request by {pid} for {request}: {result['message']}")
                if result['granted']:
                    self.update_tables()
                    self.update_graphs()
            else:
                self.results_text.append("Request simulation only available in Banker's mode")

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

    def update_graphs(self):
        self.rag_widget.set_data(self.processes, self.resources)
        self.wait_for_widget.set_data(self.processes, self.resources, self.wait_for_graph)

    def on_play(self):
        if self.current_mode == "bankers":
            result = DeadlockAlgorithms.bankers_algorithm(self.processes, self.resources)
            self.results_text.append(f"Banker's Algorithm: {result['message']}")
            if result['safe_sequence']:
                self.results_text.append(f"Safe sequence: {' -> '.join(result['safe_sequence'])}")
        elif self.current_mode == "detection":
            # For detection, we can check RAG or wait-for
            result = DeadlockAlgorithms.detect_deadlock_resource_allocation(self.processes, self.resources)
            self.results_text.append(f"Detection: {result['message']}")
        self.update_status("Analysis completed")

    def on_reset(self):
        self.processes = []
        self.resources = []
        self.wait_for_graph = {}
        self.update_tables()
        self.update_graphs()
        self.results_text.clear()
        self.update_status("Reset")