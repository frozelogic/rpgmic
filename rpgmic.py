import sys
import os
import struct
import zlib
import io
import time
from PIL import Image
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox,
    QProgressBar,
    QTextEdit,
    QStyle,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QRect
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class ConversionThread(QThread):
    progress_update = pyqtSignal(int, int, float, float)
    conversion_finished = pyqtSignal(list, list)
    error_occurred = pyqtSignal(str)

    def __init__(self, conversion_type, input_paths, output_path):
        super().__init__()
        self.conversion_type = conversion_type
        self.input_paths = input_paths
        self.output_path = output_path
        self.is_folder = isinstance(input_paths, str) and os.path.isdir(input_paths)

    def run(self):
        try:
            if self.is_folder:
                if self.conversion_type == "xyz2png":
                    converted, errors = self.process_folder_xyz2png(
                        self.input_paths, self.output_path
                    )
                elif self.conversion_type == "png2xyz":
                    converted, errors = self.process_folder_png2xyz(
                        self.input_paths, self.output_path
                    )
                elif self.conversion_type == "to256colors":
                    converted, errors = self.process_folder_to256colors(
                        self.input_paths, self.output_path
                    )
                self.conversion_finished.emit(converted, errors)
            else:
                converted_files = []
                error_messages = []
                total_files = len(self.input_paths)
                processed_files = 0
                start_time = time.time()

                for input_path in self.input_paths:
                    if self.conversion_type == "xyz2png":
                        output_filename = (
                            os.path.splitext(os.path.basename(input_path))[0] + ".png"
                        )
                        output_path = os.path.join(self.output_path, output_filename)
                        success, message = self.convert_xyz_to_png(
                            input_path, output_path
                        )
                    elif self.conversion_type == "png2xyz":
                        output_filename = (
                            os.path.splitext(os.path.basename(input_path))[0] + ".xyz"
                        )
                        output_path = os.path.join(self.output_path, output_filename)
                        success, message = self.convert_png_to_xyz(
                            input_path, output_path
                        )
                    elif self.conversion_type == "to256colors":
                        output_filename = os.path.basename(input_path)
                        output_path = os.path.join(self.output_path, output_filename)
                        success, message = self.convert_to_8bit(input_path, output_path)

                    if success:
                        converted_files.append(output_path)
                    else:
                        error_messages.append(
                            f"Error in {os.path.basename(input_path)}: {message}"
                        )

                    processed_files += 1
                    elapsed_time = time.time() - start_time
                    if processed_files > 0:
                        time_per_file = elapsed_time / processed_files
                        remaining_files = total_files - processed_files
                        remaining_time = time_per_file * remaining_files
                    else:
                        remaining_time = 0

                    self.progress_update.emit(
                        processed_files,
                        total_files,
                        processed_files / total_files,
                        remaining_time,
                    )

                self.conversion_finished.emit(converted_files, error_messages)
        except Exception as e:
            self.error_occurred.emit(str(e))

    def process_folder_xyz2png(self, folder_path, output_root):
        converted_files = []
        error_messages = []
        parent_folder_name = os.path.basename(os.path.normpath(folder_path))
        total_files = 0
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(".xyz"):
                    total_files += 1
        processed_files = 0
        start_time = time.time()
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(".xyz"):
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, start=folder_path)
                    relative_dir = os.path.dirname(relative_path)
                    output_dir = os.path.join(
                        output_root, parent_folder_name, relative_dir
                    )
                    output_path = os.path.join(
                        output_dir, os.path.splitext(file)[0] + ".png"
                    )
                    success, message = self.convert_xyz_to_png(full_path, output_path)
                    if success:
                        converted_files.append(output_path)
                    else:
                        error_messages.append(f"Error in {relative_path}: {message}")
                    processed_files += 1
                    elapsed_time = time.time() - start_time
                    if processed_files > 0:
                        time_per_file = elapsed_time / processed_files
                        remaining_files = total_files - processed_files
                        remaining_time = time_per_file * remaining_files
                    else:
                        remaining_time = 0
                    self.progress_update.emit(
                        processed_files,
                        total_files,
                        processed_files / total_files,
                        remaining_time,
                    )
        return converted_files, error_messages

    def process_folder_png2xyz(self, folder_path, output_root):
        converted_files = []
        error_messages = []
        parent_folder_name = os.path.basename(os.path.normpath(folder_path))
        total_files = 0
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(".png"):
                    total_files += 1
        processed_files = 0
        start_time = time.time()
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(".png"):
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, start=folder_path)
                    relative_dir = os.path.dirname(relative_path)
                    output_dir = os.path.join(
                        output_root, parent_folder_name, relative_dir
                    )
                    output_path = os.path.join(
                        output_dir, os.path.splitext(file)[0] + ".xyz"
                    )
                    success, message = self.convert_png_to_xyz(full_path, output_path)
                    if success:
                        converted_files.append(output_path)
                    else:
                        error_messages.append(f"Error in {relative_path}: {message}")
                    processed_files += 1
                    elapsed_time = time.time() - start_time
                    if processed_files > 0:
                        time_per_file = elapsed_time / processed_files
                        remaining_files = total_files - processed_files
                        remaining_time = time_per_file * remaining_files
                    else:
                        remaining_time = 0
                    self.progress_update.emit(
                        processed_files,
                        total_files,
                        processed_files / total_files,
                        remaining_time,
                    )
        return converted_files, error_messages

    def process_folder_to256colors(self, folder_path, output_root):
        converted_files = []
        error_messages = []
        parent_folder_name = os.path.basename(os.path.normpath(folder_path))
        total_files = 0
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(".png"):
                    total_files += 1
        processed_files = 0
        start_time = time.time()
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(".png"):
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, start=folder_path)
                    relative_dir = os.path.dirname(relative_path)
                    output_dir = os.path.join(
                        output_root, parent_folder_name, relative_dir
                    )
                    output_filename = file
                    output_path = os.path.join(output_dir, output_filename)
                    success, message = self.convert_to_8bit(full_path, output_path)
                    if success:
                        converted_files.append(output_path)
                    else:
                        error_messages.append(f"Error in {relative_path}: {message}")
                    processed_files += 1
                    elapsed_time = time.time() - start_time
                    if processed_files > 0:
                        time_per_file = elapsed_time / processed_files
                        remaining_files = total_files - processed_files
                        remaining_time = time_per_file * remaining_files
                    else:
                        remaining_time = 0
                    self.progress_update.emit(
                        processed_files,
                        total_files,
                        processed_files / total_files,
                        remaining_time,
                    )
        return converted_files, error_messages

    def convert_xyz_to_png(self, input_path, output_path):
        try:
            with open(input_path, "rb") as input_fh:
                magic = input_fh.read(4)
                if magic != b"XYZ1":
                    return False, f"Unsupported file format: {magic}"
                width, height = struct.unpack("=HH", input_fh.read(4))
                rest = input_fh.read()
                rest = zlib.decompress(rest)
                rest = io.BytesIO(rest)
                palette = []
                for x in range(256):
                    r, g, b = struct.unpack("=3B", rest.read(3))
                    palette.append((r, g, b))
                output_image = Image.new("RGBA", (width, height))
                output_pixels = output_image.load()
                for y in range(height):
                    for x in range(width):
                        output_pixels[x, y] = palette[ord(rest.read(1))]
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                output_image.save(output_path)
                return True, None
        except Exception as e:
            return False, str(e)

    def convert_png_to_xyz(self, input_path, output_path):
        try:
            with Image.open(input_path) as img:
                if img.mode != "RGBA":
                    img = img.convert("RGBA")
                width, height = img.size
                pixels = img.load()
                palette = {}
                palette_index = 0
                palette_list = []
                color_to_index = {}
                for y in range(height):
                    for x in range(width):
                        color = pixels[x, y][:3]
                        if color not in color_to_index:
                            if len(palette_list) >= 256:
                                return False, "Image has more than 256 colors"
                            color_to_index[color] = palette_index
                            palette_list.append(color)
                            palette_index += 1
                while len(palette_list) < 256:
                    palette_list.append((0, 0, 0))
                output_data = io.BytesIO()
                output_data.write(b"XYZ1")
                output_data.write(struct.pack("=HH", width, height))
                for color in palette_list:
                    output_data.write(struct.pack("=3B", *color))
                for y in range(height):
                    for x in range(width):
                        color = pixels[x, y][:3]
                        output_data.write(bytes([color_to_index[color]]))
                compressed_data = zlib.compress(output_data.getvalue()[8:])
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(b"XYZ1")
                    f.write(struct.pack("=HH", width, height))
                    f.write(compressed_data)
                return True, None
        except Exception as e:
            return False, str(e)

    def convert_to_8bit(self, input_path, output_path):
        try:
            img = Image.open(input_path).convert(
                "P", palette=Image.ADAPTIVE, colors=256
            )
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            img.save(output_path)
            return True, None
        except Exception as e:
            return False, str(e)


class RPGMakerConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        self.initUI()
        self.conversion_thread = None
        self.current_output_dir = ""
        self.drag_start_position = None
        self.is_maximized = False
        self.normal_geometry = QRect()
        self.set_application_icon()

    def set_application_icon(self):
        try:
            icon_path = resource_path("icon.ico")
            app_icon = QIcon(icon_path)
            self.setWindowIcon(app_icon)
            QApplication.setWindowIcon(app_icon)
        except Exception:
            self.setWindowIcon(
                self.style().standardIcon(getattr(QStyle, "SP_DesktopIcon"))
            )

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowTitle("RPG Maker Image Converter")
        self.setFixedSize(800, 600)
        self.center()

        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(45, 45, 48))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.AlternateBase, QColor(45, 45, 48))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(45, 45, 48))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Highlight, QColor(0, 122, 204))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(dark_palette)

        font = QFont("Segoe UI", 10)
        self.setFont(font)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(30, 40, 30, 30)

        header_layout = QHBoxLayout()

        author_label = QLabel("frozelogic")
        author_font = QFont("Segoe UI", 9)
        author_label.setFont(author_font)
        author_label.setStyleSheet("color: #A0A0A0;")
        header_layout.addWidget(author_label)

        header_layout.addStretch()

        self.minimize_btn = QPushButton("−")
        self.minimize_btn.setFixedSize(30, 30)
        self.minimize_btn.setStyleSheet(
            """
            QPushButton {
                background: #5A5A5A;
                color: white;
                border: none;
                border-radius: 15px;
                font-weight: bold;
                font-size: 16px;
                padding-top: -2px;
            }
            QPushButton:hover {
                background: #6A6A6A;
            }
            QPushButton:pressed {
                background: #4A4A4A;
            }
        """
        )
        self.minimize_btn.clicked.connect(self.showMinimized)
        header_layout.addWidget(self.minimize_btn)

        self.maximize_btn = QPushButton("🗖")
        self.maximize_btn.setFixedSize(30, 30)
        self.maximize_btn.setStyleSheet(
            """
            QPushButton {
                background: #5A5A5A;
                color: white;
                border: none;
                border-radius: 15px;
                font-weight: bold;
                font-size: 16px;
                padding-top: -2px;
            }
            QPushButton:hover {
                background: #6A6A6A;
            }
            QPushButton:pressed {
                background: #4A4A4A;
            }
        """
        )
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        header_layout.addWidget(self.maximize_btn)

        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setStyleSheet(
            """
            QPushButton {
                background: #5A5A5A;
                color: white;
                border: none;
                border-radius: 15px;
                font-weight: bold;
                font-size: 16px;
                padding-top: -2px;
            }
            QPushButton:hover {
                background: #FF5555;
            }
            QPushButton:pressed {
                background: #FF3333;
            }
        """
        )
        self.close_btn.clicked.connect(self.close)
        header_layout.addWidget(self.close_btn)

        main_layout.addLayout(header_layout)

        title_label = QLabel("RPG Maker Image Converter")
        title_font = QFont("Segoe UI", 24, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #E1E1E1; margin: 20px 0 10px 0;")
        main_layout.addWidget(title_label)

        description_label = QLabel(
            "Tool for converting images between PNG and XYZ formats\n"
            "compatible with RPG Maker 2000 and 2003. Preserves the folder\n"
            "structure and converts images to the required 256-color format."
        )
        description_font = QFont("Segoe UI", 10)
        description_label.setFont(description_font)
        description_label.setAlignment(Qt.AlignCenter)
        description_label.setStyleSheet("color: #C0C0C0; margin-bottom: 10px;")
        description_label.setWordWrap(True)
        main_layout.addWidget(description_label)

        info_label = QLabel(
            "Click 'Cancel' in the file selection dialog to switch to folder selection mode"
        )
        info_font = QFont("Segoe UI", 9)
        info_label.setFont(info_font)
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: #808080; margin-bottom: 20px;")
        info_label.setWordWrap(True)
        main_layout.addWidget(info_label)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)

        self.xyz2png_btn = QPushButton("XYZ to PNG")
        self.xyz2png_btn.setMinimumSize(200, 45)
        self.xyz2png_btn.setStyleSheet(self.get_button_style())
        self.xyz2png_btn.clicked.connect(lambda: self.start_conversion("xyz2png"))
        buttons_layout.addWidget(self.xyz2png_btn)

        self.to256colors_btn = QPushButton("To 256 Colors")
        self.to256colors_btn.setMinimumSize(200, 45)
        self.to256colors_btn.setStyleSheet(self.get_button_style())
        self.to256colors_btn.clicked.connect(
            lambda: self.start_conversion("to256colors")
        )
        buttons_layout.addWidget(self.to256colors_btn)

        self.png2xyz_btn = QPushButton("PNG to XYZ")
        self.png2xyz_btn.setMinimumSize(200, 45)
        self.png2xyz_btn.setStyleSheet(self.get_button_style())
        self.png2xyz_btn.clicked.connect(lambda: self.start_conversion("png2xyz"))
        buttons_layout.addWidget(self.png2xyz_btn)

        main_layout.addLayout(buttons_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(
            """
            QProgressBar {
                border: 2px solid #3A3A3A;
                border-radius: 0px;
                text-align: center;
                background: #2D2D2D;
                height: 20px;
                color: white;
            }
            QProgressBar::chunk {
                background: #007ACC;
                border-radius: 0px;
            }
        """
        )
        self.progress_bar.setFormat("%v/%m files")
        main_layout.addWidget(self.progress_bar)

        status_label = QLabel("Status:")
        status_label.setStyleSheet("color: #E1E1E1; margin-top: 20px;")
        main_layout.addWidget(status_label)

        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(150)
        self.status_text.setStyleSheet(
            """
            QTextEdit {
                background: #2D2D2D;
                border: 1px solid #3A3A3A;
                border-radius: 5px;
                color: #E1E1E1;
                padding: 5px;
            }
        """
        )
        main_layout.addWidget(self.status_text)

    def get_button_style(self):
        return """
            QPushButton {
                background: #5A5A5A;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
                padding: 8px;
            }
            QPushButton:hover {
                background: #6A6A6A;
            }
            QPushButton:pressed {
                background: #4A4A4A;
            }
            QPushButton:disabled {
                background: #404040;
                color: #A0A0A0;
            }
        """

    def center(self):
        frame_geometry = self.frameGeometry()
        center_point = QApplication.primaryScreen().availableGeometry().center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = (
                event.globalPos() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_start_position is not None:
            self.move(event.globalPos() - self.drag_start_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = None
            event.accept()

    def toggle_maximize(self):
        if self.is_maximized:
            self.showNormal()
            self.is_maximized = False
        else:
            self.normal_geometry = self.geometry()
            self.showMaximized()
            self.is_maximized = True

    def start_conversion(self, conversion_type):
        if conversion_type == "xyz2png":
            file_types = "XYZ Files (*.xyz);;All Files (*)"
            title = "Select XYZ file(s)"
            default_output = os.path.join(
                os.path.expanduser("~"), "Downloads", "XYZ2PNG_Output"
            )
        elif conversion_type == "png2xyz":
            file_types = "PNG Files (*.png);;All Files (*)"
            title = "Select PNG file(s)"
            default_output = os.path.join(
                os.path.expanduser("~"), "Downloads", "PNG2XYZ_Output"
            )
        else:
            file_types = "PNG Files (*.png);;All Files (*)"
            title = "Select PNG file(s)"
            default_output = os.path.join(
                os.path.expanduser("~"), "Downloads", "256COLORS_Output"
            )

        options = QFileDialog.Options()
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, title, "", file_types, options=options
        )

        folder_path = ""
        if not file_paths:
            folder_path = QFileDialog.getExistingDirectory(
                self, "Select folder", options=options
            )

        if not file_paths and not folder_path:
            return

        if file_paths:
            input_path = file_paths
            is_folder = False
            os.makedirs(default_output, exist_ok=True)
        else:
            input_path = folder_path
            is_folder = True

        self.current_output_dir = default_output
        self.set_buttons_enabled(False)

        self.conversion_thread = ConversionThread(
            conversion_type, input_path, default_output
        )
        self.conversion_thread.progress_update.connect(self.update_progress)
        self.conversion_thread.conversion_finished.connect(self.conversion_complete)
        self.conversion_thread.error_occurred.connect(self.conversion_error)
        self.conversion_thread.start()

        self.progress_bar.setVisible(True)
        self.status_text.append("Starting conversion...")

    def update_progress(self, current, total, progress, remaining_time):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_bar.setFormat(f"{current}/{total} files")
        mins, secs = divmod(int(remaining_time), 60)
        time_estimate = f"{mins:02d}:{secs:02d}" if remaining_time > 0 else "--:--"
        self.status_text.append(
            f"Processed {current}/{total} files - ETA: {time_estimate}"
        )
        self.status_text.verticalScrollBar().setValue(
            self.status_text.verticalScrollBar().maximum()
        )

    def conversion_complete(self, converted_files, error_messages):
        self.set_buttons_enabled(True)
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")
        summary = f"Conversion complete!\n\nConverted {len(converted_files)} files."
        if error_messages:
            summary += f"\n\nEncountered {len(error_messages)} errors:"
            for error in error_messages[:5]:
                summary += f"\n• {error}"
            if len(error_messages) > 5:
                summary += f"\n• ... and {len(error_messages) - 5} more errors"
        summary += f"\n\nFiles saved to: {self.current_output_dir}"
        self.status_text.append(summary)
        self.status_text.verticalScrollBar().setValue(
            self.status_text.verticalScrollBar().maximum()
        )

    def conversion_error(self, error_message):
        self.set_buttons_enabled(True)
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")
        self.status_text.append(f"Error: {error_message}")
        self.status_text.verticalScrollBar().setValue(
            self.status_text.verticalScrollBar().maximum()
        )
        QMessageBox.critical(
            self, "Conversion Error", f"An error occurred: {error_message}"
        )

    def set_buttons_enabled(self, enabled):
        self.xyz2png_btn.setEnabled(enabled)
        self.to256colors_btn.setEnabled(enabled)
        self.png2xyz_btn.setEnabled(enabled)


def main():
    import ctypes

    myappid = "frozelogic.rpgmic.converter.0.0.0"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    try:
        icon_path = resource_path("icon.ico")
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)
    except Exception:
        pass
    converter = RPGMakerConverter()
    converter.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
