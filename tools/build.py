"""index.html 생성기: links.json + flow_part*.js + short.js + shots.json + template.html -> ../index.html"""
import os, json
HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.dirname(HERE)
rd = lambda p: open(os.path.join(HERE, p), encoding="utf-8").read()

links = json.load(open(os.path.join(HERE, "links.json"), encoding="utf-8"))
base = "const BASE=" + json.dumps(links, ensure_ascii=False) + ";"
parts = "".join(rd(f) for f in ("flow_part1.js", "flow_part2.js", "flow_part3.js"))
order = ["공통 구조 (현장 시트)", "배송 입력", "포장 입력", "건조기 관리", "출퇴근 관리", "공장 전광판", "차량 위치 (CarLive)", "가스 카메라",
         "배송 현황", "현황지 출력", "보조컴퓨터 (포장랭킹 카톡)", "재무관리", "마케팅 스튜디오 (마케팅OS)", "영업 허브",
         "AI 전화상담", "회사전화", "청과 수입 판단", "출판 (Bookforge)", "내편지도", "사주도령",
         "쿠팡 주문내역 취합기", "forwarder.kr 수집기", "한글 폰트 변환기"]
flow = ("const FLOW=[\n" + parts + "];\nconst FO=" + json.dumps(order, ensure_ascii=False) +
        ";\nFLOW.sort((a,b)=>{const i=FO.indexOf(a.n),j=FO.indexOf(b.n);return (i<0?99:i)-(j<0?99:j)});")
shots = "const SHOTS=" + (rd("shots.json") if os.path.exists(os.path.join(HERE, "shots.json")) else "{}") + ";"

out = (rd("template.html").replace("/*BASE*/", base).replace("/*FLOW*/", flow)
       .replace("/*SHORT*/", rd("short.js")).replace("/*SHOTS*/", shots))
open(os.path.join(HUB, "index.html"), "w", encoding="utf-8").write(out)
print("build ok", len(out), "links:", len(links))
