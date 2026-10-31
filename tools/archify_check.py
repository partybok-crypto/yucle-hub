"""구조도 점검 알림: 마지막 코드 대조일(archify_verified.json) 이후 30일마다, 그 사이 코드가 바뀐 프로그램을 메일로 알린다.
대조를 마치면 archify_verified.json 의 verified 날짜를 오늘로 고친다. monitor.py 가 매일 호출한다."""
import json, os, subprocess, datetime
from notify import send_mail

HERE = os.path.dirname(os.path.abspath(__file__))
AUTO = os.path.dirname(os.path.dirname(HERE))
CFG = os.path.join(HERE, "archify_verified.json")
STATE = os.path.join(HERE, "archify_state.json")
NOWIN = 0x08000000


def commits_since(rel, since):
    d = os.path.join(AUTO, rel)
    if not os.path.isdir(d):
        return None
    try:
        r = subprocess.run(["git", "-C", d, "log", f"--since={since} 23:59:59", "--oneline", "--", "."],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30, creationflags=NOWIN)
        return len([x for x in r.stdout.splitlines() if x.strip()]) if r.returncode == 0 else None
    except Exception:
        return None


def check():
    cfg = json.load(open(CFG, encoding="utf-8"))
    st = json.load(open(STATE, encoding="utf-8")) if os.path.exists(STATE) else {}
    today = datetime.date.today()
    base = max(cfg["verified"], st.get("last_alert", ""))
    if (today - datetime.date.fromisoformat(base)).days < cfg.get("interval_days", 30):
        return "대기"
    changed = {n: c for n, rel in cfg["folders"].items() if (c := commits_since(rel, cfg["verified"]))}
    st["last_alert"] = today.isoformat()
    if changed:
        lines = "\n".join(f"- {n}: 커밋 {c}건" for n, c in sorted(changed.items(), key=lambda x: -x[1]))
        send_mail(f"[허브] 구조도 점검 필요 {len(changed)}곳",
                  f"마지막 대조일 {cfg['verified']} 이후 코드가 바뀐 프로그램입니다.\n\n{lines}\n\n"
                  "Claude에게 '구조도 최신화해줘'라고 하면 코드와 대조해 고칩니다. 대조가 끝나면 tools/archify_verified.json 의 verified 날짜가 갱신됩니다.\n"
                  "허브: https://partybok-crypto.github.io/yucle-hub/")
    json.dump(st, open(STATE, "w", encoding="utf-8"), ensure_ascii=False)
    return f"알림 {len(changed)}곳" if changed else "변경 없음"


if __name__ == "__main__":
    print(check())
