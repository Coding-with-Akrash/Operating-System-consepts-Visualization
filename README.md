# OS Concepts Visualizer

A GUI application for visualizing and demonstrating key operating system concepts, built with Python and PyQt6.

## Features

### CPU Scheduling Algorithms
- **First Come First Served (FCFS)**
- **Shortest Job First (SJF)**
- **Round Robin**
- **Priority Scheduling**

Interactive features:
- Add custom processes with arrival time, burst time, and priority
- Select scheduling algorithm
- Visualize execution with Gantt charts
- View performance metrics (waiting time, turnaround time)

### Planned Features
- Deadlock Handling (Banker's Algorithm, Resource Allocation Graph)
- Memory Management (Paging, Segmentation)
- File Systems
- Process Synchronization

## Installation

1. Ensure Python 3.8+ is installed
2. Install PyQt6:
   ```bash
   pip install PyQt6
   ```
3. Run the application:
   ```bash
   python main.py
   ```

## Project Structure

```
os_visualizer/
├── main.py                 # Application entry point
├── gui/
│   ├── main_window.py      # Main application window
│   └── components/
│       └── base_visualizer.py  # Base class for visualizers
├── concepts/
│   └── cpu_scheduling/
│       ├── algorithms.py   # Scheduling algorithms
│       └── visualizer.py   # GUI for CPU scheduling
├── plans/
│   └── architecture_plan.md # Detailed design document
└── README.md
```

## Usage

1. Launch the application
2. Navigate through the concept tree on the left
3. For CPU Scheduling:
   - Add processes using the input form
   - Select an algorithm from the dropdown
   - Click "Play" to run the simulation
   - View the Gantt chart and metrics

## Architecture

The application follows a modular MVC-inspired architecture:
- **Model**: Algorithm implementations
- **View**: PyQt6-based GUI components
- **Controller**: User interaction handling

Each OS concept is implemented as a separate module for easy extension and maintenance.

## Contributing

The codebase is designed for easy addition of new concepts. To add a new visualizer:

1. Create a new directory under `concepts/`
2. Implement the algorithm logic
3. Create a visualizer class inheriting from `BaseVisualizer`
4. Add navigation entries in `main_window.py`

## License

This project is for educational purposes.