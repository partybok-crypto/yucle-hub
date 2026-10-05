# 유클 업무 허브 (링크허브)

폰·PC에서 쓰는 프로그램 바로가기 + 데이터 흐름 + 화면 캡처(테마2) 페이지. GitHub Pages 공개 주소: https://partybok-crypto.github.io/yucle-hub/
저장소: partybok-crypto/yucle-hub (main 푸시 = 1~2분 뒤 자동 반영)

## 파일 구조 (index.html은 생성물 — 직접 고치지 말 것)
- `tools/links.json` : 프로그램 목록·주소·하위 메뉴(subs). **주소가 바뀌면 여기만 고침**
- `tools/flow_part1~3.js` : 데이터 흐름 상세(입력/저장/외부연동/자동실행/연결)
- `tools/short.js` : 데이터 흐름 카드의 짧은 칩(입력→저장→읽는 곳)
- `tools/template.html` : 화면 코드
- `tools/blur.json` : 캡처에서 흐리게 할 영역(이름·금액·연락처·위치)
- `tools/sites.json` : 사이트 탭 목록(프로그램이 쓰는 외부 사이트, `used`=쓰는 프로그램). `tools/map.json` : 연결 지도(그룹·연결 edges·시트 탭별 영향·lanes). build.py가 두 파일과 프로그램 목록이 어긋나면 "연결 검증 경고"를 출력한다
- `tools/capture_m.py` + `tools/blur_m.json` : 모바일(500x1000) 화면 캡처 → `shots/mN.jpg` + `shots_m.json` (테마2의 PC/모바일 전환용). 캡처 전 HTTP 오류(4xx/5xx)면 이전 이미지 유지. 개인정보 영역은 blur_m.json(500x1000 좌표)에 지정. Edge는 저장 경로를 반드시 절대 경로로 줘야 함
- 화면 개인 설정(분류 이름·이동·즐겨찾기·추가 항목)은 브라우저 localStorage 저장 → 기기 간에는 "설정 옮기기" 링크로 옮긴다
- `tools/capture.py` : 전체 화면 캡처 → 흐림 → shots/
- `tools/build.py` : 위 파일들로 index.html 생성
- `tools/refresh.py` : 캡처 + 빌드 + 커밋 + 푸시 (`python tools/refresh.py`, 캡처 생략은 `--no-capture`). 문제가 있으면 메일 발송
- `tools/monitor.py` : 서버 감시(링크 전체를 curl로 점검) → `status.json` 갱신 → 이상이 확인되면 메일(하루 1번 점검), 복구 시 메일. 변화가 있거나 2시간마다만 허브에 푸시
- `tools/notify.py` : 메일 발송(마케팅OS 서버의 Brevo 설정을 Railway에서 그때그때 읽음 — 파일에 저장하지 않음)
- `tools/projects.json` : 데이터 흐름 항목 ↔ 프로그램 폴더 연결(코드 마지막 변경일 표시용). 변경일이 설명 점검일(`FLOW_DATE` 또는 항목의 `v`)보다 늦으면 카드에 "설명 점검 필요"
- `sw.js`(자동 생성) : 오프라인·빠른 로딩용 서비스 워커
- 파이썬 기본 인증서 확인이 Railway 인증서를 만료로 오판하므로 점검은 윈도우 curl을 쓴다

## 작업 규칙
- 프로그램의 주소·화면·입력/저장 구조를 바꾸면 이 허브도 같이 고친다: links.json / flow_part*.js / short.js 수정 → `python tools/build.py` → 푸시.
- 새 프로그램을 추가하면 links.json에 넣고, blur.json에서 개인정보가 보이는 화면인지 확인한 뒤 `refresh.py`로 캡처한다.
- 푸시는 `git -C /c/Users/123/Desktop/AUTO/링크허브 ...` 형식으로 한다(설정에 허용 규칙 있음). 사용자에게 `!` 명령을 보내지 않는다.
- 개인정보(이름·금액·연락처·거래처·실시간 위치)가 보이는 캡처는 반드시 흐리게 처리한 뒤 올린다. 시트 ID·키 이름은 데이터 흐름 문구에 넣지 않는다.
- 작업 스케줄러: YucleHub_Monitor(매일 12:00 monitor.py), YucleHub_Refresh(일요일 07:00 refresh.py). 둘 다 pythonw(창 없음).
- 데이터 흐름 항목을 고쳐서 설명을 다시 확인했다면 flow_part의 해당 항목에 `v:"YYYY-MM-DD"`를 넣어 점검일을 갱신한다.
- 메일 받는 곳은 마케팅OS의 EMAIL_TO(sinijini1@naver.com). 알림 테스트: `python tools/notify.py`
