from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QTreeWidget, QTreeWidgetItem,
    QStackedWidget, QWidget, QVBoxLayout, QLabel, QStatusBar,
    QToolBar, QMessageBox, QHBoxLayout, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon, QPalette, QColor
from concepts.cpu_scheduling.visualizer import CPUSchedulingVisualizer
from concepts.deadlock.visualizer import DeadlockVisualizer
from concepts.resource_allocation.visualizer import ResourceAllocationVisualizer
from concepts.memory_management.visualizer import MemoryManagementVisualizer
from concepts.synchronization.visualizer import SynchronizationVisualizer
from concepts.file_systems.visualizer import FileSystemVisualizer
from concepts.processes_threads.visualizer import ProcessesThreadsVisualizer
from concepts.io_management.visualizer import IOManagementVisualizer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OS Concepts Visualizer")
        self.setGeometry(100, 100, 1200, 800)

        self.setup_menu()
        self.setup_status_bar()
        self.setup_central_widget()
        self.setup_navigation()

    def setup_menu(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('File')
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu('View')

        # Help menu
        help_menu = menubar.addMenu('Help')
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def setup_central_widget(self):
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Navigation panel
        self.navigation_tree = QTreeWidget()
        self.navigation_tree.setHeaderLabel("OS Concepts")
        self.navigation_tree.itemClicked.connect(self.on_navigation_item_clicked)

        # Content panel
        self.content_stack = QStackedWidget()

        # Add a default widget
        default_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Select a concept from the navigation panel"))
        default_widget.setLayout(layout)
        self.content_stack.addWidget(default_widget)

        self.splitter.addWidget(self.navigation_tree)
        self.splitter.addWidget(self.content_stack)
        self.splitter.setSizes([300, 900])

        self.setCentralWidget(self.splitter)

    def setup_navigation(self):
        # CPU Scheduling
        cpu_item = QTreeWidgetItem(["CPU Scheduling"])
        cpu_item.addChild(QTreeWidgetItem(["First Come First Served (FCFS)"]))
        cpu_item.addChild(QTreeWidgetItem(["Shortest Job First (SJF)"]))
        cpu_item.addChild(QTreeWidgetItem(["Round Robin"]))
        cpu_item.addChild(QTreeWidgetItem(["Priority Scheduling"]))
        cpu_item.addChild(QTreeWidgetItem(["Multi-level Queue"]))

        # Deadlock Handling
        deadlock_item = QTreeWidgetItem(["Deadlock Handling"])
        deadlock_item.addChild(QTreeWidgetItem(["Resource Allocation Graph"]))
        deadlock_item.addChild(QTreeWidgetItem(["Banker's Algorithm"]))
        deadlock_item.addChild(QTreeWidgetItem(["Deadlock Detection"]))
        deadlock_item.addChild(QTreeWidgetItem(["Deadlock Prevention"]))

        # Resource Allocation
        resource_item = QTreeWidgetItem(["Resource Allocation"])
        resource_item.addChild(QTreeWidgetItem(["Single Instance"]))
        resource_item.addChild(QTreeWidgetItem(["Multiple Instances"]))

        # Memory Management
        memory_item = QTreeWidgetItem(["Memory Management"])
        memory_item.addChild(QTreeWidgetItem(["Contiguous Allocation"]))
        memory_item.addChild(QTreeWidgetItem(["Paging"]))
        memory_item.addChild(QTreeWidgetItem(["Segmentation"]))
        memory_item.addChild(QTreeWidgetItem(["Virtual Memory"]))
        memory_item.addChild(QTreeWidgetItem(["Page Replacement"]))

        # File Systems
        file_item = QTreeWidgetItem(["File Systems"])
        file_item.addChild(QTreeWidgetItem(["Directory Structure"]))
        file_item.addChild(QTreeWidgetItem(["File Allocation"]))
        file_item.addChild(QTreeWidgetItem(["File System Types"]))

        # Process Synchronization
        sync_item = QTreeWidgetItem(["Process Synchronization"])
        sync_item.addChild(QTreeWidgetItem(["Semaphores"]))
        sync_item.addChild(QTreeWidgetItem(["Monitors"]))
        sync_item.addChild(QTreeWidgetItem(["Mutexes"]))
        sync_item.addChild(QTreeWidgetItem(["Producer-Consumer"]))
        sync_item.addChild(QTreeWidgetItem(["Dining Philosophers"]))
        sync_item.addChild(QTreeWidgetItem(["Readers-Writers"]))

        # I/O Management
        io_item = QTreeWidgetItem(["I/O Management"])
        io_item.addChild(QTreeWidgetItem(["I/O Operations"]))
        io_item.addChild(QTreeWidgetItem(["Device Drivers"]))
        io_item.addChild(QTreeWidgetItem(["Buffering"]))
        io_item.addChild(QTreeWidgetItem(["Spooling"]))
        io_item.addChild(QTreeWidgetItem(["I/O Scheduling"]))

        # Processes and Threads
        processes_item = QTreeWidgetItem(["Processes and Threads"])
        processes_item.addChild(QTreeWidgetItem(["Process Lifecycle"]))
        processes_item.addChild(QTreeWidgetItem(["Process Control Block"]))
        processes_item.addChild(QTreeWidgetItem(["Thread Management"]))
        processes_item.addChild(QTreeWidgetItem(["Context Switching"]))
        processes_item.addChild(QTreeWidgetItem(["Inter-Process Communication"]))

        self.navigation_tree.addTopLevelItem(cpu_item)
        self.navigation_tree.addTopLevelItem(deadlock_item)
        self.navigation_tree.addTopLevelItem(resource_item)
        self.navigation_tree.addTopLevelItem(memory_item)
        self.navigation_tree.addTopLevelItem(file_item)
        self.navigation_tree.addTopLevelItem(sync_item)
        self.navigation_tree.addTopLevelItem(io_item)
        self.navigation_tree.addTopLevelItem(processes_item)

        self.navigation_tree.expandAll()

    def on_navigation_item_clicked(self, item, column):
        if item.parent():  # It's a child item
            concept = item.text(column)
            parent_concept = item.parent().text(column)
            self.status_bar.showMessage(f"Selected: {concept}")
            self.show_visualizer(parent_concept, concept)

    def show_visualizer(self, parent_concept, concept):
        # Remove existing widgets except the first (default)
        while self.content_stack.count() > 1:
            widget = self.content_stack.widget(1)
            self.content_stack.removeWidget(widget)
            widget.deleteLater()

        # Create appropriate visualizer
        if parent_concept == "CPU Scheduling":
            visualizer = CPUSchedulingVisualizer()
        elif parent_concept == "Deadlock Handling":
            visualizer = DeadlockVisualizer()
        elif parent_concept == "Resource Allocation":
            visualizer = ResourceAllocationVisualizer()
        elif parent_concept == "Memory Management":
            visualizer = MemoryManagementVisualizer()
        elif parent_concept == "File Systems":
            visualizer = FileSystemVisualizer()
        elif parent_concept == "I/O Management":
            visualizer = IOManagementVisualizer()
        elif parent_concept == "Processes and Threads":
            visualizer = ProcessesThreadsVisualizer()
        else:
            # Placeholder for other concepts
            visualizer = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel(f"Visualizer for: {concept}"))
            layout.addWidget(QLabel("(Implementation pending)"))
            visualizer.setLayout(layout)

        self.content_stack.addWidget(visualizer)
        self.content_stack.setCurrentIndex(1)

    def show_about(self):
        # TODO: Implement about dialog
        pass