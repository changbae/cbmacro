# 기본 설정값들
ACTION_TYPES = {
    "마우스 클릭": ["x좌표", "y좌표"],
    "마우스 더블클릭": ["x좌표", "y좌표"],
    "키보드 입력": ["입력할 텍스트"],
    "딜레이": ["대기시간(초)"],
    "텔레그램 전송": ["메시지 내용"]
}

# 파일 경로 설정
TELEGRAM_SETTINGS_FILE = 'telegram_settings.json'
MACRO_SETTINGS_FILE = 'macro_settings.json'

# 이미지 매칭 설정
MATCHING_THRESHOLD = 0.8
THUMBNAIL_SIZE = (150, 150)

# UI 설정
WINDOW_TITLE = "Image Action List Application"
PREVIEW_SIZE = (200, 200)
LIST_WIDTH = 30
LIST_HEIGHT = 15
ACTION_LIST_WIDTH = 40