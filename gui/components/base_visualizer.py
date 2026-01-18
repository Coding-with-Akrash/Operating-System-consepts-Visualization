from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import pyqtSignal

class BaseVisualizer(QWidget):
    """
    Base class for all OS concept visualizers.
    Provides common UI elements and functionality.
    """

    # Signals
    data_changed = pyqtSignal()  # Emitted when visualization data changes

    def __init__(self, title="Visualizer"):
        super().__init__()
        self.title = title
        self.setup_ui()

    def setup_ui(self):
        """Set up the basic UI structure."""
        layout = QVBoxLayout()

        # Title
        title_label = QLabel(f"<h2>{self.title}</h2>")
        layout.addWidget(title_label)

        # Control panel
        self.control_layout = QHBoxLayout()

        # Add common controls
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.on_play)
        self.control_layout.addWidget(self.play_button)

        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.on_pause)
        self.control_layout.addWidget(self.pause_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.on_reset)
        self.control_layout.addWidget(self.reset_button)

        # Add stretch to push controls to the left
        self.control_layout.addStretch()

        layout.addLayout(self.control_layout)

        # Visualization area (to be overridden by subclasses)
        self.visualization_widget = self.create_visualization_widget()
        layout.addWidget(self.visualization_widget)

        # Status/info area
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def create_visualization_widget(self):
        """
        Create the main visualization widget.
        Should be overridden by subclasses.
        """
        return QLabel("Visualization area - override create_visualization_widget()")

    def on_play(self):
        """Handle play button click."""
        pass

    def on_pause(self):
        """Handle pause button click."""
        pass

    def on_reset(self):
        """Handle reset button click."""
        pass

    def update_status(self, message):
        """Update the status message."""
        self.status_label.setText(message)

    def add_control(self, widget):
        """Add a custom control to the control panel."""
        self.control_layout.insertWidget(self.control_layout.count() - 1, widget)