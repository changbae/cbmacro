import sys
import cv2
import numpy as np
import json
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget, QFileDialog, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal
import pyautogui


class MacroThread(QThread):
    update_log = pyqtSignal(str)

    def __init__(self, image_action_map):
        super().__init__()
        self.image_action_map = image_action_map
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            for entry in self.image_action_map:
                main_image = entry['main_image']
                sub_image = entry.get('sub_image')
                action = entry.get('action')

                if self.find_image(main_image):
                    self.update_log.emit(f"Main image found: {main_image}")
                    if sub_image and self.find_image(sub_image):
                        self.update_log.emit(f"Sub image found: {sub_image}, performing action: {action}")
                        # 여기에 실제 작업을 구현
                    elif not sub_image:
                        self.update_log.emit(f"Performing action: {action}")
                        # 여기에 실제 작업을 구현
                    
            self.msleep(1000)  # 1초 대기 후 반복 체크 (조정 가능)

    def stop(self):
        self.running = False

    def find_image(self, template_path, threshold=0.8):
        screen = cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_BGR2GRAY)
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            return False
        res = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        return loc[0].size > 0


class MacroApp(QWidget):
    def __init__(self):
        super().__init__()
        self.image_action_map = self.load_settings()
        self.macro_thread = MacroThread(self.image_action_map)
        self.macro_thread.update_log.connect(self.log_message)

        # UI 초기화
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.start_button = QPushButton('Start', self)
        self.start_button.clicked.connect(self.start_macro)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton('Stop', self)
        self.stop_button.clicked.connect(self.stop_macro)
        layout.addWidget(self.stop_button)

        self.list_widget = QListWidget(self)
        layout.addWidget(self.list_widget)

        self.update_list()

        add_button = QPushButton('Add Image & Action', self)
        add_button.clicked.connect(self.add_entry)
        layout.addWidget(add_button)

        remove_button = QPushButton('Remove Selected Entry', self)
        remove_button.clicked.connect(self.remove_entry)
        layout.addWidget(remove_button)

        self.setLayout(layout)
        self.setWindowTitle('Image Macro')
        self.show()

    def load_settings(self):
        try:
            with open('settings.json', 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_settings(self):
        with open('settings.json', 'w') as f:
            json.dump(self.image_action_map, f, indent=4)

    def log_message(self, message):
        QMessageBox.information(self, "Log", message)

    def start_macro(self):
        if not self.macro_thread.isRunning():
            self.macro_thread.start()

    def stop_macro(self):
        self.macro_thread.stop()

    def add_entry(self):
        main_image_path, _ = QFileDialog.getOpenFileName(self, "Select Main Image", "", "Image Files (*.png *.jpg *.jpeg)")
        if not main_image_path:
            return

        sub_image_path, _ = QFileDialog.getOpenFileName(self, "Select Sub Image", "", "Image Files (*.png *.jpg *.jpeg)")
        action, ok = QFileDialog.getText(self, 'Input Action', 'Enter action description:')
        
        if ok:
            entry = {"main_image": main_image_path, "sub_image": sub_image_path, "action": action}
            self.image_action_map.append(entry)
            self.save_settings()
            self.update_list()

    def remove_entry(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            row = self.list_widget.row(item)
            del self.image_action_map[row]
            self.list_widget.takeItem(row)

        self.save_settings()

    def update_list(self):
        self.list_widget.clear()
        for entry in self.image_action_map:
            main_image = entry['main_image']
            sub_image = entry.get('sub_image', 'None')
            action = entry.get('action', 'No Action')
            self.list_widget.addItem(f"Main: {main_image}, Sub: {sub_image}, Action: {action}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MacroApp()
    sys.exit(app.exec_())