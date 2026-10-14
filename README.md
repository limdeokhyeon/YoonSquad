# YoonSquad – JPG / RAW 분류기

맥북에서 쓰는 사진 분류 프로그램입니다. 폴더 안의 JPG와 RAW(소니 `.ARW` 기본, 캐논·니콘·후지 등도 지원)를
`JPG/`, `RAW/` 폴더로 나눠 줍니다.

## 기능
- 기본은 **복사**(원본 유지), 옵션으로 이동
- JPG+RAW 짝 개수, JPG만/RAW만 있는 사진 목록 표시
- 날짜별 폴더(`2026-10-14/JPG`, `2026-10-14/RAW`) 옵션 (파일 수정일 기준)
- 하위 폴더 포함 옵션 (SD카드 `DCIM/100MSDCF` 등)
- 이미 같은 파일이 있으면 건너뛰고, 이름만 같고 내용이 다르면 `_1`을 붙여 덮어쓰지 않음
- SD카드의 `._DSC0001.ARW` 같은 숨김 파일 무시
- **미리보기**로 결과를 먼저 확인한 뒤 실행

## 앱(.app) 받기
GitHub 저장소의 **Actions → Build macOS app → 최신 실행 → Artifacts → PhotoSort-mac** 에서 zip을 받아 압축을 풀고
`PhotoSort.app`을 응용 프로그램 폴더로 옮기면 됩니다. (Apple Silicon 맥용, 파이썬 설치 불필요)

서명이 없는 앱이라 처음 실행할 때 "열 수 없음" 경고가 뜹니다. 앱을 **우클릭 → 열기 → 열기**로 한 번 실행하거나,
터미널에서 `xattr -dr com.apple.quarantine /Applications/PhotoSort.app` 를 실행하세요.

직접 빌드하려면 맥에서 `./build_app.sh` → `dist/PhotoSort.app`

## 실행 방법 (맥, 소스로 실행)
Tk가 들어 있는 파이썬이 필요합니다. [python.org](https://www.python.org/downloads/macos/) 설치본을 권장합니다.
(Homebrew는 `brew install python-tk`)

```
python3 main.py
```

또는 `PhotoSort.command`를 더블클릭 (처음 한 번 `chmod +x PhotoSort.command`).

폴더 끌어다 놓기를 쓰려면: `pip3 install tkinterdnd2` (없어도 [폴더 선택] 버튼으로 사용 가능)

## 테스트
```
python3 -m unittest discover -s tests
```
