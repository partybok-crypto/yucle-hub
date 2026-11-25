"""팀 운영 지표 수집(마케팅·영업·운영·CS) -> monitor.py가 status.json의 "kpi"에 넣는다.
각 프로그램의 공개 조회 API에서 '개수'만 모은다. 이름·전화번호·금액·거래처는 저장하지 않는다(status.json은 공개 저장소에 올라감).
기준(노랑/빨강 경계)은 kpi.json, 날짜별 기록은 kpi_hist.json(최근 30일)."""
import json, os, re, subprocess, datetime
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
HIST = os.path.join(HERE, "kpi_hist.json")
CURL = "C:/Windows/System32/curl.exe"
NOWIN = 0x08000000
AUTO_KEYS = ("ops_pack_pct", "ops_on_shift")   # 요일·시각마다 달라서 같은 요일·같은 시각 평균을 기준으로 삼는 지표

MKT = "https://yuseong-marketing-os-review-production.up.railway.app"
SALES = "https://yuseong-sales-hub-production.up.railway.app"
AI = "https://server-production-8d8f.up.railway.app"
BOARD = "https://yuseong-display-board-production.up.railway.app"
PHONE = "https://yuseong-phone-production.up.railway.app"
URLS = {
    "glance": MKT + "/api/today-glance", "modules": MKT + "/api/modules", "errors": MKT + "/api/errors",
    "ai_today": AI + "/api/model2/today", "ai_usage": AI + "/api/bulk/usage",
    "plan": BOARD + "/api/display/packing-plan", "board": BOARD + "/api/status", "issues": BOARD + "/api/issues",
    "claims": BOARD + "/api/display/claims", "phone": PHONE + "/health", "live": PHONE + "/api/live",
}


def get(u):
    try:
        r = subprocess.run([CURL, "-s", "-L", "-m", "45", "-A", "yucle-hub-monitor/1.0", u],
                           capture_output=True, timeout=60, creationflags=NOWIN)
        return json.loads(r.stdout.decode("utf-8"))
    except Exception:
        return None


def reason(msg):
    m = str(msg)
    if "invalid_grant" in m or "expired or revoked" in m:
        return "구글 로그인 토큰 만료"
    if "429" in m and "uota" in m:
        return "구글시트 읽기 한도 초과"
    if "network" in m.lower() or "timeout" in m.lower() or "timed out" in m.lower():
        return "네트워크 오류"
    if "login" in m.lower() or "로그인" in m:
        return "로그인 필요"
    return "기타 오류"


