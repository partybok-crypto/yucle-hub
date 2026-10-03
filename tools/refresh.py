"""한 번에: 화면 캡처 -> index.html 생성 -> 변경이 있으면 커밋·푸시. 실패하면 메일로 알린다."""
import os, subprocess, sys, datetime, time
try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass
HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from notify import send_mail
py = sys.executable
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
LOCK = os.path.join(HERE, "refresh.lock")
log = open(os.path.join(HERE, "refresh.log"), "a", encoding="utf-8")

def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV, **kw)
    log.write(f"$ {' '.join(cmd)}\n{r.stdout}{r.stderr}\n"); log.flush()
    print(r.stdout, r.stderr)
    return r

def main():
    log.write(f"\n===== {datetime.datetime.now():%Y-%m-%d %H:%M} =====\n")
    problems = []
    if "--no-capture" not in sys.argv:
        r = run([py, os.path.join(HERE, "capture.py")])
        if r.returncode != 0:
            problems.append("캡처 프로그램 오류")
        problems += [l.strip() for l in r.stdout.splitlines() if "이전 이미지 유지" in l]
    b = run([py, os.path.join(HERE, "build.py")])
    if b.returncode != 0:
        problems.append("index.html 생성 실패")
    g = ["git", "-C", HUB]
    run(g + ["add", "index.html", "sw.js", "shots", "tools", ".gitignore", "CLAUDE.md"])
    if run(g + ["status", "--porcelain"]).stdout.strip():
        msg = f"hub auto refresh {datetime.datetime.now():%Y-%m-%d}\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
        run(g + ["commit", "-m", msg])
        run(g + ["pull", "--rebase", "-q"])
        p = run(g + ["push"])
        if p.returncode != 0:
            problems.append("푸시 실패: " + p.stderr.strip()[:200])
        else:
            print("푸시 완료")
    else:
        print("변경 없음")
    if problems:
        send_mail("[허브] 화면 캡처 갱신에 문제가 있습니다", "자동 갱신 중 아래 문제가 있었습니다.\n\n" + "\n".join(problems) +
                  f"\n\n시각 {datetime.datetime.now():%Y-%m-%d %H:%M}\n로그: AUTO\링크허브\tools\refresh.log")

if os.path.exists(LOCK) and time.time() - os.path.getmtime(LOCK) < 1800:
    sys.exit("이미 실행 중")
open(LOCK, "w").write("x")
try:
    main()
except Exception as e:
    log.write(f"예외 {type(e).__name__}: {e}\n")
    send_mail("[허브] 화면 캡처 갱신 중 오류", f"{type(e).__name__}: {e}")
    raise
finally:
    try: os.remove(LOCK)
    except OSError: pass
