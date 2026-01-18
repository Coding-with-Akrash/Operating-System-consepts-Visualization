from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QSpinBox,
    QLineEdit, QMessageBox, QGroupBox, QFormLayout, QSplitter,
    QTextEdit, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from gui.components.base_visualizer import BaseVisualizer
from .algorithms import (
    MemoryBlock, MemoryManager, PageReplacement,
    VirtualMemorySimulator, SegmentationSimulator
)

class MemoryLayoutWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.blocks = []
        self.setMinimumHeight(200)

    def set_blocks(self, blocks):
        self.blocks = blocks
        self.update()

    def paintEvent(self, event):
        if not self.blocks:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        # Calculate total memory size
        total_memory = sum(block.size for block in self.blocks)

        if total_memory == 0:
            return

        x = 10
        colors = [
            QColor(100, 200, 100),  # Free - green
            QColor(200, 100, 100),  # Allocated - red
            QColor(100, 100, 200),  # Process - blue
        ]

        for block in self.blocks:
            block_width = (block.size / total_memory) * (width - 20)
            color = colors[0] if block.is_free else colors[1]

            painter.fillRect(int(x), 20, int(block_width), height - 40, color)
            painter.setPen(QPen(Qt.GlobalColor.black, 2))
            painter.drawRect(int(x), 20, int(block_width), height - 40)

            # Draw label
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.setFont(QFont("Arial", 8))
            label = f"{block.process_id or 'Free'}\n{block.size}KB"
            painter.drawText(int(x + 5), 40, label)

            x += block_width

class PageTableWidget(QTableWidget):
    def __init__(self):
        super().__init__()
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(["Page", "Frame", "Valid", "Referenced"])
        self.setMaximumHeight(300)

    def set_page_table(self, page_table):
        self.setRowCount(len(page_table))
        for i, (page_num, entry) in enumerate(page_table.items()):
            self.setItem(i, 0, QTableWidgetItem(str(page_num)))
            self.setItem(i, 1, QTableWidgetItem(str(entry.frame_number) if entry.frame_number is not None else "-"))
            self.setItem(i, 2, QTableWidgetItem("Yes" if entry.valid else "No"))
            self.setItem(i, 3, QTableWidgetItem("Yes" if entry.referenced else "No"))

class PageReplacementVisualization(QWidget):
    def __init__(self):
        super().__init__()
        self.history = []
        self.current_step = 0
        self.frames_display = QLabel("Frames: []")
        self.page_display = QLabel("Current Page: -")
        self.fault_display = QLabel("Page Fault: No")
        self.replaced_display = QLabel("Replaced: -")

        layout = QVBoxLayout()
        layout.addWidget(self.frames_display)
        layout.addWidget(self.page_display)
        layout.addWidget(self.fault_display)
        layout.addWidget(self.replaced_display)
        self.setLayout(layout)

    def set_history(self, history):
        self.history = history
        self.current_step = 0
        self.update_display()

    def next_step(self):
        if self.current_step < len(self.history) - 1:
            self.current_step += 1
            self.update_display()

    def prev_step(self):
        if self.current_step > 0:
            self.current_step -= 1
            self.update_display()

    def update_display(self):
        if not self.history:
            return

        step = self.history[self.current_step]
        self.frames_display.setText(f"Frames: {step['frames']}")
        self.page_display.setText(f"Current Page: {step['page']}")
        self.fault_display.setText(f"Page Fault: {'Yes' if step['fault'] else 'No'}")
        self.replaced_display.setText(f"Replaced: {step['replaced'] if step['replaced'] is not None else '-'}")

