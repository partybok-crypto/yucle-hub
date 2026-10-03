"""index.html 생성기: links.json + flow_part*.js + short.js + shots.json + template.html -> ../index.html"""
import os, json, subprocess, datetime, hashlib, time
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


# ---- 프로그램 폴더의 마지막 코드 변경일 (git 커밋일, 없으면 파일 수정일) ----
FLOW_DATE = "2026-10-03"   # 데이터 흐름 설명을 마지막으로 점검한 날(항목별 v 값이 있으면 그 값이 우선)
AUTO = os.path.dirname(HUB)
SKIP = {"node_modules", ".git", "dist", "build", "__pycache__", ".next", "target", ".venv", "venv", "logs", "data", "backups", "chrome_profile", "test-results", ".gradle"}
def last_change(rel):
    d = os.path.join(AUTO, rel)
    if not os.path.isdir(d):
        return None
    try:
        r = subprocess.run(["git", "-C", d, "log", "-1", "--format=%cs", "--", "."], capture_output=True, text=True, timeout=30)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    newest = 0
    for root, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if x not in SKIP]
        for f in files:
            if f.endswith((".png", ".jpg", ".log", ".db", ".zip", ".mp4", ".pdf")):
                continue
            try:
                newest = max(newest, os.path.getmtime(os.path.join(root, f)))
            except OSError:
                pass
    return datetime.date.fromtimestamp(newest).isoformat() if newest else None
projects = json.load(open(os.path.join(HERE, "projects.json"), encoding="utf-8"))
chg = {n: c for n, rel in projects.items() if (c := last_change(rel))}
chgjs = "const CHG=" + json.dumps(chg, ensure_ascii=False) + ";" + chr(10) + "const FLOW_DATE=" + json.dumps(FLOW_DATE) + ";"

out = (rd("template.html").replace("/*BASE*/", base).replace("/*FLOW*/", flow)
       .replace("/*SHORT*/", rd("short.js")).replace("/*SHOTS*/", shots).replace("/*CHG*/", chgjs))
open(os.path.join(HUB, "index.html"), "w", encoding="utf-8").write(out)
# ---- 서비스 워커(오프라인·빠른 로딩) ----
ver = hashlib.md5(out.encode("utf-8")).hexdigest()[:10]
files = ["./", "manifest.json", "icon-192.png", "apple-touch-icon.png"] + sorted(set(json.loads(shots[len("const SHOTS="):-1]).values()))
sw = f"""const V="hub-{ver}";
const FILES={json.dumps(files, ensure_ascii=False)};
self.addEventListener("install",e=>{{e.waitUntil(caches.open(V).then(c=>c.addAll(FILES).catch(()=>{{}})).then(()=>self.skipWaiting()))}});
self.addEventListener("activate",e=>{{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==V).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))}});
self.addEventListener("fetch",e=>{{
  const r=e.request;if(r.method!=="GET")return;
  const u=new URL(r.url);if(u.origin!==location.origin)return;
  if(u.pathname.endsWith("status.json")){{
    e.respondWith(fetch(r).then(x=>{{const c=x.clone();caches.open(V).then(ca=>ca.put(r,c));return x}}).catch(()=>caches.match(r)));return}}
  e.respondWith(caches.open(V).then(ca=>ca.match(r,{{ignoreSearch:true}}).then(hit=>{{
    const net=fetch(r).then(x=>{{if(x.ok)ca.put(r,x.clone());return x}}).catch(()=>hit);
    return hit||net}})));
}});
"""
open(os.path.join(HUB, "sw.js"), "w", encoding="utf-8").write(sw)
print("build ok", len(out), "links:", len(links))