def collect():
    with ThreadPoolExecutor(6) as ex:
        R = dict(zip(URLS, ex.map(get, URLS.values())))
    v, miss, mods = {}, [], None
    today = datetime.date.today().isoformat()

    # ---- 마케팅 (마케팅OS) ----
    g = (R["glance"] or {}).get("data") if R["glance"] else None
    if g:
        tiles = [t for t in g.get("tiles", []) if t.get("key") != "errors"]
        okc = sum(1 for t in tiles if t.get("level") in ("ok", "wait") or (t.get("key") == "procurement" and t.get("level") == "warn"))
        v["mkt_jobs_ok"] = round(okc * 100 / len(tiles)) if tiles else None
        et = next((t for t in g.get("tiles", []) if t.get("key") == "errors"), None)
        n = re.match(r"(\d+)", str(et.get("main", ""))) if et else None
        v["mkt_err"] = int(n.group(1)) if n else 0
        jobs = [{"n": t.get("title"), "s": t.get("level"), "m": str(t.get("main", ""))[:30]} for t in tiles]
    else:
        miss.append("마케팅 요약"); jobs = []
    rows = (R["modules"] or {}).get("data") if R["modules"] else None
    if rows is not None:
        errs = (R["errors"] or {}).get("data") or []
        by = {}
        for e in errs:
            if str(e.get("발생일시", ""))[:10] == today and str(e.get("복구상태", "")) != "복구완료":
                k = str(e.get("모듈ID", "") or "기타")
                d = by.setdefault(k, {"c": 0, "why": {}})
                d["c"] += 1
                w = reason(e.get("오류메시지", ""))
                d["why"][w] = d["why"].get(w, 0) + 1
        ml = []
        for r in rows:
            mid = str(r.get("모듈ID", ""))
            st = str(r.get("상태", ""))
            e = by.pop(mid, None)
            lv = "bad" if (e and e["c"]) or st in ("오류", "실패", "중지") else ("warn" if st not in ("정상", "") else "ok")
            ml.append({"id": mid, "n": r.get("모듈명") or mid, "g": r.get("분류") or "공통", "st": st or "-", "lv": lv,
                       "last": str(r.get("마지막실행시간", ""))[5:16], "e": e["c"] if e else 0,
                       "why": max(e["why"], key=e["why"].get) if e else ""})
        BG = {"lead_sources": "문의(리드) 수집", "ad_alerts": "광고 경보", "lead_center": "리드 센터"}
        for mid, e in by.items():   # 모듈 목록에 없는 백그라운드 작업에서 난 오류
            ml.append({"id": mid, "n": BG.get(mid, mid),"g": "백그라운드 작업", "st": "오류", "lv": "bad", "last": "", "e": e["c"],
                       "why": max(e["why"], key=e["why"].get)})
        ml.sort(key=lambda m: ({"bad": 0, "warn": 1, "ok": 2}[m["lv"]], -m["e"]))
        v["mkt_mod_bad"] = sum(1 for m in ml if m["lv"] != "ok")
        mods = {"prog": "마케팅 스튜디오 (마케팅OS)", "list": ml, "jobs": jobs, "err_sample": len(errs)}
    else:
        miss.append("마케팅 모듈")

    # ---- 영업 (AI 전화상담 / 영업 허브) ----
    s = (R["ai_today"] or {}).get("summary") if R["ai_today"] else None
    if s:
        v["ai_dialed"], v["ai_interest"], v["ai_answered"] = s.get("dialed", 0), s.get("interested", 0), s.get("answered", 0)
    else:
        miss.append("AI 발신 요약")
    u = R["ai_usage"]
    if u and u.get("planMinutes"):
        v["ai_minutes_pct"] = round(u.get("outboundBillableMinutes", 0) * 100 / u["planMinutes"])
    else:
        miss.append("통화 사용량")

    # ---- 운영 (공장 전광판) ----
    p = (R["plan"] or {}).get("plan") if R["plan"] else None
    if p:
        v["ops_pack_pct"] = p.get("progress_percent")
        ds = p.get("dryer_summary") or {}
        v["ops_dryers"] = f'{ds.get("dryers_running", 0)}/{ds.get("dryers_total", 0)}'
    else:
        miss.append("포장 계획")
    b = R["board"]
    if b and "on_shift_count" in b:
        v["ops_on_shift"] = b.get("on_shift_count")
    else:
        miss.append("출근 인원")
    iss = R["issues"]
    if iss and isinstance(iss.get("issues"), list):
        v["ops_issue_err"] = sum(1 for i in iss["issues"] if i.get("level") == "error")
        v["ops_issue_warn"] = sum(1 for i in iss["issues"] if i.get("level") != "error")
    else:
        miss.append("현장 이상 징후")

    # ---- CS (회사전화 / 클레임) ----
    lv = R["live"]
    if lv and "unhandled" in lv:
        v["cs_missed"] = lv.get("unhandled")
    else:
        miss.append("부재중")
    c = R["claims"]
    if c and isinstance(c.get("claims"), list):
        v["cs_claims_open"] = sum(1 for x in c["claims"] if x.get("status") == "open")
    else:
        miss.append("클레임")
    ph = R["phone"]
    if ph and "sync_problems" in ph:
        v["cs_sync"] = len(ph.get("sync_problems") or [])
    else:
        miss.append("회사전화 동기화")

    # ---- 날짜별 기록(그날 마지막 값) ----
    try:
        h = json.load(open(HIST, encoding="utf-8")) if os.path.exists(HIST) else {}
    except Exception:
        h = {}
    slots = h.pop("_slots", {})
    h[today] = {k: x for k, x in v.items() if isinstance(x, (int, float))}
    h = dict(sorted(h.items())[-30:])
    # 같은 요일·같은 시각 기록(자동 기준용): "요일-시" -> {지표: [[날짜, 값], ...최근 8회]}
    now = datetime.datetime.now()
    sk = f"{now.weekday()}-{now.hour:02d}"
    base = {}
    for k in AUTO_KEYS:
        if not isinstance(v.get(k), (int, float)):
            continue
        rec = [r for r in slots.setdefault(sk, {}).get(k, []) if r[0] != today]
        if rec:
            vals = [r[1] for r in rec]
            base[k] = {"avg": round(sum(vals) / len(vals), 1), "n": len(vals), "slot": sk}
        else:
            base[k] = {"avg": None, "n": 0, "slot": sk}
        slots[sk][k] = (rec + [[today, v[k]]])[-8:]
    h["_slots"] = slots
    json.dump(h, open(HIST, "w", encoding="utf-8"), ensure_ascii=False)
    days = {d: x for d, x in h.items() if not d.startswith("_")}
    return {"at": now.strftime("%Y-%m-%d %H:%M"), "v": v, "miss": miss, "mods": mods, "base": base,
            "hist": dict(list(days.items())[-14:])}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(collect(), ensure_ascii=False, indent=1))
