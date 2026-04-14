#!/usr/bin/env python3

import sys
import os
import subprocess

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QGridLayout, QLabel, QComboBox,
                            QDoubleSpinBox, QSpinBox, QLineEdit, QPushButton,
                            QGroupBox, QCheckBox, QTextEdit, QFileDialog,
                            QMessageBox, QFrame, QSplitter, QToolTip,
                            QScrollArea, QSizePolicy)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap, QIcon, QCursor, QPainter, QPen

class FilterThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, command):
        super().__init__()
        self.command = command

    def run(self):
        try:
            result = subprocess.run(self.command, shell=False, capture_output=True, text=True)
            if result.returncode == 0:
                self.finished.emit(result.stdout.strip() or "Filter generated successfully!")
            else:
                self.error.emit(f"Error: {result.stderr.strip()}")
        except (OSError, subprocess.SubprocessError) as e:
            self.error.emit(f"Error: {e!s}")

class InfoButton(QLabel):
    """Custom info button with consistent styling"""
    def __init__(self, tooltip_text):
        super().__init__("?")
        self.setFixedSize(16, 16)
        self.setToolTip(tooltip_text)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: #6c757d;
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 9px;
                font-weight: bold;
            }
        """)

class ModernFilterGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Digital Filter Designer")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 700)

        # Define comprehensive tooltips
        self.tooltips = {
            'filter_type': 'Lowpass: Blocks high frequencies, smooths signals\nHighpass: Blocks low frequencies, removes DC components\nBandpass: Allows only frequencies in a specific range\nBandstop: Blocks frequencies in a specific range',
            'sampling_rate': 'The rate at which your signal is sampled (samples per second).\nMust be at least twice the highest frequency of interest (Nyquist theorem).',
            'filter_order': 'Higher order = steeper rolloff but more computation.\nTypical values: 2-8 for most applications.',
            'critical_freq_lowpass': 'Corner frequency where the filter response is -3dB.\nFrequencies above this will be attenuated.',
            'critical_freq_highpass': 'Corner frequency where the filter response is -3dB.\nFrequencies below this will be attenuated.',
            'freq_low': 'Lower cutoff frequency of the pass/stop band.',
            'freq_high': 'Upper cutoff frequency of the pass/stop band.',
            'language': 'Programming language for the generated filter code.',
            'class_name': 'Name of the generated filter class.',
            'file_name': 'Output filename (extension will be added automatically).',
            'plot': 'Generate a frequency response plot to visualize filter characteristics.'
        }

        # Set professional dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
                color: #e8e9ea;
            }

            QGroupBox {
                font-weight: 600;
                font-size: 13px;
                border: 1px solid #404040;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
                background-color: #2d2d2d;
                color: #e8e9ea;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                color: #b3b3b3;
                background-color: #2d2d2d;
                margin-left: 8px;
            }

            QLabel {
                color: #b3b3b3;
                font-size: 12px;
                font-weight: 500;
                background-color: transparent;
            }

            QComboBox {
                border: 1px solid #404040;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: #3a3a3a;
                color: #e8e9ea;
                min-height: 18px;
                font-size: 12px;
            }

            QComboBox:hover {
                border-color: #569cd6;
            }

            QComboBox:focus {
                border-color: #569cd6;
                outline: none;
            }

            QComboBox::drop-down {
                border: none;
                width: 20px;
                background-color: transparent;
            }

            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #b3b3b3;
                margin-right: 8px;
            }

            QComboBox QAbstractItemView {
                border: 1px solid #404040;
                background-color: #3a3a3a;
                color: #e8e9ea;
                selection-background-color: #569cd6;
                selection-color: #ffffff;
                border-radius: 4px;
            }

            QDoubleSpinBox, QSpinBox {
                border: 1px solid #404040;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: #3a3a3a;
                color: #e8e9ea;
                min-height: 18px;
                font-size: 12px;
            }

            QDoubleSpinBox:hover, QSpinBox:hover {
                border-color: #569cd6;
            }

            QDoubleSpinBox:focus, QSpinBox:focus {
                border-color: #569cd6;
                outline: none;
            }

            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button,
            QSpinBox::up-button, QSpinBox::down-button {
                width: 0px;
                height: 0px;
                border: none;
            }

            QDoubleSpinBox::up-arrow, QDoubleSpinBox::down-arrow,
            QSpinBox::up-arrow, QSpinBox::down-arrow {
                width: 0px;
                height: 0px;
            }

            QLineEdit {
                border: 1px solid #404040;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: #3a3a3a;
                color: #e8e9ea;
                min-height: 18px;
                font-size: 12px;
            }

            QLineEdit:hover {
                border-color: #569cd6;
            }

            QLineEdit:focus {
                border-color: #569cd6;
                outline: none;
            }

            QPushButton {
                background-color: #569cd6;
                border: none;
                border-radius: 6px;
                color: white;
                padding: 12px 24px;
                font-size: 13px;
                font-weight: 600;
                min-height: 16px;
            }

            QPushButton:hover {
                background-color: #4a86c7;
            }

            QPushButton:pressed {
                background-color: #3e73a8;
            }

            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }

            QTextEdit {
                border: 1px solid #404040;
                border-radius: 6px;
                background-color: #2d2d2d;
                color: #e8e9ea;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 11px;
                selection-background-color: #569cd6;
                selection-color: #ffffff;
            }

            QCheckBox {
                color: #b3b3b3;
                spacing: 8px;
                font-size: 12px;
                font-weight: 500;
            }

            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }

            QCheckBox::indicator:unchecked {
                border: 1px solid #404040;
                background-color: #3a3a3a;
                border-radius: 3px;
            }

            QCheckBox::indicator:unchecked:hover {
                border-color: #569cd6;
            }

            QCheckBox::indicator:checked {
                border: 1px solid #569cd6;
                background-color: #569cd6;
                border-radius: 3px;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }

            QFrame {
                border: 1px solid #404040;
                border-radius: 6px;
                background-color: #2d2d2d;
            }

            QScrollArea {
                border: none;
                background-color: transparent;
            }

            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }

            QScrollBar:vertical {
                background-color: #1a1a1a;
                width: 12px;
                border-radius: 6px;
            }

            QScrollBar::handle:vertical {
                background-color: #555555;
                min-height: 20px;
                border-radius: 6px;
                margin: 2px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #666666;
            }

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QToolTip {
                background-color: #1a1a1a;
                color: #e8e9ea;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px;
                font-size: 11px;
            }

            .title-label {
                color: #e8e9ea;
                font-size: 24px;
                font-weight: 700;
                background-color: transparent;
                border: none;
                padding: 16px;
            }

            .section-label {
                color: #b3b3b3;
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                background-color: transparent;
                margin: 8px 0 4px 0;
            }
        """)

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout with proper spacing
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(24)
        main_layout.setContentsMargins(24, 24, 24, 24)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel for controls
        left_panel = self.create_left_panel()
        right_panel = self.create_right_panel()

        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([500, 900])

    def create_left_panel(self):
        """Create the left control panel"""
        left_panel = QWidget()
        left_panel.setFixedWidth(500)
        left_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        # Create scroll area for the left panel
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Create the scrollable content widget
        scroll_content = QWidget()
        left_layout = QVBoxLayout(scroll_content)
        left_layout.setSpacing(24)
        left_layout.setContentsMargins(16, 16, 16, 16)

        # Title
        title_label = QLabel("Digital Filter Designer")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("QLabel { " + self.styleSheet().split('.title-label {')[1].split('}')[0] + " }")
        left_layout.addWidget(title_label)

        # Filter Configuration Group
        filter_group = self.create_filter_config_group()
        left_layout.addWidget(filter_group)

        # Output Configuration Group
        output_group = self.create_output_config_group()
        left_layout.addWidget(output_group)

        # Generate Button
        self.generate_button = QPushButton("Generate Filter")
        self.generate_button.clicked.connect(self.generate_filter)
        self.generate_button.setMinimumHeight(44)
        left_layout.addWidget(self.generate_button)

        # Status section
        status_label = QLabel("STATUS")
        status_label.setStyleSheet("QLabel { " + self.styleSheet().split('.section-label {')[1].split('}')[0] + " }")
        left_layout.addWidget(status_label)

        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(120)
        self.status_text.setPlaceholderText("Status messages will appear here...")
        left_layout.addWidget(self.status_text)

        left_layout.addStretch()

        # Set the scroll content
        scroll_area.setWidget(scroll_content)

        # Create container for scroll area
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(scroll_area)

        return container

    def create_filter_config_group(self):
        """Create the filter configuration group"""
        filter_group = QGroupBox("Filter Configuration")
        filter_layout = QGridLayout(filter_group)
        filter_layout.setSpacing(16)
        filter_layout.setContentsMargins(20, 24, 20, 20)

        row = 0

        # Filter Type
        filter_layout.addWidget(QLabel("Filter Type"), row, 0, Qt.AlignTop)
        type_layout = QHBoxLayout()
        type_layout.setSpacing(8)

        self.filter_type = QComboBox()
        self.filter_type.addItems(['lowpass', 'highpass', 'bandpass', 'bandstop'])
        self.filter_type.currentTextChanged.connect(self.on_filter_type_changed)
        type_layout.addWidget(self.filter_type)

        type_info = InfoButton(self.tooltips['filter_type'])
        type_layout.addWidget(type_info, 0, Qt.AlignVCenter)
        type_layout.addStretch()

        filter_layout.addLayout(type_layout, row, 1)
        row += 1

        # Sampling Rate
        filter_layout.addWidget(QLabel("Sampling Rate (Hz)"), row, 0, Qt.AlignTop)
        rate_layout = QHBoxLayout()
        rate_layout.setSpacing(8)

        self.sampling_rate = QDoubleSpinBox()
        self.sampling_rate.setRange(0.1, 100000)
        self.sampling_rate.setValue(500.0)
        self.sampling_rate.setDecimals(3)
        rate_layout.addWidget(self.sampling_rate)

        rate_info = InfoButton(self.tooltips['sampling_rate'])
        rate_layout.addWidget(rate_info, 0, Qt.AlignVCenter)
        rate_layout.addStretch()

        filter_layout.addLayout(rate_layout, row, 1)
        row += 1

        # Filter Order
        filter_layout.addWidget(QLabel("Filter Order"), row, 0, Qt.AlignTop)
        order_layout = QHBoxLayout()
        order_layout.setSpacing(8)

        self.filter_order = QSpinBox()
        self.filter_order.setRange(1, 20)
        self.filter_order.setValue(4)
        order_layout.addWidget(self.filter_order)

        order_info = InfoButton(self.tooltips['filter_order'])
        order_layout.addWidget(order_info, 0, Qt.AlignVCenter)
        order_layout.addStretch()

        filter_layout.addLayout(order_layout, row, 1)
        row += 1

        # Critical/Low Cutoff Frequency
        self.freq1_label = QLabel("Cutoff Frequency (Hz)")
        filter_layout.addWidget(self.freq1_label, row, 0, Qt.AlignTop)
        freq1_layout = QHBoxLayout()
        freq1_layout.setSpacing(8)

        self.freq1_input = QDoubleSpinBox()
        self.freq1_input.setRange(0.001, 50000)
        self.freq1_input.setValue(50.0)
        self.freq1_input.setDecimals(3)
        freq1_layout.addWidget(self.freq1_input)

        self.freq1_info = InfoButton(self.tooltips['critical_freq_lowpass'])
        freq1_layout.addWidget(self.freq1_info, 0, Qt.AlignVCenter)
        freq1_layout.addStretch()

        filter_layout.addLayout(freq1_layout, row, 1)
        row += 1

        # High Cutoff Frequency (for bandpass/bandstop)
        self.freq2_label = QLabel("High Cutoff Freq (Hz)")
        filter_layout.addWidget(self.freq2_label, row, 0, Qt.AlignTop)
        freq2_layout = QHBoxLayout()
        freq2_layout.setSpacing(8)

        self.freq2_input = QDoubleSpinBox()
        self.freq2_input.setRange(0.001, 50000)
        self.freq2_input.setValue(100.0)
        self.freq2_input.setDecimals(3)
        freq2_layout.addWidget(self.freq2_input)

        self.freq2_info = InfoButton(self.tooltips['freq_high'])
        freq2_layout.addWidget(self.freq2_info, 0, Qt.AlignVCenter)
        freq2_layout.addStretch()

        filter_layout.addLayout(freq2_layout, row, 1)

        # Initially hide freq2 controls
        self.freq2_label.hide()
        self.freq2_input.hide()
        self.freq2_info.hide()

        return filter_group

    def create_output_config_group(self):
        """Create the output configuration group"""
        output_group = QGroupBox("Output Configuration")
        output_layout = QGridLayout(output_group)
        output_layout.setSpacing(16)
        output_layout.setContentsMargins(20, 24, 20, 20)

        row = 0

        # Output Language
        output_layout.addWidget(QLabel("Programming Language"), row, 0, Qt.AlignTop)
        lang_layout = QHBoxLayout()
        lang_layout.setSpacing(8)

        self.output_language = QComboBox()
        self.output_language.addItems(['python', 'javascript', 'typescript', 'c++', 'java'])
        lang_layout.addWidget(self.output_language)

        lang_info = InfoButton(self.tooltips['language'])
        lang_layout.addWidget(lang_info, 0, Qt.AlignVCenter)
        lang_layout.addStretch()

        output_layout.addLayout(lang_layout, row, 1)
        row += 1

        # Class Name
        output_layout.addWidget(QLabel("Class Name"), row, 0, Qt.AlignTop)
        class_layout = QHBoxLayout()
        class_layout.setSpacing(8)

        self.class_name = QLineEdit()
        self.class_name.setText("MyFilter")
        self.class_name.setPlaceholderText("e.g., NotchFilter")
        class_layout.addWidget(self.class_name)

        class_info = InfoButton(self.tooltips['class_name'])
        class_layout.addWidget(class_info, 0, Qt.AlignVCenter)
        class_layout.addStretch()

        output_layout.addLayout(class_layout, row, 1)
        row += 1

        # File Name
        output_layout.addWidget(QLabel("Output Filename"), row, 0, Qt.AlignTop)
        file_layout = QHBoxLayout()
        file_layout.setSpacing(8)

        self.file_name = QLineEdit()
        self.file_name.setText("my_filter")
        self.file_name.setPlaceholderText("filename (without extension)")
        file_layout.addWidget(self.file_name)

        file_info = InfoButton(self.tooltips['file_name'])
        file_layout.addWidget(file_info, 0, Qt.AlignVCenter)
        file_layout.addStretch()

        output_layout.addLayout(file_layout, row, 1)
        row += 1

        # Generate Plot checkbox
        plot_layout = QHBoxLayout()
        plot_layout.setSpacing(8)

        self.generate_plot = QCheckBox("Generate Frequency Response Plot")
        self.generate_plot.setChecked(True)
        plot_layout.addWidget(self.generate_plot)

        plot_info = InfoButton(self.tooltips['plot'])
        plot_layout.addWidget(plot_info, 0, Qt.AlignVCenter)
        plot_layout.addStretch()

        output_layout.addLayout(plot_layout, row, 0, 1, 2)

        return output_group

    def create_right_panel(self):
        """Create the right panel for code preview"""
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(20)
        right_layout.setContentsMargins(0, 16, 16, 16)

        # Preview Group
        preview_group = QGroupBox("Generated Filter Code")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setSpacing(16)
        preview_layout.setContentsMargins(20, 24, 20, 20)

        self.code_preview = QTextEdit()
        self.code_preview.setPlaceholderText("Generated filter code will appear here after generation...")
        preview_layout.addWidget(self.code_preview)

        right_layout.addWidget(preview_group)

        return right_panel

    def on_filter_type_changed(self):
        """Handle filter type changes"""
        filter_type = self.filter_type.currentText()

        # Update frequency label and tooltip based on filter type
        if filter_type in ['bandpass', 'bandstop']:
            self.freq1_label.setText("Low Cutoff Freq (Hz)")
            self.freq1_info.setToolTip(self.tooltips['freq_low'])
            self.freq2_label.show()
            self.freq2_input.show()
            self.freq2_info.show()
        else:
            if filter_type == 'lowpass':
                self.freq1_label.setText("Cutoff Frequency (Hz)")
                self.freq1_info.setToolTip(self.tooltips['critical_freq_lowpass'])
            else:  # highpass
                self.freq1_label.setText("Cutoff Frequency (Hz)")
                self.freq1_info.setToolTip(self.tooltips['critical_freq_highpass'])

            self.freq2_label.hide()
            self.freq2_input.hide()
            self.freq2_info.hide()

    def get_file_extension(self):
        """Get file extension based on selected language"""
        language = self.output_language.currentText().lower()
        extensions = {
            'python': '.py',
            'javascript': '.js',
            'typescript': '.ts',
            'c++': '.cpp',
            'java': '.java'
        }
        return extensions.get(language, '.py')

    def build_command(self):
        """Build the command for filter_gen.py"""
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'filter_gen.py')
        cmd_parts = [sys.executable, script_path,
            '--type', self.filter_type.currentText(),
            '--rate', str(self.sampling_rate.value()),
            '--order', str(self.filter_order.value())]

        if self.filter_type.currentText() in ['bandpass', 'bandstop']:
            cmd_parts += ['--freqs', str(self.freq1_input.value()), str(self.freq2_input.value())]
        else:
            cmd_parts += ['--freqs', str(self.freq1_input.value())]

        if self.class_name.text().strip():
            cmd_parts += ['--name', self.class_name.text().strip()]

        language = self.output_language.currentText().lower()
        cmd_parts += ['--language', language]

        filename = self.file_name.text().strip()
        if filename:
            base, ext = os.path.splitext(filename)
            out_path = filename if ext else base + self.get_file_extension()
            self._out_path = out_path
            cmd_parts += ['--out', out_path]
        else:
            self._out_path = None

        if self.generate_plot.isChecked():
            plot_filename = filename if filename else self.filter_type.currentText()
            cmd_parts += ['--plot', f'{plot_filename}_response.png']

        return cmd_parts

    def generate_filter(self):
        """Generate the filter"""
        # Validate inputs against Nyquist
        nyquist = self.sampling_rate.value() / 2.0
        filter_type = self.filter_type.currentText()
        f1 = self.freq1_input.value()
        f2 = self.freq2_input.value()

        if f1 >= nyquist:
            QMessageBox.critical(self, "Invalid Frequency", f"Cutoff frequency ({f1} Hz) must be strictly less than the Nyquist frequency ({nyquist:.1f} Hz).")
            return

        if filter_type in ['bandpass', 'bandstop']:
            if f2 >= nyquist:
                QMessageBox.critical(self, "Invalid Frequency", f"High cutoff frequency ({f2} Hz) must be strictly less than the Nyquist frequency ({nyquist:.1f} Hz).")
                return
            if f1 >= f2:
                QMessageBox.critical(self, "Invalid Range", f"Low cutoff frequency ({f1} Hz) must be strictly less than High cutoff frequency ({f2} Hz).")
                return

        self.generate_button.setEnabled(False)
        self.generate_button.setText("Generating...")
        self.status_text.clear()
        self.status_text.append("Generating filter...")

        command = self.build_command()

        # Create and start the worker thread
        self.worker_thread = FilterThread(command)
        self.worker_thread.finished.connect(self.on_generation_finished)
        self.worker_thread.error.connect(self.on_generation_error)
        self.worker_thread.start()

    def on_generation_finished(self, message):
        """Handle successful generation"""
        self.generate_button.setEnabled(True)
        self.generate_button.setText("Generate Filter")
        self.status_text.append(f"✓ {message}")

        # Try to load and display the generated code
        if hasattr(self, '_out_path') and self._out_path:
            try:
                with open(self._out_path, 'r') as f:
                    code = f.read()
                self.code_preview.setText(code)
                self.status_text.append(f"Generated file: {self._out_path}")
            except FileNotFoundError:
                self.status_text.append("Warning: Generated file not found for preview")
            except Exception as e:
                self.status_text.append(f"Warning: Error reading generated file: {str(e)}")

        # Check if plot was generated
        if self.generate_plot.isChecked():
            filename = self.file_name.text().strip()
            plot_filename = filename if filename else self.filter_type.currentText()
            plot_path = f"{plot_filename}_response.png"
            if os.path.exists(plot_path):
                self.status_text.append(f"Generated plot: {plot_path}")

    def on_generation_error(self, error_message):
        """Handle generation errors"""
        self.generate_button.setEnabled(True)
        self.generate_button.setText("Generate Filter")
        self.status_text.append(f"✗ {error_message}")
        QMessageBox.critical(self, "Error", error_message)

def main():
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("Digital Filter Designer")
    app.setApplicationVersion("2.0")
    app.setApplicationDisplayName("Digital Filter Designer")

    # Create and show the GUI
    gui = ModernFilterGUI()
    gui.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
