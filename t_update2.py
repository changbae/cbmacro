import requests
import os
import sys
import shutil
import zipfile

def check_for_update(owner, repo):
    API_URL = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    
    try:
        print(f'{API_URL}')
        response = requests.get(API_URL)
        print(response)
        response.raise_for_status()  # 에러 발생 시 예외를 발생시킵니다.
        latest_release = response.json()
        latest_version = latest_release['tag_name']
        
        # 현재 버전 확인 (version.txt 파일이 없으면 '0.0.0'으로 가정)
        try:
            with open("version.txt", "r") as f:
                current_version = f.read().strip()
        except FileNotFoundError:
            current_version = '0.0.0'
        
        if latest_version != current_version:
            return latest_release
        else:
            return None
    except requests.RequestException as e:
        print(f"API 요청 중 오류 발생: {e}")
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

def main(owner, repo):
    update = check_for_update(owner, repo)
    if update:
        print(f"새 버전 {update['tag_name']}이(가) 발견되었습니다.")
        
        if update['assets']:
            print("업데이트를 시작합니다.")
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
            print("릴리스에 다운로드 가능한 자산이 없습니다. 수동으로 업데이트를 확인해주세요.")
            update_version(update['tag_name'])  # 버전 정보만 업데이트
    else:
        print("이미 최신 버전이거나 업데이트를 확인할 수 없습니다.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("사용법: python script.py [소유자] [저장소]")
        sys.exit(1)
    
    owner = sys.argv[1]
    repo = sys.argv[2]
    main(owner, repo)