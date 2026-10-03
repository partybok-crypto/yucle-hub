# 유클 업무 허브 (링크허브)

폰·PC에서 쓰는 프로그램 바로가기 + 데이터 흐름 + 화면 캡처(테마2) 페이지. GitHub Pages 공개 주소: https://partybok-crypto.github.io/yucle-hub/
저장소: partybok-crypto/yucle-hub (main 푸시 = 1~2분 뒤 자동 반영)

## 파일 구조 (index.html은 생성물 — 직접 고치지 말 것)
- `tools/links.json` : 프로그램 목록·주소·하위 메뉴(subs). **주소가 바뀌면 여기만 고침**
- `tools/flow_part1~3.js` : 데이터 흐름 상세(입력/저장/외부연동/자동실행/연결)
- `tools/short.js` : 데이터 흐름 카드의 짧은 칩(입력→저장→읽는 곳)
- `tools/template.html` : 화면 코드
- `tools/blur.json` : 캡처에서 흐리게 할 영역(이름·금액·연락처·위치)
- `tools/capture.py` : 전체 화면 캡처 → 흐림 → shots/
- `tools/build.py` : 위 파일들로 index.html 생성
- `tools/refresh.py` : 캡처 + 빌드 + 커밋 + 푸시 (`python tools/refresh.py`, 캡처 생략은 `--no-capture`)

## 작업 규칙
- 프로그램의 주소·화면·입력/저장 구조를 바꾸면 이 허브도 같이 고친다: links.json / flow_part*.js / short.js 수정 → `python tools/build.py` → 푸시.
- 새 프로그램을 추가하면 links.json에 넣고, blur.json에서 개인정보가 보이는 화면인지 확인한 뒤 `refresh.py`로 캡처한다.
- 푸시는 `git -C /c/Users/123/Desktop/AUTO/링크허브 ...` 형식으로 한다(설정에 허용 규칙 있음). 사용자에게 `!` 명령을 보내지 않는다.
- 개인정보(이름·금액·연락처·거래처·실시간 위치)가 보이는 캡처는 반드시 흐리게 처리한 뒤 올린다. 시트 ID·키 이름은 데이터 흐름 문구에 넣지 않는다.
- 매주 일요일 07:00 작업 스케줄러(YucleHub_Refresh)가 refresh.py를 실행해 캡처를 갱신한다.
