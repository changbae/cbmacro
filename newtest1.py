import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import cv2
import numpy as np
import telegram
import json
import time
from datetime import datetime
import logging
import argparse
import asyncio  # 추가된 부분


def setup_logging(log_level):
    logger = logging.getLogger('CBMacro')
    logger.setLevel(log_level)

    file_handler = logging.FileHandler('cbmacro.log')
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

class CaptureThread(QThread):
    captured = pyqtSignal(np.ndarray)
    
    def __init__(self, logger):
        super().__init__()
        self.running = False
        self.logger = logger
        
    def run(self):
        self.logger.info("캡처 스레드 시작")
        while self.running:
            try:
                screen = QScreen.grabWindow(QApplication.primaryScreen(), 0)
                image = screen.toImage()
                
                width = image.width()
                height = image.height()
                ptr = image.bits()
                ptr.setsize(image.byteCount())
                arr = np.array(ptr).reshape(height, width, 4)
                arr_bgr = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
                
                self.captured.emit(arr_bgr)
                time.sleep(5)
            except Exception as e:
                self.logger.error(f"캡처 중 오류 발생: {str(e)}")
            
    def stop(self):
        self.running = False
        self.logger.info("캡처 스레드 정지")

class MainWindow(QMainWindow):
    def __init__(self, logger):
        super().__init__()
        self.logger = logger
        self.target_image = None
        self.initUI()
        self.capture_thread = CaptureThread(logger)
        self.capture_thread.captured.connect(self.processImage)
        self.loadSettings()

    def initUI(self):
        self.setWindowTitle('화면 캡처 & 이미지 검색')
        self.setGeometry(100, 100, 400, 350)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # === 설정 그룹 ===
        settings_group = QGroupBox('설정')
        settings_layout = QGridLayout()
        settings_layout.setSpacing(5)

        # 이미지 선택 UI
        self.image_path = QLineEdit()
        self.image_path.setMaximumHeight(25)
        browse_btn = QPushButton('찾기', self)
        browse_btn.setMaximumWidth(50)
        browse_btn.clicked.connect(self.browseImage)
        settings_layout.addWidget(QLabel('이미지:'), 0, 0)
        settings_layout.addWidget(self.image_path, 0, 1)
        settings_layout.addWidget(browse_btn, 0, 2)

        # 텔레그램 설정 UI
        self.telegram_token = QLineEdit()
        self.telegram_token.setMaximumHeight(25)
        self.telegram_chat_id = QLineEdit()
        self.telegram_chat_id.setMaximumHeight(25)
        settings_layout.addWidget(QLabel('토큰:'), 1, 0)
        settings_layout.addWidget(self.telegram_token, 1, 1, 1, 2)
        settings_layout.addWidget(QLabel('채팅ID:'), 2, 0)
        settings_layout.addWidget(self.telegram_chat_id, 2, 1, 1, 2)

        # 메시지 설정 UI
        self.telegram_message = QTextEdit()
        self.telegram_message.setMaximumHeight(50)
        self.telegram_message.setPlaceholderText("전송할 메시지를 입력하세요. {time}을 포함하면 발견 시각이 표시됩니다.")
        settings_layout.addWidget(QLabel('메시지:'), 3, 0)
        settings_layout.addWidget(self.telegram_message, 3, 1, 1, 2)

        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)

        # === 제어 버튼 ===
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        
        button_size = QSize(70, 25)
        
        self.start_btn = QPushButton('시작', self)
        self.stop_btn = QPushButton('정지', self)
        self.save_btn = QPushButton('저장', self)
        self.load_btn = QPushButton('불러오기', self)

        for btn in [self.start_btn, self.stop_btn, self.save_btn, self.load_btn]:
            btn.setFixedSize(button_size)

        self.start_btn.clicked.connect(self.startCapture)
        self.stop_btn.clicked.connect(self.stopCapture)
        self.save_btn.clicked.connect(self.saveSettings)
        self.load_btn.clicked.connect(self.loadSettings)

        self.stop_btn.setEnabled(False)

        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.load_btn)
        button_layout.addStretch()

        main_layout.addLayout(button_layout)

        # === 로그 표시 영역 ===
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(100)
        self.log_text.setReadOnly(True)
        main_layout.addWidget(self.log_text)

        # === 상태 표시 ===
        self.status_label = QLabel('대기 중...')
        self.status_label.setMaximumHeight(20)
        main_layout.addWidget(self.status_label)

    def updateLog(self, message):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_text.append(f"{current_time} - {message}")

    def browseImage(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            '이미지 선택',
            '',
            'Images (*.png *.jpg *.jpeg)'
        )
        if file_name:
            self.image_path.setText(file_name)
            self.logger.info(f"이미지 선택됨: {file_name}")
            self.updateLog(f"이미지 선택됨: {file_name}")

    def startCapture(self):
        try:
            if not self.telegram_token.text().strip():
                raise Exception("텔레그램 봇 토큰을 입력해주세요.")
            if not self.telegram_chat_id.text().strip():
                raise Exception("텔레그램 채팅 ID를 입력해주세요.")
            
            if not os.path.exists(self.image_path.text()):
                raise Exception("대상 이미지를 선택해주세요.")
                
            self.target_image = cv2.imread(self.image_path.text())
            if self.target_image is None:
                raise Exception("이미지 로드 실패")
                
            self.capture_thread.running = True
            self.capture_thread.start()
            self.status_label.setText('캡처 중...')
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.logger.info("캡처 시작")
            self.updateLog("캡처 시작")
            
        except Exception as e:
            QMessageBox.critical(self, '오류', f'프로그램 시작 실패: {str(e)}')
            self.logger.error(f"시작 실패: {str(e)}")
            self.updateLog(f"시작 실패: {str(e)}")

    def stopCapture(self):
        self.capture_thread.stop()
        self.capture_thread.wait()
        self.status_label.setText('중지됨')
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.logger.info("캡처 중지")
        self.updateLog("캡처 중지")

    def processImage(self, captured_image):
        try:
            result = cv2.matchTemplate(captured_image, self.target_image, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val > 0.8:
                self.logger.info(f"이미지 매칭 성공 (유사도: {max_val:.2f})")
                self.sendTelegramMessage()
                self.stopCapture()
                QMessageBox.information(self, '알림', '대상 이미지가 발견되어 프로그램이 정지되었습니다.')
                
        except Exception as e:
            self.logger.error(f"이미지 처리 오류: {str(e)}")
            self.updateLog(f"이미지 처리 오류: {str(e)}")

    def sendTelegramMessage(self):
        try:
            # 새로운 이벤트 루프 생성
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def send_message():
                bot = telegram.Bot(token=self.telegram_token.text().strip())
                message_template = self.telegram_message.toPlainText().strip()
                if not message_template:
                    message_template = '대상 이미지가 발견되었습니다! {time}'
                    
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                message = message_template.replace('{time}', current_time)
                
                await bot.send_message(
                    chat_id=self.telegram_chat_id.text().strip(),
                    text=message
                )
            
            # 비동기 함수 실행
            loop.run_until_complete(send_message())
            loop.close()
            
            self.logger.info("텔레그램 메시지 전송 성공")
            self.updateLog("텔레그램 메시지 전송됨")
                
        except Exception as e:
            self.logger.error(f"텔레그램 전송 실패: {str(e)}")
            self.updateLog(f"텔레그램 전송 실패: {str(e)}")
            self.stopCapture()
            QMessageBox.warning(self, '경고', f'텔레그램 전송 실패: {str(e)}\n프로그램이 정지되었습니다.')

    def saveSettings(self):
        settings = {
            'image_path': self.image_path.text(),
            'telegram_token': self.telegram_token.text(),
            'telegram_chat_id': self.telegram_chat_id.text(),
            'telegram_message': self.telegram_message.toPlainText()
        }
        
        try:
            with open('settings.json', 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False)
            self.logger.info("설정 저장 완료")
            self.updateLog("설정 저장됨")
        except Exception as e:
            self.logger.error(f"설정 저장 실패: {str(e)}")
            self.updateLog(f"설정 저장 실패: {str(e)}")

    def loadSettings(self):
        try:
            with open('settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
                self.image_path.setText(settings.get('image_path', ''))
                self.telegram_token.setText(settings.get('telegram_token', ''))
                self.telegram_chat_id.setText(settings.get('telegram_chat_id', ''))
                self.telegram_message.setText(settings.get('telegram_message', ''))
            self.logger.info("설정 불러오기 완료")
            self.updateLog("설정 불러옴")
        except:
            self.logger.warning("저장된 설정이 없음")
            self.updateLog("저장된 설정이 없음")

def main():
    parser = argparse.ArgumentParser(description='화면 캡처 & 이미지 검색 프로그램')
    parser.add_argument('--log', default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       help='로깅 레벨 설정')
    args = parser.parse_args()

    logger = setup_logging(args.log)

    app = QApplication(sys.argv)
    window = MainWindow(logger)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()