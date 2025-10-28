"""
KeyKraken - Advanced Macro Automation Application
A Qt-based application for creating and executing automation macros
"""

import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QLabel, QTextEdit, QDialog,
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QMessageBox,
    QSplitter, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QProgressDialog, QInputDialog
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QIcon, QPixmap, QFont, QColor

import pyautogui
import pynput
from pynput import mouse, keyboard


class MacroRecorder(QThread):
    """Thread for recording mouse and keyboard actions"""
    step_recorded = Signal(dict)
    recording_stopped = Signal()
    
    def __init__(self):
        super().__init__()
        self.recording = False
        self.steps = []
        self.mouse_listener = None
        self.keyboard_listener = None
        
    def run(self):
        self.recording = True
        self.steps = []
        
        def on_click(x, y, button, pressed):
            if not self.recording:
                return False
            if pressed:
                step = {
                    "name": f"Click at ({x}, {y})",
                    "type": "click",
                    "value": [x, y],
                    "delay": 0.25,
                    "button": "left" if button == mouse.Button.left else "right"
                }
                self.steps.append(step)
                self.step_recorded.emit(step)
        
        def on_press(key):
            if not self.recording:
                return False
            try:
                key_name = key.char
            except AttributeError:
                key_name = str(key).replace('Key.', '')
            
            step = {
                "name": f"Press key: {key_name}",
                "type": "keypress",
                "value": key_name,
                "delay": 0.1
            }
            self.steps.append(step)
            self.step_recorded.emit(step)
        
        self.mouse_listener = mouse.Listener(on_click=on_click)
        self.keyboard_listener = keyboard.Listener(on_press=on_press)
        
        self.mouse_listener.start()
        self.keyboard_listener.start()
        
        while self.recording:
            time.sleep(0.1)
        
        self.mouse_listener.stop()
        self.keyboard_listener.stop()
        self.recording_stopped.emit()
    
    def stop_recording(self):
        self.recording = False


class MacroExecutor(QThread):
    """Thread for executing macro steps"""
    step_executed = Signal(int, str)
    execution_finished = Signal(bool, str)
    iteration_started = Signal(int, int)
    
    def __init__(self, steps: List[Dict[str, Any]], iterations: int = 1):
        super().__init__()
        self.steps = steps
        self.iterations = iterations
        self.should_stop = False
        
    def run(self):
        try:
            pyautogui.FAILSAFE = True
            
            for iteration in range(self.iterations):
                if self.should_stop:
                    self.execution_finished.emit(False, "Execution stopped by user")
                    return
                
                self.iteration_started.emit(iteration + 1, self.iterations)
                
                for idx, step in enumerate(self.steps):
                    if self.should_stop:
                        self.execution_finished.emit(False, "Execution stopped by user")
                        return
                    
                    self.step_executed.emit(idx, f"[{iteration + 1}/{self.iterations}] Executing: {step['name']}")
                    
                    step_type = step.get('type', '')
                    value = step.get('value', '')
                    delay = step.get('delay', 0.25)
                    
                    if step_type == 'click':
                        if isinstance(value, list) and len(value) == 2:
                            x, y = value
                        else:
                            x, y = 0, 0
                        button = step.get('button', 'left')
                        pyautogui.click(x, y, button=button)
                    
                    elif step_type == 'keypress':
                        pyautogui.press(value)
                    
                    elif step_type == 'type':
                        pyautogui.typewrite(value, interval=0.05)
                    
                    elif step_type == 'scroll':
                        pyautogui.scroll(int(value))
                    
                    elif step_type == 'delay':
                        time.sleep(float(value))
                    
                    elif step_type == 'move':
                        if isinstance(value, list) and len(value) == 2:
                            x, y = value
                        else:
                            x, y = 0, 0
                        pyautogui.moveTo(x, y)
                    
                    time.sleep(delay)
            
            self.execution_finished.emit(True, f"Execution completed successfully ({self.iterations} iteration(s))")
        
        except Exception as e:
            self.execution_finished.emit(False, f"Error: {str(e)}")
    
    def stop(self):
        self.should_stop = True


