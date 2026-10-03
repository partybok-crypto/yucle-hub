"""프로그램 화면 캡처 -> 개인정보 영역 흐림 -> ../shots/N.jpg + shots.json 갱신
실패하거나 빈 화면이면 이전 이미지를 그대로 둔다."""
import os, sys, json, subprocess, tempfile, shutil, time
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageFilter, ImageStat

HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.dirname(HERE)
OUT = os.path.join(HUB, "shots")
RAW = os.path.join(HERE, "raw")
os.makedirs(OUT, exist_ok=True); os.makedirs(RAW, exist_ok=True)

links = json.load(open(os.path.join(HERE, "links.json"), encoding="utf-8"))
blur = json.load(open(os.path.join(HERE, "blur.json"), encoding="utf-8"))
shots_p = os.path.join(HERE, "shots.json")
shots = json.load(open(shots_p, encoding="utf-8")) if os.path.exists(shots_p) else {}

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
    png = os.path.join(RAW, f"{i}.png")
    base = [EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=1280,800"]
    # 1차: 가상 시간으로 데이터 로딩을 충분히 기다림. 멈추면 2차: 일반 타임아웃
    for extra, wait in ((["--virtual-time-budget=12000"], 50), (["--timeout=15000"], 40)):
        if os.path.exists(png): os.remove(png)
        prof = tempfile.mkdtemp(prefix="hubshot_")
        try:
            _run(base + extra + [f"--user-data-dir={prof}", f"--screenshot={png}", url], wait)
        finally:
            shutil.rmtree(prof, ignore_errors=True)
        if os.path.exists(png):
            return png
    return None

def process(i, p):
    png = shoot(i, p["u"])
    if not png:
        return i, p["n"], "캡처 실패(이전 이미지 유지)"
    im = Image.open(png).convert("RGB")
    if im.size != (1280, 800): im = im.resize((1280, 800))
    if max(ImageStat.Stat(im.convert("L")).stddev) < 6:
        return i, p["n"], "빈 화면(이전 이미지 유지)"
    for x0, y0, x1, y1 in blur.get(p["n"], []):
        im.paste(im.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(14)), (x0, y0))
    im.resize((640, 400), Image.LANCZOS).save(os.path.join(OUT, f"{i}.jpg"), quality=72, optimize=True)
    shots[p["n"]] = f"shots/{i}.jpg"
    return i, p["n"], "갱신"

t0 = time.time()
with ThreadPoolExecutor(4) as ex:
    for i, n, r in ex.map(lambda t: process(*t), list(enumerate(links))):
        print(f"{i:2d} {n}: {r}")
json.dump(shots, open(shots_p, "w", encoding="utf-8"), ensure_ascii=False)
print(f"capture done {time.time()-t0:.0f}s")
