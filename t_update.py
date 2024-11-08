import requests
import os
import sys
import shutil
import zipfile

GITHUB_REPO = "/changbae/cbmacro"
API_SERVER_URL = f"https://api.github.com/repos/{GITHUB_REPO}"

def check_for_update():
    # 최신 릴리스 정보 가져오기
    response = requests.get(f"{API_SERVER_URL}/releases/latest")
    if response.status_code != 200:
        print("릴리스 정보를 가져오는데 실패했습니다.")
        return None
    
    latest_release = response.json()
    latest_version = latest_release['tag_name']
    
    # 현재 버전 확인
    with open("version.txt", "r") as f:
        current_version = f.read().strip()
    
    if latest_version != current_version:
        return latest_release
    else:
        return None

def download_update(asset_url, filename):
    response = requests.get(asset_url, stream=True)
    with open(filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

def apply_update(filename):
    with zipfile.ZipFile(filename, 'r') as zip_ref:
        zip_ref.extractall(".")
    
    os.remove(filename)

def update_version(new_version):
    with open("version.txt", "w") as f:
        f.write(new_version)

def main():
    update = check_for_update()
    if update:
        print(f"새 버전 {update['tag_name']}이(가) 발견되었습니다. 업데이트를 시작합니다.")
        
        # 업데이트 파일 다운로드
        asset = update['assets'][0]  # 첫 번째 asset을 다운로드
        download_update(asset['browser_download_url'], asset['name'])
        
        # 업데이트 적용
        apply_update(asset['name'])
        
        # 버전 정보 업데이트
        update_version(update['tag_name'])
        
        print("업데이트가 완료되었습니다. 프로그램을 재시작합니다.")
        os.execv(sys.executable, ['python'] + sys.argv)
    else:
        print("이미 최신 버전입니다.")

if __name__ == "__main__":
    main()