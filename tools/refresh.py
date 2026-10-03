"""한 번에: 화면 캡처 -> index.html 생성 -> 변경이 있으면 커밋·푸시"""
import os, subprocess, sys, datetime
try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.dirname(HERE)
py = sys.executable
log = open(os.path.join(HERE, "refresh.log"), "a", encoding="utf-8")
def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV, **kw)
    log.write(f"$ {' '.join(cmd)}\n{r.stdout}{r.stderr}\n"); log.flush()
    print(r.stdout, r.stderr)
    return r
log.write(f"\n===== {datetime.datetime.now():%Y-%m-%d %H:%M} =====\n")
if "--no-capture" not in sys.argv:
    run([py, os.path.join(HERE, "capture.py")])
run([py, os.path.join(HERE, "build.py")])
g = ["git", "-C", HUB]
run(g + ["add", "index.html", "shots", "tools", ".gitignore"])
if run(g + ["status", "--porcelain"]).stdout.strip():
    msg = f"hub auto refresh {datetime.datetime.now():%Y-%m-%d}\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
    run(g + ["commit", "-m", msg])
    run(g + ["push"])
    print("푸시 완료")
else:
    print("변경 없음")
