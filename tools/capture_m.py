"""프로그램 모바일 화면 캡처 -> 개인정보 영역 흐림(blur_m.json) -> ../shots/mN.jpg + shots_m.json 갱신
PC 캡처(capture.py)와 같은 방식. 실패하거나 빈 화면이면 이전 이미지를 그대로 둔다.
(헤드리스 Edge는 창 너비가 500 아래로 줄지 않아 500x1000으로 찍는다 — 스마트폰 레이아웃 기준점 600px 아래)"""
import os, sys, json, subprocess, tempfile, shutil, time
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageFilter, ImageStat

HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.dirname(HERE)
OUT = os.path.join(HUB, "shots")
RAW = os.path.join(HERE, "raw_m")
os.makedirs(OUT, exist_ok=True); os.makedirs(RAW, exist_ok=True)

links = json.load(open(os.path.join(HERE, "links.json"), encoding="utf-8"))
bp = os.path.join(HERE, "blur_m.json")
blur = json.load(open(bp, encoding="utf-8")) if os.path.exists(bp) else {}
shots_p = os.path.join(HERE, "shots_m.json")
shots = json.load(open(shots_p, encoding="utf-8")) if os.path.exists(shots_p) else {}
W, H = 500, 1000
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"

EDGE = next((p for p in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                         r"C:\Program Files\Microsoft\Edge\Application\msedge.exe") if os.path.exists(p)), None)
if not EDGE:
    sys.exit("Edge를 찾을 수 없습니다")

def _run(cmd, wait):
    p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        p.wait(timeout=wait)
    except subprocess.TimeoutExpired:
        pass
    finally:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def shoot(i, url):
    png = os.path.join(RAW, f"{i}.png")   # 반드시 절대 경로 (상대 경로는 Edge가 엉뚱한 곳에 저장)
    base = [EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--window-size={W},{H}", f"--user-agent={UA}"]
    for extra, wait in ((["--virtual-time-budget=12000"], 50), (["--timeout=15000"], 40)):
        if os.path.exists(png): os.remove(png)
        prof = tempfile.mkdtemp(prefix="hubshotm_")
        try:
            _run(base + extra + [f"--user-data-dir={prof}", f"--screenshot={png}", url], wait)
        finally:
            shutil.rmtree(prof, ignore_errors=True)
        if os.path.exists(png):
            return png
    return None

def http_ok(url):
    """페이지가 오류(4xx/5xx)를 돌려주면 캡처하지 않는다 — 오류 화면이 그림으로 저장되는 것을 막음"""
    try:
        r = subprocess.run(["curl", "-s", "-o", "NUL", "-L", "-m", "25", "-w", "%{http_code}", url], capture_output=True, text=True, creationflags=0x08000000)
        c = int(r.stdout.strip() or 0)
        return c == 0 or c < 400
    except Exception:
        return True

def process(i, p):
    if not http_ok(p["u"]):
        return i, p["n"], "서버 오류 응답(이전 이미지 유지)"
    png = shoot(i, p["u"])
    if not png:
        return i, p["n"], "모바일 캡처 실패(이전 이미지 유지)"
    im = Image.open(png).convert("RGB")
    if im.size != (W, H): im = im.resize((W, H))
    if max(ImageStat.Stat(im.convert("L")).stddev) < 6:
        return i, p["n"], "모바일 빈 화면(이전 이미지 유지)"
    for x0, y0, x1, y1 in blur.get(p["n"], []):
        im.paste(im.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(14)), (x0, y0))
    im.resize((300, 600), Image.LANCZOS).save(os.path.join(OUT, f"m{i}.jpg"), quality=72, optimize=True)
    shots[p["n"]] = f"shots/m{i}.jpg"
    return i, p["n"], "갱신"

if __name__ == "__main__":
    t0 = time.time()
    raw_only = "--raw" in sys.argv   # 흐림 영역을 정할 때: 원본만 저장하고 shots/는 건드리지 않음
    with ThreadPoolExecutor(4) as ex:
        if raw_only:
            list(ex.map(lambda t: shoot(t[0], t[1]["u"]), list(enumerate(links))))
        else:
            for i, n, r in ex.map(lambda t: process(*t), list(enumerate(links))):
                print(f"{i:2d} {n}: {r}")
            json.dump(shots, open(shots_p, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"capture_m done {time.time()-t0:.0f}s")
