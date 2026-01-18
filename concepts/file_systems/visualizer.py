from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem,
    QComboBox, QSpinBox, QLineEdit, QMessageBox, QGroupBox,
    QFormLayout, QSplitter, QTextEdit, QGridLayout, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QFont, QPen
from gui.components.base_visualizer import BaseVisualizer
from .algorithms import FileSystem, FATFileSystem, NTFSFileSystem, Ext4FileSystem, File, Directory

class DiskVisualizationWidget(QWidget):
    def __init__(self, file_system: FileSystem):
        super().__init__()
        self.file_system = file_system
        self.setMinimumHeight(300)

    def paintEvent(self, event):
        if not self.file_system:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        blocks_per_row = 10
        block_size = min(width // blocks_per_row, height // (self.file_system.total_blocks // blocks_per_row + 1))

        for i, block in enumerate(self.file_system.disk):
            row = i // blocks_per_row
            col = i % blocks_per_row
            x = col * block_size
            y = row * block_size

            if block.allocated:
                color = QColor(255, 100, 100) if block.file else QColor(100, 100, 255)
            else:
                color = QColor(200, 200, 200)

            painter.fillRect(x, y, block_size - 2, block_size - 2, color)
            painter.setPen(QPen(Qt.GlobalColor.black, 1))
            painter.drawRect(x, y, block_size - 2, block_size - 2)

            # Draw block number
            painter.setFont(QFont("Arial", 6))
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.drawText(x + 2, y + block_size - 4, str(i))

class DirectoryTreeWidget(QTreeWidget):
    def __init__(self, file_system: FileSystem):
        super().__init__()
        self.file_system = file_system
        self.setHeaderLabel("Directory Structure")
        self.refresh_tree()

    def refresh_tree(self):
        self.clear()
        self.add_directory_to_tree(self.file_system.root, None)

    def add_directory_to_tree(self, directory: Directory, parent_item):
        item = QTreeWidgetItem([directory.name or "root"])
        if parent_item:
            parent_item.addChild(item)
        else:
            self.addTopLevelItem(item)

        for file in directory.files:
            file_item = QTreeWidgetItem([f"{file.name} ({file.size} bytes)"])
            item.addChild(file_item)

        for subdir in directory.subdirectories:
            self.add_directory_to_tree(subdir, item)

class FileSystemVisualizer(BaseVisualizer):
    def __init__(self):
        self.file_system = FileSystem()
        self.disk_widget = DiskVisualizationWidget(self.file_system)
        self.directory_tree = DirectoryTreeWidget(self.file_system)
        super().__init__("File Systems")
        self.setup_specific_ui()

    def setup_specific_ui(self):
        # File System Type Selection
        fs_group = QGroupBox("File System Type")
        fs_layout = QHBoxLayout()
        self.fs_combo = QComboBox()
        self.fs_combo.addItems(["Generic", "FAT", "NTFS", "ext4"])
        self.fs_combo.currentTextChanged.connect(self.on_fs_changed)
        fs_layout.addWidget(QLabel("Type:"))
        fs_layout.addWidget(self.fs_combo)
        fs_layout.addStretch()
        fs_group.setLayout(fs_layout)
        self.layout().insertWidget(1, fs_group)

        # Allocation Method
        alloc_group = QGroupBox("Allocation Method")
        alloc_layout = QHBoxLayout()
        self.alloc_combo = QComboBox()
        self.alloc_combo.addItems(["contiguous", "linked", "indexed"])
        self.alloc_combo.currentTextChanged.connect(self.on_alloc_changed)
        alloc_layout.addWidget(QLabel("Method:"))
        alloc_layout.addWidget(self.alloc_combo)
        alloc_layout.addStretch()
        alloc_group.setLayout(alloc_layout)
        self.layout().insertWidget(2, alloc_group)

        # File Operations
        file_group = QGroupBox("File Operations")
        file_layout = QFormLayout()

        self.path_edit = QLineEdit("/")
        self.name_edit = QLineEdit("file.txt")
        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 10000)
        self.size_spin.setValue(1024)

        file_layout.addRow("Path:", self.path_edit)
        file_layout.addRow("Name:", self.name_edit)
        file_layout.addRow("Size (bytes):", self.size_spin)

        btn_layout = QHBoxLayout()
        create_file_btn = QPushButton("Create File")
        create_file_btn.clicked.connect(self.create_file)
        delete_file_btn = QPushButton("Delete File")
        delete_file_btn.clicked.connect(self.delete_file)
        create_dir_btn = QPushButton("Create Directory")
        create_dir_btn.clicked.connect(self.create_directory)

        btn_layout.addWidget(create_file_btn)
        btn_layout.addWidget(delete_file_btn)
        btn_layout.addWidget(create_dir_btn)
        btn_layout.addStretch()

        file_layout.addRow(btn_layout)
        file_group.setLayout(file_layout)
        self.layout().insertWidget(3, file_group)

        # Directory Tree and File Info
        tree_info_splitter = QSplitter(Qt.Orientation.Horizontal)

        tree_group = QGroupBox("Directory Structure")
        tree_layout = QVBoxLayout()
        tree_layout.addWidget(self.directory_tree)
        tree_group.setLayout(tree_layout)
        tree_info_splitter.addWidget(tree_group)

        info_group = QGroupBox("File/Directory Info")
        info_layout = QVBoxLayout()
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(150)
        info_layout.addWidget(self.info_text)
        info_group.setLayout(info_layout)
        tree_info_splitter.addWidget(info_group)

        tree_info_splitter.setSizes([400, 300])
        self.layout().insertWidget(4, tree_info_splitter)

        # Connect tree item click
        self.directory_tree.itemClicked.connect(self.on_tree_item_clicked)

        # Disk Usage Info
        self.usage_label = QLabel()
        self.layout().addWidget(self.usage_label)

    def create_visualization_widget(self):
        # Return a container widget
        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.disk_widget)
        widget.setLayout(layout)
        return widget

    def on_fs_changed(self, fs_type):
        if fs_type == "FAT":
            self.file_system = FATFileSystem()
        elif fs_type == "NTFS":
            self.file_system = NTFSFileSystem()
        elif fs_type == "ext4":
            self.file_system = Ext4FileSystem()
        else:
            self.file_system = FileSystem()

        self.disk_widget.file_system = self.file_system
        self.directory_tree.file_system = self.file_system
        self.directory_tree.refresh_tree()
        self.update_disk_usage()
        self.disk_widget.update()

    def on_alloc_changed(self, method):
        self.file_system.allocation_method = method

    def create_file(self):
        try:
            path = self.path_edit.text().strip()
            name = self.name_edit.text().strip()
            size = self.size_spin.value()

            if not name:
                QMessageBox.warning(self, "Error", "File name cannot be empty")
                return

            if self.file_system.create_file(path, name, size):
                self.directory_tree.refresh_tree()
                self.disk_widget.update()
                self.update_disk_usage()
                self.update_status(f"Created file: {name}")
            else:
                QMessageBox.warning(self, "Error", "Failed to create file")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def delete_file(self):
        try:
            path = self.path_edit.text().strip()
            name = self.name_edit.text().strip()

            if not name:
                QMessageBox.warning(self, "Error", "File name cannot be empty")
                return

            if self.file_system.delete_file(path, name):
                self.directory_tree.refresh_tree()
                self.disk_widget.update()
                self.update_disk_usage()
                self.update_status(f"Deleted file: {name}")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete file")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def create_directory(self):
        try:
            path = self.path_edit.text().strip()
            name = self.name_edit.text().strip()

            if not name:
                QMessageBox.warning(self, "Error", "Directory name cannot be empty")
                return

            if self.file_system.create_directory(path, name):
                self.directory_tree.refresh_tree()
                self.update_status(f"Created directory: {name}")
            else:
                QMessageBox.warning(self, "Error", "Failed to create directory")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def update_disk_usage(self):
        usage = self.file_system.get_disk_usage()
        self.usage_label.setText(
            f"Disk Usage: {usage['allocated_blocks']}/{usage['total_blocks']} blocks "
            ".1f"
        )

    def on_play(self):
        # Could implement simulation of file operations
        pass

    def on_pause(self):
        pass

    def on_tree_item_clicked(self, item, column):
        """Show information about selected file or directory."""
        text = item.text(column)
        if text.startswith("root"):
            self.show_directory_info(self.file_system.root)
        elif " (" in text:  # It's a file
            file_name = text.split(" (")[0]
            # Find the file in the directory structure
            self.show_file_info(file_name)
        else:  # It's a directory
            dir_name = text
            # Find the directory
            self.show_directory_info_by_name(dir_name)

    def show_file_info(self, file_name):
        """Show information about a file."""
        def find_file(directory, name):
            for file in directory.files:
                if file.name == name:
                    return file
            for subdir in directory.subdirectories:
                result = find_file(subdir, name)
                if result:
                    return result
            return None

        file = find_file(self.file_system.root, file_name)
        if file:
            info = f"File Name: {file.name}\n"
            info += f"Size: {file.size} bytes\n"
            info += f"Blocks Allocated: {len(file.blocks)}\n"
            info += f"Block Indices: {file.blocks}\n"
            info += f"Allocation Method: {self.file_system.allocation_method}\n"
            if file.content:
                info += f"Content Preview: {file.content[:100]}...\n"
            self.info_text.setText(info)
        else:
            self.info_text.setText("File not found")

    def show_directory_info(self, directory):
        """Show information about a directory."""
        info = f"Directory: {directory.get_path()}\n"
        info += f"Files: {len(directory.files)}\n"
        info += f"Subdirectories: {len(directory.subdirectories)}\n"
        total_size = sum(f.size for f in directory.files)
        info += f"Total File Size: {total_size} bytes\n"
        self.info_text.setText(info)

    def show_directory_info_by_name(self, dir_name):
        """Find and show directory info by name."""
        def find_directory(directory, name):
            if directory.name == name:
                return directory
            for subdir in directory.subdirectories:
                result = find_directory(subdir, name)
                if result:
                    return result
            return None

        directory = find_directory(self.file_system.root, dir_name)
        if directory:
            self.show_directory_info(directory)
        else:
            self.info_text.setText("Directory not found")

    def on_reset(self):
        self.file_system = FileSystem()
        self.disk_widget.file_system = self.file_system
        self.directory_tree.file_system = self.file_system
        self.directory_tree.refresh_tree()
        self.disk_widget.update()
        self.update_disk_usage()
        self.info_text.clear()
        self.update_status("Reset")