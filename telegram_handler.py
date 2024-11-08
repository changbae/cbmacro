import json
import requests
import tkinter as tk
from tkinter import ttk, messagebox
from config import TELEGRAM_SETTINGS_FILE

class TelegramHandler:
    def __init__(self):
        self.settings = {
            'app_key': '',
            'chat_id': ''
        }
        self.load_settings()

    def load_settings(self):
        try:
            with open(TELEGRAM_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                self.settings = json.load(f)
        except:
            pass

    def save_settings(self, app_key, chat_id):
        self.settings['app_key'] = app_key
        self.settings['chat_id'] = chat_id
        with open(TELEGRAM_SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=2)

    def send_message(self, message):
        try:
            url = f'https://api.telegram.org/bot{self.settings["app_key"]}/sendMessage'
            data = {
                'chat_id': self.settings['chat_id'],
                'text': message,
                'parse_mode': 'Markdown'
            }
            response = requests.post(url, data=data)
            return response.json().get('ok', False)
        except Exception as e:
            print(f"Telegram error: {str(e)}")
            return False

    def show_settings_dialog(self, parent):
        dialog = tk.Toplevel(parent)
        dialog.title("텔레그램 설정")
        dialog.geometry("400x200")
        dialog.transient(parent)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # APP Key 입력
        ttk.Label(frame, text="APP Key:").grid(row=0, column=0, sticky='e', pady=5)
        app_key_var = tk.StringVar(value=self.settings['app_key'])
        app_key_entry = ttk.Entry(frame, textvariable=app_key_var, width=40)
        app_key_entry.grid(row=0, column=1, padx=5, pady=5)

        # Chat ID 입력
        ttk.Label(frame, text="Chat ID:").grid(row=1, column=0, sticky='e', pady=5)
        chat_id_var = tk.StringVar(value=self.settings['chat_id'])
        chat_id_entry = ttk.Entry(frame, textvariable=chat_id_var, width=40)
        chat_id_entry.grid(row=1, column=1, padx=5, pady=5)

        # 테스트 메시지
        ttk.Label(frame, text="테스트 메시지:").grid(row=2, column=0, sticky='e', pady=5)
        test_msg_var = tk.StringVar(value="테스트 메시지입니다.")
        test_msg_entry = ttk.Entry(frame, textvariable=test_msg_var, width=40)
        test_msg_entry.grid(row=2, column=1, padx=5, pady=5)

        def save_and_close():
            self.save_settings(app_key_var.get(), chat_id_var.get())
            dialog.destroy()
            messagebox.showinfo("알림", "설정이 저장되었습니다.")

        def test_send():
            if self.send_message(test_msg_var.get()):
                messagebox.showinfo("성공", "테스트 메시지가 전송되었습니다.")
            else:
                messagebox.showerror("실패", "메시지 전송에 실패했습니다.")

        # 버튼 프레임
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)

        ttk.Button(btn_frame, text="테스트", command=test_send).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="저장", command=save_and_close).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="취소", command=dialog.destroy).pack(side=tk.LEFT, padx=5)