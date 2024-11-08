import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import pyautogui
import numpy as np
import cv2
import time
import threading
from datetime import datetime
import keyboard

class ImageActionListApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Action List Application")
        
        # 실행 제어 변수
        self.is_running = False
        self.pause_event = threading.Event()
        
        # 핫키 설정
        keyboard.on_press_key('F5', lambda _: self.start_automation())
        keyboard.on_press_key('F8', lambda _: self.stop_automation())
        
        # 기존 코드의 액션 타입 정의
        self.action_types = {
            "마우스 클릭": ["x좌표", "y좌표"],
            "마우스 더블클릭": ["x좌표", "y좌표"],
            "키보드 입력": ["입력할 텍스트"],
            "딜레이": ["대기시간(초)"],
            "텔레그램 전송": ["메시지 내용"]
        }
        
        # 데이터 저장용 딕셔너리
        self.action_data = {}
        self.image_references = {}
        
        # UI 구성
        self.create_ui()

    def create_ui(self):
        # 메인 프레임들
        self.left_frame = ttk.Frame(self.root, padding="5")
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        
        self.right_frame = ttk.Frame(self.root, padding="5")
        self.right_frame.grid(row=0, column=1, sticky="nsew")
        
        # 제어 프레임 (시작/정지 버튼용)
        self.control_frame = ttk.Frame(self.root, padding="5")
        self.control_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        # 이미지 프리뷰 레이블
        self.preview_label = ttk.Label(self.left_frame)
        self.preview_label.grid(row=0, column=0, columnspan=2)
        
        # 리스트박스들
        self.list1 = tk.Listbox(self.left_frame, width=30, height=15)
        self.list1.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.list1.bind('<<ListboxSelect>>', self.on_select_image)
        
        self.list2 = tk.Listbox(self.right_frame, width=40, height=15)
        self.list2.grid(row=0, column=0, columnspan=2, sticky="nsew")
        
        # 기존 버튼들
        ttk.Button(self.left_frame, text="이미지 추가", command=self.add_image).grid(row=2, column=0)
        ttk.Button(self.left_frame, text="이미지 삭제", command=self.remove_image).grid(row=2, column=1)
        ttk.Button(self.right_frame, text="액션 추가", command=self.add_action).grid(row=1, column=0)
        ttk.Button(self.right_frame, text="액션 삭제", command=self.remove_action).grid(row=1, column=1)
        
        # 실행 제어 버튼들
        self.start_button = ttk.Button(self.control_frame, text="시작 (F5)", command=self.start_automation)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(self.control_frame, text="정지 (F8)", command=self.stop_automation, state='disabled')
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # 상태 표시 레이블
        self.status_label = ttk.Label(self.control_frame, text="대기 중")
        self.status_label.pack(side=tk.LEFT, padx=20)

    def on_select_image(self, event):
        selection = self.list1.curselection()
        if selection:
            self.list2.delete(0, tk.END)  # 기존 액션 리스트 클리어
            selected_image = self.list1.get(selection)
            
            # 이미지 프리뷰 업데이트
            if selected_image in self.image_references:
                self.preview_label.configure(image=self.image_references[selected_image]['photo'])
            
            # 선택된 이미지의 액션 리스트 표시
            for action in self.action_data.get(selected_image, []):
                self.list2.insert(tk.END, action)

    def add_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if file_path:
            image_name = file_path.split("/")[-1]
            self.list1.insert(tk.END, image_name)
            self.action_data[image_name] = []
            
            image = Image.open(file_path)
            image.thumbnail((150, 150))
            photo = ImageTk.PhotoImage(image)
            self.image_references[image_name] = {
                'path': file_path,
                'photo': photo
            }

    def remove_image(self):
        selection = self.list1.curselection()
        if selection:
            image_name = self.list1.get(selection)
            self.list1.delete(selection)
            if image_name in self.action_data:
                del self.action_data[image_name]
            if image_name in self.image_references:
                del self.image_references[image_name]
            self.preview_label.configure(image='')
            self.list2.delete(0, tk.END)

    def add_action(self):
        selection = self.list1.curselection()
        if not selection:
            return
            
        selected_image = self.list1.get(selection)
        
        dialog = tk.Toplevel(self.root)
        dialog.title("액션 추가")
        dialog.geometry("300x400")
        
        # 액션 입력 프레임
        frame = ttk.Frame(dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 액션 타입 선택 콤보박스
        ttk.Label(frame, text="액션 타입:").pack(pady=5)
        action_type = ttk.Combobox(frame, values=list(self.action_types.keys()), state="readonly")
        action_type.pack(pady=5)
        
        # 파라미터 입력 필드를 담을 프레임
        param_frame = ttk.Frame(frame)
        param_frame.pack(pady=10, fill=tk.X)
        
        # 파라미터 입력 필드들을 저장할 딕셔너리
        param_entries = {}
        
        def update_params(*args):
            # 기존 위젯 제거
            for widget in param_frame.winfo_children():
                widget.destroy()
            
            # 선택된 액션 타입에 따른 파라미터 필드 생성
            selected_type = action_type.get()
            if selected_type in self.action_types:
                param_entries.clear()
                for param in self.action_types[selected_type]:
                    ttk.Label(param_frame, text=param).pack(pady=2)
                    entry = ttk.Entry(param_frame)
                    entry.pack(pady=2)
                    param_entries[param] = entry
        
        action_type.bind('<<ComboboxSelected>>', update_params)
        
        def add_item():
            selected_type = action_type.get()
            if not selected_type:
                return
                
            # 파라미터 값 수집
            params = []
            for param, entry in param_entries.items():
                value = entry.get()
                if not value:
                    return
                params.append(f"{param}={value}")
            
            # 액션 텍스트 생성
            action_text = f"{selected_type} - {', '.join(params)}"
            self.list2.insert(tk.END, action_text)
            self.action_data[selected_image].append(action_text)
            dialog.destroy()
        
        ttk.Button(frame, text="추가", command=add_item).pack(pady=10)

    def remove_action(self):
        selection = self.list2.curselection()
        if selection:
            action = self.list2.get(selection)
            self.list2.delete(selection)
            
            list1_selection = self.list1.curselection()
            if list1_selection:
                selected_image = self.list1.get(list1_selection)
                if action in self.action_data[selected_image]:
                    self.action_data[selected_image].remove(action)

    def start_automation(self):
        if not self.is_running:  # 이미 실행 중이 아닐 때만 실행
            self.is_running = True
            self.start_button.configure(state='disabled')
            self.stop_button.configure(state='normal')
            self.status_label.configure(text="실행 중...")
            
            # 자동화 스레드 시작
            self.automation_thread = threading.Thread(target=self.run_automation)
            self.automation_thread.daemon = True
            self.automation_thread.start()

    def stop_automation(self):
        if self.is_running:  # 실행 중일 때만 중지
            self.is_running = False
            self.start_button.configure(state='normal')
            self.stop_button.configure(state='disabled')
            self.status_label.configure(text="중지됨")

    def run_automation(self):
        while self.is_running:
            # 모든 이미지에 대해 검사
            for image_name in self.image_references:
                if not self.is_running:
                    break
                
                try:
                    # 화면 캡처 및 그레이스케일 변환
                    screenshot = pyautogui.screenshot()
                    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                    screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
                    
                    # 저장된 이미지 로드 및 그레이스케일 변환
                    template = cv2.imread(self.image_references[image_name]['path'])
                    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
                    
                    # 이미지 매칭
                    result = cv2.matchTemplate(screenshot_gray, template_gray, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    
                    # 매칭 임계값 (조정 가능)
                    if max_val > 0.8:
                        # 매칭된 이미지에 대한 액션 실행
                        self.execute_actions(image_name)
                        
                except Exception as e:
                    print(f"Error during image matching: {str(e)}")
                    continue
                
            time.sleep(0.1)  # CPU 부하 감소를 위한 짧은 대기

    def execute_actions(self, image_name):
        if image_name not in self.action_data:
            return
            
        for action in self.action_data[image_name]:
            if not self.is_running:
                break
                
            # 액션 파싱aaaaaaaaaaaaaaaaaaaa
            action_type = action.split(" - ")[0]
            params = dict(param.split("=") for param in action.split(" - ")[1].split(", "))
            
            # 액션 실행
            if action_type == "마우스 클릭":
                pyautogui.click(int(params["x좌표"]), int(params["y좌표"]))
            
            elif action_type == "마우스 더블클릭":
                pyautogui.doubleClick(int(params["x좌표"]), int(params["y좌표"]))
            
            elif action_type == "키보드 입력":
                pyautogui.write(params["입력할 텍스트"])
            
            elif action_type == "딜레이":
                time.sleep(float(params["대기시간(초)"]))
            
            elif action_type == "텔레그램 전송":
                # 텔레그램 전송 로직 구현 필요
                print(f"텔레그램 메시지 전송: {params['메시지 내용']}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageActionListApp(root)
    root.mainloop()