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
import json
import os
import requests

class ImageActionListApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Action List Application")
        
        # 텔레그램 설정 저장
        self.telegram_settings = {
            'app_key': '',
            'chat_id': ''
        }
        self.load_telegram_settings()  # 설정 로드

        # 실행 제어 변수
        self.is_running = False
        self.pause_event = threading.Event()
        
        # 핫키 설정
        keyboard.on_press_key('F5', lambda _: self.start_automation())
        keyboard.on_press_key('F8', lambda _: self.stop_automation())
        
        # 액션 타입 정의
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
        
        # 이미지 프리뷰 프레임 (고정 크기)
        preview_frame = ttk.Frame(self.left_frame, width=200, height=200)
        preview_frame.grid(row=0, column=0, columnspan=2, pady=5)
        preview_frame.grid_propagate(False)  # 크기 고정
        
        # 이미지 프리뷰 레이블
        self.preview_label = ttk.Label(preview_frame)
        self.preview_label.place(relx=0.5, rely=0.5, anchor='center')  # 중앙 정렬
        
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
        
        # 상태 표시 레이블들
        self.status_frame = ttk.Frame(self.control_frame)
        self.status_frame.pack(side=tk.LEFT, padx=20)
        
        self.status_label = ttk.Label(self.status_frame, text="대기 중")
        self.status_label.pack(side=tk.TOP)
        
        self.current_image_label = ttk.Label(self.status_frame, text="검색 이미지: 없음")
        self.current_image_label.pack(side=tk.TOP)

        # 텔레그램 설정 버튼 추가
        ttk.Button(self.control_frame, text="텔레그램 설정", 
                  command=self.show_telegram_settings).pack(side=tk.LEFT, padx=5)

    def show_telegram_settings(self):
        # 텔레그램 설정 창 생성
        settings_window = tk.Toplevel(self.root)
        settings_window.title("텔레그램 설정")
        settings_window.geometry("400x200")
        settings_window.transient(self.root)  # 부모 창에 종속
        settings_window.grab_set()  # 모달 창으로 설정

        # 설정 프레임
        frame = ttk.Frame(settings_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # APP Key 입력
        ttk.Label(frame, text="APP Key:").grid(row=0, column=0, sticky='e', pady=5)
        app_key_var = tk.StringVar(value=self.telegram_settings['app_key'])
        app_key_entry = ttk.Entry(frame, textvariable=app_key_var, width=40)
        app_key_entry.grid(row=0, column=1, padx=5, pady=5)

        # Chat ID 입력
        ttk.Label(frame, text="Chat ID:").grid(row=1, column=0, sticky='e', pady=5)
        chat_id_var = tk.StringVar(value=self.telegram_settings['chat_id'])
        chat_id_entry = ttk.Entry(frame, textvariable=chat_id_var, width=40)
        chat_id_entry.grid(row=1, column=1, padx=5, pady=5)

        # 테스트 메시지 입력
        ttk.Label(frame, text="테스트 메시지:").grid(row=2, column=0, sticky='e', pady=5)
        test_msg_var = tk.StringVar(value="테스트 메시지입니다.")
        test_msg_entry = ttk.Entry(frame, textvariable=test_msg_var, width=40)
        test_msg_entry.grid(row=2, column=1, padx=5, pady=5)

        def save_settings():
            self.telegram_settings['app_key'] = app_key_var.get()
            self.telegram_settings['chat_id'] = chat_id_var.get()
            self.save_telegram_settings()
            settings_window.destroy()

        def test_telegram():
            app_key = app_key_var.get()
            chat_id = chat_id_var.get()
            message = test_msg_var.get()
            
            if not app_key or not chat_id:
                tk.messagebox.showerror("오류", "APP Key와 Chat ID를 모두 입력해주세요.")
                return
                
            try:
                url = f'https://api.telegram.org/bot{app_key}/sendMessage'
                data = {
                    'chat_id': chat_id,
                    'text': message,
                    'parse_mode': 'Markdown'
                }
                response = requests.post(url, data=data)
                result = response.json()
                
                if result.get('ok'):
                    tk.messagebox.showinfo("성공", "테스트 메시지가 성공적으로 전송되었습니다!")
                else:
                    tk.messagebox.showerror("오류", f"메시지 전송 실패: {result.get('description', '알 수 없는 오류')}")
            except Exception as e:
                tk.messagebox.showerror("오류", f"메시지 전송 중 오류 발생: {str(e)}")

        # 버튼 프레임
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)

        ttk.Button(btn_frame, text="테스트", command=test_telegram).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="저장", command=save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="취소", command=settings_window.destroy).pack(side=tk.LEFT, padx=5)

    def save_telegram_settings(self):
        try:
            with open('telegram_settings.json', 'w', encoding='utf-8') as f:
                json.dump(self.telegram_settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            tk.messagebox.showerror("오류", f"설정 저장 중 오류 발생: {str(e)}")

    def load_telegram_settings(self):
        try:
            if os.path.exists('telegram_settings.json'):
                with open('telegram_settings.json', 'r', encoding='utf-8') as f:
                    self.telegram_settings = json.load(f)
        except Exception as e:
            tk.messagebox.showerror("오류", f"설정 로드 중 오류 발생: {str(e)}")

    def add_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if file_path:
            image_name = file_path.split("/")[-1]
            # 번호 매기기
            next_index = self.list1.size() + 1
            self.list1.insert(tk.END, f"{next_index}. {image_name}")
            self.action_data[image_name] = []
            
            image = Image.open(file_path)
            image.thumbnail((150, 150))
            photo = ImageTk.PhotoImage(image)
            self.image_references[image_name] = {
                'path': file_path,
                'photo': photo
            }

    def disable_all_except_stop(self):
        # 왼쪽 프레임의 위젯들 비활성화
        for widget in self.left_frame.winfo_children():
            if isinstance(widget, (ttk.Button, tk.Button, tk.Listbox)):
                widget['state'] = 'disabled'
            elif isinstance(widget, ttk.Frame):  # 프레임 안의 위젯들도 처리
                for child in widget.winfo_children():
                    if isinstance(child, (ttk.Button, tk.Button, tk.Listbox)):
                        child['state'] = 'disabled'
        
        # 오른쪽 프레임의 위젯들 비활성화
        for widget in self.right_frame.winfo_children():
            if isinstance(widget, (ttk.Button, tk.Button, tk.Listbox)):
                widget['state'] = 'disabled'
        
        # 컨트롤 프레임의 모든 버튼 비활성화 (정지 버튼 제외)
        for widget in self.control_frame.winfo_children():
            if isinstance(widget, (ttk.Button, tk.Button)) and widget != self.stop_button:
                widget['state'] = 'disabled'
        
        # 시작 버튼 비활성화, 정지 버튼 활성화
        self.start_button['state'] = 'disabled'
        self.stop_button['state'] = 'normal'

    def enable_all_widgets(self):
        # 왼쪽 프레임의 위젯들 활성화
        for widget in self.left_frame.winfo_children():
            if isinstance(widget, (ttk.Button, tk.Button, tk.Listbox)):
                widget['state'] = 'normal'
            elif isinstance(widget, ttk.Frame):  # 프레임 안의 위젯들도 처리
                for child in widget.winfo_children():
                    if isinstance(child, (ttk.Button, tk.Button, tk.Listbox)):
                        child['state'] = 'normal'
        
        # 오른쪽 프레임의 위젯들 활성화
        for widget in self.right_frame.winfo_children():
            if isinstance(widget, (ttk.Button, tk.Button, tk.Listbox)):
                widget['state'] = 'normal'
        
        # 컨트롤 프레임의 모든 버튼 활성화
        for widget in self.control_frame.winfo_children():
            if isinstance(widget, (ttk.Button, tk.Button)):
                widget['state'] = 'normal'
        
        # 정지 버튼은 비활성화
        self.stop_button['state'] = 'disabled'

    def on_select_image(self, event):
        selection = self.list1.curselection()
        if selection:
            self.list2.delete(0, tk.END)  # 기존 액션 리스트 클리어
            selected_image = self.list1.get(selection)
            # 번호 제거하고 이미지 이름만 추출
            image_name = selected_image.split(". ", 1)[1]
            
            # 이미지 프리뷰 업데이트
            if image_name in self.image_references:
                self.preview_label.configure(image=self.image_references[image_name]['photo'])
            
            # 선택된 이미지의 액션 리스트 표시
            for idx, action in enumerate(self.action_data.get(image_name, []), start=1):
                self.list2.insert(tk.END, f"{idx}. {action}")

    def remove_image(self):
        selection = self.list1.curselection()
        if selection:
            selected_item = self.list1.get(selection)
            image_name = selected_item.split(". ", 1)[1]  # 번호 제거
            self.list1.delete(selection)
            
            # 남은 항목들의 번호 재정렬
            for i in range(self.list1.size()):
                item = self.list1.get(i)
                old_num, name = item.split(". ", 1)
                self.list1.delete(i)
                self.list1.insert(i, f"{i+1}. {name}")
            
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
            
        selected_item = self.list1.get(selection)
        selected_image = selected_item.split(". ", 1)[1]  # 번호 제거

        dialog = tk.Toplevel(self.root)
        dialog.title("액션 추가")
        dialog.geometry("300x450")
        
        # 액션 입력 프레임
        frame = ttk.Frame(dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # NOT 조건 체크박스
        not_var = tk.BooleanVar()
        not_check = ttk.Checkbutton(frame, text="이미지를 찾지 못했을 때의 액션", variable=not_var)
        not_check.pack(pady=5)
        
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
            
            # 액션 텍스트 생성 (NOT 조건 포함)
            action_text = f"{'NOT - ' if not_var.get() else ''}{selected_type} - {', '.join(params)}"
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

    # start_automation 메서드 수정
    def start_automation(self):
        if not self.is_running:
            self.is_running = True
            self.disable_all_except_stop()  # 모든 위젯 비활성화
            self.status_label.configure(text="실행 중...")
            
            # 자동화 스레드 시작
            self.automation_thread = threading.Thread(target=self.run_automation)
            self.automation_thread.daemon = True
            self.automation_thread.start()

    # stop_automation 메서드 수정
    def stop_automation(self):
        if self.is_running:
            self.is_running = False
            self.enable_all_widgets()  # 모든 위젯 활성화
            self.status_label.configure(text="중지됨")

    def run_automation(self):
        while self.is_running:
            # 모든 이미지에 대해 검사
            for image_name in self.image_references:
                if not self.is_running:
                    break
                
                try:
                    # 현재 검색 중인 이미지 표시
                    self.current_image_label.configure(text=f"검색 이미지: {image_name}")
                    
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
                        # 이미지를 찾았을 때의 액션 실행
                        self.execute_actions(image_name, found=True)
                    else:
                        # 이미지를 찾지 못했을 때의 액션 실행
                        self.execute_actions(image_name, found=False)
                        
                except Exception as e:
                    print(f"Error during image matching: {str(e)}")
                    continue
                
            time.sleep(0.1)  # CPU 부하 감소를 위한 짧은 대기
    
        # 자동화 종료 시 레이블 초기화
        self.current_image_label.configure(text="검색 이미지: 없음")

    def execute_actions(self, image_name, found=True):
        if image_name not in self.action_data:
            return
            
        for action in self.action_data[image_name]:
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
                if action_type == "마우스 클릭":
                    pyautogui.click(int(params["x좌표"]), int(params["y좌표"]))
                
                elif action_type == "마우스 더블클릭":
                    pyautogui.doubleClick(int(params["x좌표"]), int(params["y좌표"]))
                
                elif action_type == "키보드 입력":
                    pyautogui.write(params["입력할 텍스트"])
                
                elif action_type == "딜레이":
                    time.sleep(float(params["대기시간(초)"]))
                
                elif action_type == "텔레그램 전송":
                    try:
                        url = f'https://api.telegram.org/bot{self.telegram_settings["app_key"]}/sendMessage'
                        data = {
                            'chat_id': self.telegram_settings['chat_id'],
                            'text': params['메시지 내용'],
                            'parse_mode': 'Markdown'
                        }
                        requests.post(url, data=data)
                    except Exception as e:
                        print(f"텔레그램 메시지 전송 중 오류: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageActionListApp(root)
    root.mainloop()