class StepEditorDialog(QDialog):
    """Dialog for adding/editing individual macro steps"""
    
    def __init__(self, parent=None, step_data: Optional[Dict] = None):
        super().__init__(parent)
        self.step_data = step_data or {}
        self.setWindowTitle("Edit Step" if step_data else "Add Step")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Step name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Step Name:"))
        self.name_input = QLineEdit(self.step_data.get('name', ''))
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # Step type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(['click', 'keypress', 'type', 'scroll', 'move', 'delay'])
        current_type = self.step_data.get('type', 'click')
        self.type_combo.setCurrentText(current_type)
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)
        
        # Value input (changes based on type)
        self.value_widget = QWidget()
        self.value_layout = QHBoxLayout()
        self.value_widget.setLayout(self.value_layout)
        layout.addWidget(self.value_widget)
        
        # Delay
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("Delay (seconds):"))
        self.delay_input = QDoubleSpinBox()
        self.delay_input.setRange(0, 10)
        self.delay_input.setSingleStep(0.1)
        self.delay_input.setValue(self.step_data.get('delay', 0.25))
        delay_layout.addWidget(self.delay_input)
        layout.addLayout(delay_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.on_type_changed(current_type)
        
    def on_type_changed(self, step_type: str):
        # Clear existing widgets
        while self.value_layout.count():
            child = self.value_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self.value_layout.addWidget(QLabel("Value:"))
        
        if step_type in ['click', 'move']:
            self.x_input = QSpinBox()
            self.x_input.setRange(0, 10000)
            self.y_input = QSpinBox()
            self.y_input.setRange(0, 10000)
            
            value = self.step_data.get('value', [0, 0])
            if isinstance(value, list) and len(value) == 2:
                self.x_input.setValue(value[0])
                self.y_input.setValue(value[1])
            
            self.value_layout.addWidget(QLabel("X:"))
            self.value_layout.addWidget(self.x_input)
            self.value_layout.addWidget(QLabel("Y:"))
            self.value_layout.addWidget(self.y_input)
            
            if step_type == 'click':
                self.button_combo = QComboBox()
                self.button_combo.addItems(['left', 'right', 'middle'])
                self.button_combo.setCurrentText(self.step_data.get('button', 'left'))
                self.value_layout.addWidget(QLabel("Button:"))
                self.value_layout.addWidget(self.button_combo)
        
        elif step_type in ['keypress', 'type']:
            self.text_input = QLineEdit(str(self.step_data.get('value', '')))
            self.value_layout.addWidget(self.text_input)
        
        elif step_type == 'scroll':
            self.scroll_input = QSpinBox()
            self.scroll_input.setRange(-1000, 1000)
            self.scroll_input.setValue(int(self.step_data.get('value', 0)))
            self.value_layout.addWidget(self.scroll_input)
        
        elif step_type == 'delay':
            self.delay_value_input = QDoubleSpinBox()
            self.delay_value_input.setRange(0, 60)
            self.delay_value_input.setSingleStep(0.1)
            self.delay_value_input.setValue(float(self.step_data.get('value', 1.0)))
            self.value_layout.addWidget(self.delay_value_input)
    
    def get_step_data(self) -> Dict[str, Any]:
        step_type = self.type_combo.currentText()
        step = {
            "name": self.name_input.text(),
            "type": step_type,
            "delay": self.delay_input.value()
        }
        
        if step_type in ['click', 'move']:
            step['value'] = [self.x_input.value(), self.y_input.value()]
            if step_type == 'click':
                step['button'] = self.button_combo.currentText()
        
        elif step_type in ['keypress', 'type']:
            step['value'] = self.text_input.text()
        
        elif step_type == 'scroll':
            step['value'] = self.scroll_input.value()
        
        elif step_type == 'delay':
            step['value'] = self.delay_value_input.value()
        
        return step


class KeyKrakenMain(QMainWindow):
    """Main application window for KeyKraken"""
    
    def __init__(self):
        super().__init__()
        self.scenarios_dir = Path("scenarios")
        self.scenarios_dir.mkdir(exist_ok=True)
        self.current_scenario = None
        self.current_steps = []
        self.recorder = None
        self.executor = None
        
        self.init_ui()
        self.load_scenarios_list()
        
    def init_ui(self):
        self.setWindowTitle("KeyKraken - Macro Automation")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set icon if available
        icon_path = Path("images/icon.png")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        
        # Left panel - Scenarios list
        left_panel = self.create_left_panel()
        
        # Right panel - Scenario details
        right_panel = self.create_right_panel()
        
        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
    def create_left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Header
        header_label = QLabel("Scenarios")
        header_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(header_label)
        
        # Scenarios list
        self.scenarios_list = QListWidget()
        self.scenarios_list.itemClicked.connect(self.on_scenario_selected)
        layout.addWidget(self.scenarios_list)
        
        # Buttons
        btn_layout = QVBoxLayout()
        
        new_btn = QPushButton("New Scenario")
        new_btn.clicked.connect(self.new_scenario)
        btn_layout.addWidget(new_btn)
        
        delete_btn = QPushButton("Delete Scenario")
        delete_btn.clicked.connect(self.delete_scenario)
        btn_layout.addWidget(delete_btn)
        
        refresh_btn = QPushButton("Refresh List")
        refresh_btn.clicked.connect(self.load_scenarios_list)
        btn_layout.addWidget(refresh_btn)
        
        layout.addLayout(btn_layout)
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Scenario info
        info_group = QGroupBox("Scenario Information")
        info_layout = QVBoxLayout()
        
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_input = QLineEdit()
        name_layout.addWidget(self.name_input)
        info_layout.addLayout(name_layout)
        
        info_layout.addWidget(QLabel("Description:"))
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        info_layout.addWidget(self.description_input)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Steps table
        steps_group = QGroupBox("Macro Steps")
        steps_layout = QVBoxLayout()
        
        self.steps_table = QTableWidget()
        self.steps_table.setColumnCount(5)
        self.steps_table.setHorizontalHeaderLabels(["#", "Name", "Type", "Value", "Delay"])
        self.steps_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.steps_table.setSelectionBehavior(QTableWidget.SelectRows)
        steps_layout.addWidget(self.steps_table)
        
        # Steps buttons
        steps_btn_layout = QHBoxLayout()
        
        add_step_btn = QPushButton("Add Step")
        add_step_btn.clicked.connect(self.add_step)
        steps_btn_layout.addWidget(add_step_btn)
        
        edit_step_btn = QPushButton("Edit Step")
        edit_step_btn.clicked.connect(self.edit_step)
        steps_btn_layout.addWidget(edit_step_btn)
        
        delete_step_btn = QPushButton("Delete Step")
        delete_step_btn.clicked.connect(self.delete_step)
        steps_btn_layout.addWidget(delete_step_btn)
        
        move_up_btn = QPushButton("↑ Move Up")
        move_up_btn.clicked.connect(self.move_step_up)
        steps_btn_layout.addWidget(move_up_btn)
        
        move_down_btn = QPushButton("↓ Move Down")
        move_down_btn.clicked.connect(self.move_step_down)
        steps_btn_layout.addWidget(move_down_btn)
        
        steps_layout.addLayout(steps_btn_layout)
        
        # Record button
        record_layout = QHBoxLayout()
        self.record_btn = QPushButton("🔴 Start Recording")
        self.record_btn.clicked.connect(self.toggle_recording)
        record_layout.addWidget(self.record_btn)
        steps_layout.addLayout(record_layout)
        
        steps_group.setLayout(steps_layout)
        layout.addWidget(steps_group)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        # Iterations control
        iterations_layout = QHBoxLayout()
        iterations_layout.addWidget(QLabel("Run"))
        self.iterations_spinbox = QSpinBox()
        self.iterations_spinbox.setRange(1, 1000)
        self.iterations_spinbox.setValue(1)
        self.iterations_spinbox.setFixedWidth(80)
        iterations_layout.addWidget(self.iterations_spinbox)
        iterations_layout.addWidget(QLabel("time(s)"))
        iterations_layout.addStretch()
        action_layout.addLayout(iterations_layout)
        
        save_btn = QPushButton("💾 Save Scenario")
        save_btn.clicked.connect(self.save_scenario)
        action_layout.addWidget(save_btn)
        
        execute_btn = QPushButton("▶️ Execute Scenario")
        execute_btn.clicked.connect(self.execute_scenario)
        action_layout.addWidget(execute_btn)
        
        layout.addLayout(action_layout)
        
        return panel
    
    def load_scenarios_list(self):
        self.scenarios_list.clear()
        for file in self.scenarios_dir.glob("*.json"):
            self.scenarios_list.addItem(file.stem)
    
    def on_scenario_selected(self, item):
        scenario_name = item.text()
        self.load_scenario(scenario_name)
    
    def load_scenario(self, scenario_name: str):
        scenario_path = self.scenarios_dir / f"{scenario_name}.json"
        if not scenario_path.exists():
            QMessageBox.warning(self, "Error", f"Scenario file not found: {scenario_name}")
            return
        
        try:
            with open(scenario_path, 'r') as f:
                data = json.load(f)
            
            self.current_scenario = scenario_name
            self.name_input.setText(data.get('name', ''))
            self.description_input.setPlainText(data.get('description', ''))
            self.current_steps = data.get('steps', [])
            self.refresh_steps_table()
            
            self.statusBar().showMessage(f"Loaded scenario: {scenario_name}")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load scenario: {str(e)}")
    
    def refresh_steps_table(self):
        self.steps_table.setRowCount(len(self.current_steps))
        
        for idx, step in enumerate(self.current_steps):
            self.steps_table.setItem(idx, 0, QTableWidgetItem(str(idx + 1)))
            self.steps_table.setItem(idx, 1, QTableWidgetItem(step.get('name', '')))
            self.steps_table.setItem(idx, 2, QTableWidgetItem(step.get('type', '')))
            self.steps_table.setItem(idx, 3, QTableWidgetItem(str(step.get('value', ''))))
            self.steps_table.setItem(idx, 4, QTableWidgetItem(str(step.get('delay', ''))))
    
    def new_scenario(self):
        name, ok = QInputDialog.getText(self, "New Scenario", "Enter scenario name:")
        if ok and name:
            self.current_scenario = name
            self.name_input.setText(name)
            self.description_input.clear()
            self.current_steps = []
            self.refresh_steps_table()
            self.statusBar().showMessage(f"Created new scenario: {name}")
    
    def delete_scenario(self):
        if not self.current_scenario:
            QMessageBox.warning(self, "Warning", "No scenario selected")
            return
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete '{self.current_scenario}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            scenario_path = self.scenarios_dir / f"{self.current_scenario}.json"
            if scenario_path.exists():
                scenario_path.unlink()
            self.load_scenarios_list()
            self.current_scenario = None
            self.name_input.clear()
            self.description_input.clear()
            self.current_steps = []
            self.refresh_steps_table()
            self.statusBar().showMessage("Scenario deleted")
    
    def add_step(self):
        dialog = StepEditorDialog(self)
        if dialog.exec():
            step_data = dialog.get_step_data()
            self.current_steps.append(step_data)
            self.refresh_steps_table()
    
    def edit_step(self):
        row = self.steps_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Warning", "Please select a step to edit")
            return
        
        dialog = StepEditorDialog(self, self.current_steps[row])
        if dialog.exec():
            self.current_steps[row] = dialog.get_step_data()
            self.refresh_steps_table()
    
    def delete_step(self):
        row = self.steps_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Warning", "Please select a step to delete")
            return
        
        del self.current_steps[row]
        self.refresh_steps_table()
    
    def move_step_up(self):
        row = self.steps_table.currentRow()
        if row <= 0:
            return
        
        self.current_steps[row], self.current_steps[row-1] = \
            self.current_steps[row-1], self.current_steps[row]
        self.refresh_steps_table()
        self.steps_table.selectRow(row - 1)
    
    def move_step_down(self):
        row = self.steps_table.currentRow()
        if row < 0 or row >= len(self.current_steps) - 1:
            return
        
        self.current_steps[row], self.current_steps[row+1] = \
            self.current_steps[row+1], self.current_steps[row]
        self.refresh_steps_table()
        self.steps_table.selectRow(row + 1)
    
    def toggle_recording(self):
        if self.recorder and self.recorder.recording:
            self.recorder.stop_recording()
            self.record_btn.setText("🔴 Start Recording")
            self.statusBar().showMessage("Recording stopped")
        else:
            self.recorder = MacroRecorder()
            self.recorder.step_recorded.connect(self.on_step_recorded)
            self.recorder.recording_stopped.connect(self.on_recording_stopped)
            self.recorder.start()
            self.record_btn.setText("⏹️ Stop Recording")
            self.statusBar().showMessage("Recording... (move mouse to top-left corner to stop)")
    
    def on_step_recorded(self, step: Dict):
        self.current_steps.append(step)
        self.refresh_steps_table()
    
    def on_recording_stopped(self):
        self.record_btn.setText("🔴 Start Recording")
        self.statusBar().showMessage("Recording complete")
    
    def save_scenario(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Warning", "Please enter a scenario name")
            return
        
        scenario_data = {
            "version": "1.2",
            "name": name,
            "description": self.description_input.toPlainText(),
            "steps": self.current_steps,
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        scenario_path = self.scenarios_dir / f"{name}.json"
        
        try:
            with open(scenario_path, 'w') as f:
                json.dump(scenario_data, f, indent=4)
            
            self.current_scenario = name
            self.load_scenarios_list()
            self.statusBar().showMessage(f"Scenario saved: {name}")
            QMessageBox.information(self, "Success", "Scenario saved successfully!")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save scenario: {str(e)}")
    
    def execute_scenario(self):
        if not self.current_steps:
            QMessageBox.warning(self, "Warning", "No steps to execute")
            return
        
        iterations = self.iterations_spinbox.value()
        
        reply = QMessageBox.question(
            self, "Execute Scenario",
            f"Execute {len(self.current_steps)} steps {iterations} time(s)?\n\nYou have 3 seconds to position windows.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # 3 second countdown
        time.sleep(3)
        
        self.executor = MacroExecutor(self.current_steps, iterations)
        self.executor.step_executed.connect(self.on_step_executed)
        self.executor.execution_finished.connect(self.on_execution_finished)
        if hasattr(self.executor, 'iteration_started'):
            self.executor.iteration_started.connect(self.on_iteration_started)
        self.executor.start()
        
        self.statusBar().showMessage("Executing scenario...")
    
    def on_step_executed(self, step_idx: int, message: str):
        self.statusBar().showMessage(f"Step {step_idx + 1}/{len(self.current_steps)}: {message}")
        self.steps_table.selectRow(step_idx)
    
    def on_iteration_started(self, current: int, total: int):
        self.statusBar().showMessage(f"Starting iteration {current} of {total}")
    
    def on_execution_finished(self, success: bool, message: str):
        self.statusBar().showMessage(message)
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.warning(self, "Execution Result", message)


class SplashScreen(QDialog):
    """Splash screen with header image"""
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.init_ui()
        
        # Auto close after 2 seconds
        QTimer.singleShot(2000, self.accept)
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        header_path = Path("images/keykraken_header_v2.png")
        if header_path.exists():
            pixmap = QPixmap(str(header_path))
            label = QLabel()
            label.setPixmap(pixmap)
            layout.addWidget(label)
        else:
            title = QLabel("KeyKraken")
            title.setFont(QFont("Arial", 24, QFont.Bold))
            title.setAlignment(Qt.AlignCenter)
            layout.addWidget(title)
            
            subtitle = QLabel("Macro Automation Tool")
            subtitle.setAlignment(Qt.AlignCenter)
            layout.addWidget(subtitle)
        
        self.setLayout(layout)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("KeyKraken")
    
    # Show splash screen
    splash = SplashScreen()
    splash.exec()
    
    # Show main window
    window = KeyKrakenMain()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()