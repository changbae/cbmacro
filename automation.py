import cv2
import numpy as np
import pyautogui
import time
import threading
from config import MATCHING_THRESHOLD

class AutomationHandler:
    def __init__(self, telegram_handler):
        self.is_running = False
        self.telegram_handler = telegram_handler
        self.current_image = None

    def start(self):
        self.is_running = True

    def stop(self):
        self.is_running = False

    def find_image(self, template_path):
        try:
            # 화면 캡처 및 그레이스케일 변환
            screenshot = pyautogui.screenshot()
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            
            # 저장된 이미지 로드 및 그레이스케일 변환
            template = cv2.imread(template_path)
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            
            # 이미지 매칭
            result = cv2.matchTemplate(screenshot_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            return max_val > MATCHING_THRESHOLD
        except Exception as e:
            print(f"Image matching error: {str(e)}")
            return False

    def execute_action(self, action_type, params):
        try:
            if action_type == "마우스 클릭":
                pyautogui.click(int(params["x좌표"]), int(params["y좌표"]))
            
            elif action_type == "마우스 더블클릭":
                pyautogui.doubleClick(int(params["x좌표"]), int(params["y좌표"]))
            
            elif action_type == "키보드 입력":
                pyautogui.write(params["입력할 텍스트"])
            
            elif action_type == "딜레이":
                time.sleep(float(params["대기시간(초)"]))
            
            elif action_type == "텔레그램 전송":
                self.telegram_handler.send_message(params["메시지 내용"])
            
            return True
        except Exception as e:
            print(f"Action execution error: {str(e)}")
            return False

    def run_automation(self, image_references, action_data, status_callback=None):
        while self.is_running:
            for image_name, image_data in image_references.items():
                if not self.is_running:
                    break

                self.current_image = image_name
                if status_callback:
                    status_callback(f"검색 중: {image_name}")

                try:
                    found = self.find_image(image_data['path'])
                    
                    if image_name in action_data:
                        for action in action_data[image_name]:
                            if not self.is_running:
                                break

                            # NOT 조건 확인
                            is_not_action = action.startswith("NOT - ")
                            
                            # 이미지를 찾았을 때는 일반 액션만, 못 찾았을 때는 NOT 액션만 실행
                            if (found and not is_not_action) or (not found and is_not_action):
                                # NOT 프리픽스 제거
                                action_text = action[6:] if is_not_action else action
                                
                                # 액션 파싱
                                action_type = action_text.split(" - ")[0]
                                params = dict(param.split("=") for param in action_text.split(" - ")[1].split(", "))
                                
                                # 액션 실행
                                self.execute_action(action_type, params)

                except Exception as e:
                    print(f"Automation error: {str(e)}")
                    continue

            time.sleep(0.1)  # CPU 부하 감소

        if status_callback:
            status_callback("중지됨")