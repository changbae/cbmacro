import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import keyboard
import os
from PIL import Image
from telegram_handler import TelegramHandler
from settings_handler import SettingsHandler
from automation import AutomationHandler
from config import ACTION_TYPES, WINDOW_TITLE, PREVIEW_SIZE, LIST_WIDTH, LIST_HEIGHT, ACTION_LIST_WIDTH

class ImageActionListApp:
    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE)
        
        # 핸들러 초기화
        self.telegram_handler = TelegramHandler()
        self.automation = AutomationHandler(self.telegram_handler)
        
        # 데이터 저장용 딕셔너리
        self.action_data = {}
        self.image_references = {}
        
        # 핫키 설정
        keyboard.on_press_key('F5', lambda _: self.start_automation())
        keyboard.on_press_key('F8', lambda _: self.stop_automation())
        
        # UI 구성
        self.create_ui()
        
    def create_ui(self):
        # 메인 프레임들
        self.left_frame = ttk.Frame(self.root, padding="5")
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        
        self.right_frame = ttk.Frame(self.root, padding="5")
        self.right_frame.grid(row=0, column=1, sticky="nsew")
        
        # 제어 프레임
        self.control_frame = ttk.Frame(self.root, padding="5")
        self.control_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        # 이미지 프리뷰 프레임
        preview_frame = ttk.Frame(self.left_frame, width=PREVIEW_SIZE[0], height=PREVIEW_SIZE[1])
        preview_frame.grid(row=0, column=0, columnspan=2, pady=5)
        preview_frame.grid_propagate(False)
        
        # 이미지 프리뷰 레이블
        self.preview_label = ttk.Label(preview_frame)
        self.preview_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # 리스트박스들
        self.list1 = tk.Listbox(self.left_frame, width=LIST_WIDTH, height=LIST_HEIGHT)
        self.list1.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.list1.bind('<<ListboxSelect>>', self.on_select_image)
        
        self.list2 = tk.Listbox(self.right_frame, width=ACTION_LIST_WIDTH, height=LIST_HEIGHT)
        self.list2.grid(row=0, column=0, columnspan=2, sticky="nsew")
        
        # 버튼들
        ttk.Button(self.left_frame, text="이미지 추가", command=self.add_image).grid(row=2, column=0)
        ttk.Button(self.left_frame, text="이미지 삭제", command=self.remove_image).grid(row=2, column=1)
        ttk.Button(self.right_frame, text="액션 추가", command=self.add_action).grid(row=1, column=0)
        ttk.Button(self.right_frame, text="액션 삭제", command=self.remove_action).grid(row=1, column=1)
        
        # 제어 버튼들
        self.start_button = ttk.Button(self.control_frame, text="시작 (F5)", command=self.start_automation)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(self.control_frame, text="정지 (F8)", 
                                    command=self.stop_automation, state='disabled')
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # 설정 버튼들
        ttk.Button(self.control_frame, text="텔레그램 설정", 
                  command=lambda: self.telegram_handler.show_settings_dialog(self.root)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(self.control_frame, text="저장", 
                  command=lambda: SettingsHandler.save_settings(self.action_data, self.image_references)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(self.control_frame, text="불러오기", 
                  command=self.load_settings).pack(side=tk.LEFT, padx=5)
        
        # 상태 표시 레이블
        self.status_frame = ttk.Frame(self.control_frame)
        self.status_frame.pack(side=tk.LEFT, padx=20)
        
        self.status_label = ttk.Label(self.status_frame, text="대기 중")
        self.status_label.pack(side=tk.TOP)
        
        self.current_image_label = ttk.Label(self.status_frame, text="검색 이미지: 없음")
        self.current_image_label.pack(side=tk.TOP)

    def on_select_image(self, event):
        selection = self.list1.curselection()
        if selection:
            self.list2.delete(0, tk.END)
            selected_item = self.list1.get(selection)
            image_name = selected_item.split(". ", 1)[1]
            
            if image_name in self.image_references:
                self.preview_label.configure(image=self.image_references[image_name]['photo'])
            
            for idx, action in enumerate(self.action_data.get(image_name, []), start=1):
                self.list2.insert(tk.END, f"{idx}. {action}")

    def add_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if file_path:
            image_name = file_path.split("/")[-1]
            next_index = self.list1.size() + 1
            self.list1.insert(tk.END, f"{next_index}. {image_name}")
            self.action_data[image_name] = []
            
            image = Image.open(file_path)
            image.thumbnail(PREVIEW_SIZE)
            photo = ImageTk.PhotoImage(image)
            self.image_references[image_name] = {
                'path': file_path,
                'photo': photo
            }

    def remove_image(self):
        selection = self.list1.curselection()
        if selection:
            selected_item = self.list1.get(selection)
            image_name = selected_item.split(". ", 1)[1]
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
        selected_image = selected_item.split(". ", 1)[1]
        
        dialog = tk.Toplevel(self.root)
        dialog.title("액션 추가")
        dialog.geometry("300x450")
        
        frame = ttk.Frame(dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # NOT 조건 체크박스
        not_var = tk.BooleanVar()
        not_check = ttk.Checkbutton(frame, text="이미지를 찾지 못했을 때의 액션", variable=not_var)
        not_check.pack(pady=5)
        
        # 액션 타입 선택
        ttk.Label(frame, text="액션 타입:").pack(pady=5)
        action_type = ttk.Combobox(frame, values=list(ACTION_TYPES.keys()), state="readonly")
        action_type.pack(pady=5)
        
        # 파라미터 프레임
        param_frame = ttk.Frame(frame)
        param_frame.pack(pady=10, fill=tk.X)
        
        param_entries = {}
        
        def update_params(*args):
            for widget in param_frame.winfo_children():
                widget.destroy()
            
            selected_type = action_type.get()
            if selected_type in ACTION_TYPES:
                param_entries.clear()
                for param in ACTION_TYPES[selected_type]:
                    ttk.Label(param_frame, text=param).pack(pady=2)
                    entry = ttk.Entry(param_frame)
                    entry.pack(pady=2)
                    param_entries[param] = entry
        
        action_type.bind('<<ComboboxSelected>>', update_params)
        
        def add_item():
            selected_type = action_type.get()
            if not selected_type:
                return
                
            params = []
            for param, entry in param_entries.items():
                value = entry.get()
                if not value:
                    return
                params.append(f"{param}={value}")
            
            action_text = f"{'NOT - ' if not_var.get() else ''}{selected_type} - {', '.join(params)}"
            next_index = self.list2.size() + 1
            self.list2.insert(tk.END, f"{next_index}. {action_text}")
            self.action_data[selected_image].append(action_text)
            dialog.destroy()
        
        ttk.Button(frame, text="추가", command=add_item).pack(pady=10)

    def remove_action(self):
        selection = self.list2.curselection()
        if selection:
            action = self.list2.get(selection)
            self.list2.delete(selection)
            
            # 남은 항목들의 번호 재정렬
            for i in range(self.list2.size()):
                item = self.list2.get(i)
                old_num, text = item.split(". ", 1)
                self.list2.delete(i)
                self.list2.insert(i, f"{i+1}. {text}")
            
            list1_selection = self.list1.curselection()
            if list1_selection:
                selected_item = self.list1.get(list1_selection)
                selected_image = selected_item.split(". ", 1)[1]
                action_text = action.split(". ", 1)[1]
                if action_text in self.action_data[selected_image]:
                    self.action_data[selected_image].remove(action_text)

    def load_settings(self):
        settings = SettingsHandler.load_settings()
        if settings:
            # 기존 데이터 초기화
            self.action_data.clear()
            self.image_references.clear()
            self.list1.delete(0, tk.END)
            self.list2.delete(0, tk.END)
            self.preview_label.configure(image='')
            
            # 이미지와 액션 데이터 로드
            for image_name, image_path in settings['image_paths'].items():
                if os.path.exists(image_path):
                    image = Image.open(image_path)
                    image.thumbnail(PREVIEW_SIZE)
                    photo = ImageTk.PhotoImage(image)
                    
                    self.image_references[image_name] = {
                        'path': image_path,
                        'photo': photo
                    }
                    
                    next_index = self.list1.size() + 1
                    self.list1.insert(tk.END, f"{next_index}. {image_name}")
            
            self.action_data = settings['action_data']

    def disable_all_except_stop(self):
        for widget in self.left_frame.winfo_children():
            if isinstance(widget, (ttk.Button, tk.Button, tk.Listbox)):
                widget['state'] = 'disabled'
            elif isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, (ttk.Button, tk.Button, tk.Listbox)):
                        child['state'] = 'disabled'
        
        for widget in self.right_frame.winfo_children():
            if isinstance(widget, (ttk.Button, tk.Button, tk.Listbox)):
                widget['state'] = 'disabled'
        
        for widget in self.control_frame.winfo_children():
            if isinstance(widget, (ttk.Button, tk.Button)) and widget != self.stop_button:
                widget['state'] = 'disabled'
        
        self.stop_button['state'] = 'normal'

    def enable_all_widgets(self):
        for widget in self.left_frame.winfo_children():
            if isinstance(widget, (ttk.Button, tk.Button, tk.Listbox)):
                widget['state'] = 'normal'
            elif isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, (ttk.Button, tk.Button, tk.Listbox)):
                        child['state'] = 'normal'
        
        for widget in self.right_frame.winfo_children():
            if isinstance(widget, (ttk.Button, tk.Button, tk.Listbox)):
                widget['state'] = 'normal'
        
        for widget in self.control_frame.winfo_children():
            if isinstance(widget, (ttk.Button, tk.Button)):
                widget['state'] = 'normal'
        
        self.stop_button['state'] = 'disabled'

    def update_status(self, message):
        self.status_label.configure(text=message)

    def start_automation(self):
        if not self.automation.is_running:
            self.automation.start()
            self.disable_all_except_stop()
            self.update_status("실행 중...")
            
            automation_thread = threading.Thread(
                target=self.automation.run_automation,
                args=(self.image_references, self.action_data, self.update_status)
            )
            automation_thread.daemon = True
            automation_thread.start()

    def stop_automation(self):
        if self.automation.is_running:
            self.automation.stop()
            self.enable_all_widgets()
            self.update_status("중지됨")