class MemoryManagementVisualizer(BaseVisualizer):
    def __init__(self):
        self.memory_layout = MemoryLayoutWidget()
        self.page_table_widget = PageTableWidget()
        self.page_replacement_viz = PageReplacementVisualization()
        super().__init__("Memory Management")

        self.memory_blocks = []
        self.total_memory = 1024  # KB
        self.current_concept = "Contiguous Allocation"
        self.current_algorithm = "First Fit"
        self.virtual_memory = VirtualMemorySimulator(4)
        self.segmentation = SegmentationSimulator()

        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_step)
        self.setup_specific_ui()

    def setup_specific_ui(self):
        # Concept selection
        concept_group = QGroupBox("Memory Management Concept")
        concept_layout = QHBoxLayout()
        self.concept_combo = QComboBox()
        self.concept_combo.addItems([
            "Contiguous Allocation",
            "Paging",
            "Segmentation",
            "Virtual Memory",
            "Page Replacement"
        ])
        self.concept_combo.currentTextChanged.connect(self.on_concept_changed)
        concept_layout.addWidget(QLabel("Concept:"))
        concept_layout.addWidget(self.concept_combo)
        concept_layout.addStretch()
        concept_group.setLayout(concept_layout)
        self.layout().insertWidget(1, concept_group)

        # Algorithm/Sub-concept selection
        algo_group = QGroupBox("Algorithm/Strategy")
        algo_layout = QHBoxLayout()
        self.algo_combo = QComboBox()
        self.update_algorithm_options()
        self.algo_combo.currentTextChanged.connect(self.on_algorithm_changed)
        algo_layout.addWidget(QLabel("Algorithm:"))
        algo_layout.addWidget(self.algo_combo)
        algo_layout.addStretch()
        algo_group.setLayout(algo_layout)
        self.layout().insertWidget(2, algo_group)

        # Input controls
        input_group = QGroupBox("Input Controls")
        input_layout = QFormLayout()

        self.memory_size_edit = QSpinBox()
        self.memory_size_edit.setRange(256, 4096)
        self.memory_size_edit.setValue(1024)
        self.memory_size_edit.setSingleStep(256)
        input_layout.addRow("Total Memory (KB):", self.memory_size_edit)

        self.process_id_edit = QLineEdit("P1")
        self.process_size_edit = QSpinBox()
        self.process_size_edit.setRange(1, 512)
        self.process_size_edit.setValue(100)

        self.allocate_btn = QPushButton("Allocate Memory")
        self.allocate_btn.clicked.connect(self.allocate_memory)

        self.deallocate_btn = QPushButton("Deallocate Process")
        self.deallocate_btn.clicked.connect(self.deallocate_memory)

        input_layout.addRow("Process ID:", self.process_id_edit)
        input_layout.addRow("Process Size (KB):", self.process_size_edit)
        input_layout.addRow(self.allocate_btn, self.deallocate_btn)

        # Page replacement inputs
        self.page_sequence_edit = QLineEdit("1,2,3,4,1,2,5,1,2,3,4,5")
        self.num_frames_edit = QSpinBox()
        self.num_frames_edit.setRange(1, 8)
        self.num_frames_edit.setValue(3)

        self.run_replacement_btn = QPushButton("Run Page Replacement")
        self.run_replacement_btn.clicked.connect(self.run_page_replacement)

        input_layout.addRow("Page Sequence:", self.page_sequence_edit)
        input_layout.addRow("Number of Frames:", self.num_frames_edit)
        input_layout.addRow(self.run_replacement_btn)

        input_group.setLayout(input_layout)
        self.layout().insertWidget(3, input_group)

        # Animation controls for page replacement
        anim_group = QGroupBox("Animation Controls")
        anim_layout = QHBoxLayout()
        self.prev_step_btn = QPushButton("Previous Step")
        self.prev_step_btn.clicked.connect(self.page_replacement_viz.prev_step)
        self.next_step_btn = QPushButton("Next Step")
        self.next_step_btn.clicked.connect(self.page_replacement_viz.next_step)
        anim_layout.addWidget(self.prev_step_btn)
        anim_layout.addWidget(self.next_step_btn)
        anim_group.setLayout(anim_layout)
        self.layout().insertWidget(4, anim_group)

        # Results display
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(150)
        self.layout().addWidget(self.results_text)

    def create_visualization_widget(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # Splitter for different visualizations
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Memory layout
        layout.addWidget(QLabel("<b>Memory Layout:</b>"))
        layout.addWidget(self.memory_layout)

        # Page table
        layout.addWidget(QLabel("<b>Page Table:</b>"))
        layout.addWidget(self.page_table_widget)

        # Page replacement visualization
        layout.addWidget(QLabel("<b>Page Replacement:</b>"))
        layout.addWidget(self.page_replacement_viz)

        widget.setLayout(layout)
        return widget

    def on_concept_changed(self, concept):
        self.current_concept = concept
        self.update_algorithm_options()
        self.update_ui_visibility()

    def on_algorithm_changed(self, algorithm):
        self.current_algorithm = algorithm

    def update_algorithm_options(self):
        self.algo_combo.clear()
        if self.current_concept == "Contiguous Allocation":
            self.algo_combo.addItems(["First Fit", "Best Fit", "Worst Fit"])
        elif self.current_concept == "Page Replacement":
            self.algo_combo.addItems(["FIFO", "LRU", "Optimal"])
        else:
            self.algo_combo.addItem("Default")

    def update_ui_visibility(self):
        # Show/hide controls based on concept
        is_contiguous = self.current_concept == "Contiguous Allocation"
        is_page_replacement = self.current_concept == "Page Replacement"

        self.memory_size_edit.setEnabled(is_contiguous)
        self.process_id_edit.setEnabled(is_contiguous)
        self.process_size_edit.setEnabled(is_contiguous)
        self.allocate_btn.setEnabled(is_contiguous)
        self.deallocate_btn.setEnabled(is_contiguous)

        self.page_sequence_edit.setEnabled(is_page_replacement)
        self.num_frames_edit.setEnabled(is_page_replacement)
        self.run_replacement_btn.setEnabled(is_page_replacement)
        self.prev_step_btn.setEnabled(is_page_replacement)
        self.next_step_btn.setEnabled(is_page_replacement)

    def allocate_memory(self):
        if self.current_concept != "Contiguous Allocation":
            return

        process_id = self.process_id_edit.text().strip()
        if not process_id:
            QMessageBox.warning(self, "Error", "Process ID cannot be empty")
            return

        process_size = self.process_size_edit.value()

        # Initialize memory blocks if empty
        if not self.memory_blocks:
            total_memory = self.memory_size_edit.value()
            self.memory_blocks = [MemoryBlock(0, total_memory)]
            self.total_memory = total_memory

        # Try to allocate
        if self.current_algorithm == "First Fit":
            address = MemoryManager.first_fit(self.memory_blocks, process_size, process_id)
        elif self.current_algorithm == "Best Fit":
            address = MemoryManager.best_fit(self.memory_blocks, process_size, process_id)
        elif self.current_algorithm == "Worst Fit":
            address = MemoryManager.worst_fit(self.memory_blocks, process_size, process_id)

        if address is not None:
            self.memory_layout.set_blocks(self.memory_blocks)
            self.update_status(f"Allocated {process_size}KB to {process_id} at address {address}")
            self.process_id_edit.setText(f"P{len([b for b in self.memory_blocks if not b.is_free]) + 1}")
        else:
            QMessageBox.warning(self, "Allocation Failed", f"No suitable block found for {process_size}KB")

    def deallocate_memory(self):
        if self.current_concept != "Contiguous Allocation":
            return

        process_id = self.process_id_edit.text().strip()
        if not process_id:
            QMessageBox.warning(self, "Error", "Process ID cannot be empty")
            return

        if MemoryManager.deallocate_memory(self.memory_blocks, process_id):
            self.memory_layout.set_blocks(self.memory_blocks)
            self.update_status(f"Deallocated memory for {process_id}")
        else:
            QMessageBox.warning(self, "Deallocation Failed", f"Process {process_id} not found")

    def run_page_replacement(self):
        if self.current_concept != "Page Replacement":
            return

        try:
            page_sequence = [int(x.strip()) for x in self.page_sequence_edit.text().split(',')]
            num_frames = self.num_frames_edit.value()

            if self.current_algorithm == "FIFO":
                result = PageReplacement.fifo(page_sequence, num_frames)
            elif self.current_algorithm == "LRU":
                result = PageReplacement.lru(page_sequence, num_frames)
            elif self.current_algorithm == "Optimal":
                result = PageReplacement.optimal(page_sequence, num_frames)

            self.page_replacement_viz.set_history(result['history'])

            # Display results
            text = f"Page Replacement Results ({self.current_algorithm}):\n"
            text += f"Total Pages: {result['total_pages']}\n"
            text += f"Page Faults: {result['page_faults']}\n"
            text += ".2f"
            self.results_text.setText(text)

            self.update_status(f"Page replacement simulation completed with {result['page_faults']} faults")

        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid page sequence format")

    def on_play(self):
        if self.current_concept == "Page Replacement" and hasattr(self, 'page_replacement_result'):
            self.animation_timer.start(1000)  # 1 second per step

    def on_pause(self):
        self.animation_timer.stop()

    def on_reset(self):
        self.animation_timer.stop()
        self.memory_blocks = []
        self.memory_layout.set_blocks([])
        self.page_table_widget.set_page_table({})
        self.page_replacement_viz.set_history([])
        self.results_text.clear()
        self.update_status("Reset")

    def animate_step(self):
        self.page_replacement_viz.next_step()