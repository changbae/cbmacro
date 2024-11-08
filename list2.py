import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk

class ImageActionListApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Action List Application")
        
        # 액션 타입 정의
        self.action_types = {
            "마우스 클릭": ["x좌표", "y좌표"],
            "마우스 더블클릭": ["x좌표", "y좌표"],
            "키보드 입력": ["입력할 텍스트"],
            "딜레이": ["대기시간(초)"],
            "텔레그램 전송": ["메시지 내용"]
        }
        
        # 데이터 저장용 딕셔너리
        self.action_data = {}  # {이미지경로: [액션리스트]}
        self.image_references = {}  # 이미지 객체 참조 저장
        
        # 프레임 생성
        self.left_frame = ttk.Frame(root, padding="5")
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        
        self.right_frame = ttk.Frame(root, padding="5")
        self.right_frame.grid(row=0, column=1, sticky="nsew")
        
        # 이미지 프리뷰 레이블
        self.preview_label = ttk.Label(self.left_frame)
        self.preview_label.grid(row=0, column=0, columnspan=2)
        
        # 첫 번째 리스트 (이미지 리스트)
        self.list1 = tk.Listbox(self.left_frame, width=30, height=15)
        self.list1.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.list1.bind('<<ListboxSelect>>', self.on_select_image)
        
        # 두 번째 리스트 (액션 리스트)
        self.list2 = tk.Listbox(self.right_frame, width=40, height=15)
        self.list2.grid(row=0, column=0, columnspan=2, sticky="nsew")
        
        # 이미지 리스트 버튼
        ttk.Button(self.left_frame, text="이미지 추가", command=self.add_image).grid(row=2, column=0)
        ttk.Button(self.left_frame, text="이미지 삭제", command=self.remove_image).grid(row=2, column=1)
        
        # 액션 리스트 버튼
        ttk.Button(self.right_frame, text="액션 추가", command=self.add_action).grid(row=1, column=0)
        ttk.Button(self.right_frame, text="액션 삭제", command=self.remove_action).grid(row=1, column=1)

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

    def on_select_image(self, event):
        selection = self.list1.curselection()
        if selection:
            self.list2.delete(0, tk.END)
            selected_image = self.list1.get(selection)
            
            if selected_image in self.image_references:
                self.preview_label.configure(image=self.image_references[selected_image]['photo'])
            
            for action in self.action_data.get(selected_image, []):
                self.list2.insert(tk.END, action)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageActionListApp(root)
    root.mainloop()