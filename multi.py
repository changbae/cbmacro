import sys
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QPushButton, QWidget

class WorkerThread(QThread):
    update_progress = pyqtSignal(int)
    
    def run(self):
        for i in range(5):
            self.sleep(1)  # 1초씩 대기하면서 작업 시뮬레이션
            self.update_progress.emit(i + 1)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        # 윈도우 설정
        self.setWindowTitle("멀티스레딩 예제")
        self.setGeometry(100, 100, 300, 150)
        
        # 중앙 위젯과 레이아웃 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 레이블 생성
        self.label = QLabel("진행 상황: 0%")
        layout.addWidget(self.label)
        
        # 시작 버튼 생성
        self.start_button = QPushButton("작업 시작")
        self.start_button.clicked.connect(self.start_worker)
        layout.addWidget(self.start_button)
        
        # 스레드 초기화
        self.worker_thread = None
    
    def start_worker(self):
        # 버튼 비활성화
        self.start_button.setEnabled(False)
        
        # 새로운 작업 스레드 생성 및 시작
        self.worker_thread = WorkerThread()
        self.worker_thread.update_progress.connect(self.update_progress_label)
        self.worker_thread.finished.connect(self.on_worker_finished)
        self.worker_thread.start()
    
    def update_progress_label(self, progress):
        self.label.setText(f"진행 상황: {progress * 20}%")
    
    def on_worker_finished(self):
        # 작업이 완료되면 버튼 다시 활성화
        self.start_button.setEnabled(True)
        self.label.setText("작업 완료!")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()