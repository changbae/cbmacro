import json
import os
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import messagebox
from config import MACRO_SETTINGS_FILE, THUMBNAIL_SIZE

class SettingsHandler:
    @staticmethod
    def save_settings(action_data, image_references):
        try:
            settings = {
                'action_data': action_data,
                'image_paths': {name: data['path'] for name, data in image_references.items()}
            }
            
            with open(MACRO_SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("알림", "설정이 저장되었습니다.")
            return True
        except Exception as e:
            messagebox.showerror("오류", f"설정 저장 중 오류 발생: {str(e)}")
            return False

    @staticmethod
    def load_settings():
        try:
            if not os.path.exists(MACRO_SETTINGS_FILE):
                messagebox.showwarning("알림", "저장된 설정 파일이 없습니다.")
                return None
                
            with open(MACRO_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # 이미지 파일 존재 확인
            for image_name, image_path in settings['image_paths'].items():
                if not os.path.exists(image_path):
                    messagebox.showwarning("주의", f"이미지를 찾을 수 없습니다: {image_name}")
            
            return settings
        except Exception as e:
            messagebox.showerror("오류", f"설정 불러오기 중 오류 발생: {str(e)}")
            return None

    @staticmethod
    def create_thumbnail(image_path):
        try:
            image = Image.open(image_path)
            image.thumbnail(THUMBNAIL_SIZE)
            return ImageTk.PhotoImage(image)
        except Exception as e:
            messagebox.showerror("오류", f"썸네일 생성 중 오류 발생: {str(e)}")
            return None