"""서버 감시: 링크 전체를 점검 -> 상태 파일(status.json) 갱신 -> 연속 2회 이상이면 메일 -> 변화가 있거나 2시간마다 허브에 반영
작업 스케줄러가 10분마다 실행한다(pythonw)."""
import json, os, sys, time, subprocess, datetime
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from notify import send_mail

STATE = os.path.join(HERE, "monitor_state.json")
LOG = os.path.join(HERE, "monitor.log")
LOCK = os.path.join(HERE, "monitor.lock")
FAIL_LIMIT = 2          # 연속 몇 번 이상이면 알림
PUSH_EVERY_MIN = 120    # 변화가 없어도 이 간격으로 허브 상태 갱신
SLOW_SEC = 5.0

def log(m):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now():%m-%d %H:%M} {m}\n")
    try:
        if os.path.getsize(LOG) > 200_000:
            open(LOG, "w", encoding="utf-8").write("")
    except OSError:
        pass

CURL = "C:/Windows/System32/curl.exe"

def check(p):
    # 파이썬 기본 인증서 저장소가 Railway 인증서 체인을 만료로 오판하므로 윈도우 curl(Schannel)로 점검한다
    t0 = time.time()
    try:
        r = subprocess.run([CURL, "-s", "-o", "NUL", "-L", "-m", "25", "-A", "yucle-hub-monitor/1.0",
                            "-w", "%{http_code} %{time_total}", p["u"]],
                           capture_output=True, text=True, timeout=40)
        code_s, _, sec_s = r.stdout.strip().partition(" ")
        code = int(code_s) if code_s.isdigit() else 0
        sec = float(sec_s) if sec_s else time.time() - t0
    except Exception:
        return {"s": "down", "ms": int((time.time() - t0) * 1000), "code": 0}
    ms = int(sec * 1000)
    if code == 0:
        return {"s": "down", "ms": ms, "code": 0}
    s = "error" if code >= 500 else ("slow" if sec > SLOW_SEC else "ok")
    return {"s": s, "ms": ms, "code": code}

def refresh_busy():
    p = os.path.join(HERE, "refresh.lock")
    return os.path.exists(p) and time.time() - os.path.getmtime(p) < 1800

def main():
    if os.path.exists(LOCK) and time.time() - os.path.getmtime(LOCK) < 600:
        return
    open(LOCK, "w").write("x")
    try:
        links = json.load(open(os.path.join(HERE, "links.json"), encoding="utf-8"))
        st = json.load(open(STATE, encoding="utf-8")) if os.path.exists(STATE) else {"fails": {}, "alerted": {}, "last_push": 0, "last_sig": ""}
        with ThreadPoolExecutor(6) as ex:
            res = list(ex.map(check, links))
        items = {p["n"]: r for p, r in zip(links, res)}
        now = datetime.datetime.now()
        newly_bad, recovered = [], []
        for p in links:
            n, bad = p["n"], items[p["n"]]["s"] in ("down", "error")
            if p.get("watch") is False:
                continue
            if bad:
                st["fails"][n] = st["fails"].get(n, 0) + 1
                if st["fails"][n] >= FAIL_LIMIT and not st["alerted"].get(n):
                    st["alerted"][n] = True
                    newly_bad.append(n)
            else:
                st["fails"][n] = 0
                if st["alerted"].pop(n, None):
                    recovered.append(n)
        def desc(n):
            r = items[n]
            return f"{n}: " + ("응답 없음" if r["s"] == "down" else f"서버 오류 HTTP {r['code']}")
        if newly_bad:
            send_mail(f"[허브] 서버 이상 {len(newly_bad)}건: " + ", ".join(newly_bad),
                      "연속 2번(약 10분) 이상이 확인되었습니다.\n\n" + "\n".join(desc(n) for n in newly_bad) +
                      f"\n\n확인 시각 {now:%Y-%m-%d %H:%M}\n허브: https://partybok-crypto.github.io/yucle-hub/")
            log("알림: " + ", ".join(newly_bad))
        if recovered:
            send_mail("[허브] 서버 복구: " + ", ".join(recovered), "정상으로 돌아왔습니다.\n" + ", ".join(recovered) + f"\n확인 시각 {now:%Y-%m-%d %H:%M}")
            log("복구: " + ", ".join(recovered))
        out = {"checked_at": now.strftime("%Y-%m-%d %H:%M"), "items": items}
        sig = json.dumps({n: r["s"] for n, r in items.items()}, sort_keys=True)
        due = (time.time() - st.get("last_push", 0)) / 60 >= PUSH_EVERY_MIN
        if (sig != st.get("last_sig") or due) and not refresh_busy():
            json.dump(out, open(os.path.join(HUB, "status.json"), "w", encoding="utf-8"), ensure_ascii=False)
            g = ["git", "-C", HUB]
            subprocess.run(g + ["add", "status.json"], capture_output=True)
            c = subprocess.run(g + ["commit", "-m", f"status {now:%m-%d %H:%M}", "--", "status.json"], capture_output=True)
            if c.returncode == 0:
                subprocess.run(g + ["pull", "--rebase", "-q"], capture_output=True)
                p = subprocess.run(g + ["push", "-q"], capture_output=True, text=True)
                log("상태 반영" + ("" if p.returncode == 0 else f" 푸시 실패 {p.stderr[:100]}"))
            st["last_push"], st["last_sig"] = time.time(), sig
        json.dump(st, open(STATE, "w", encoding="utf-8"), ensure_ascii=False)
    except Exception as e:
        log(f"오류 {type(e).__name__}: {e}")
    finally:
        try: os.remove(LOCK)
        except OSError: pass

if __name__ == "__main__":
    main()
