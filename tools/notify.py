"""메일 발송: 마케팅OS 서버가 쓰는 Brevo 설정을 Railway에서 실행할 때마다 읽어 사용한다(파일에 저장하지 않음)."""
import json, os, shutil, subprocess, urllib.request

MARKETING_DIR = r"C:\Users\123\Desktop\AUTO\마케팅os"
SERVICE = "yuseong-marketing-os-review"


def _vars():
    RW = shutil.which("railway") or "C:/Users/123/AppData/Roaming/npm/railway.CMD"
    r = subprocess.run([RW, "variables", "-s", SERVICE, "--json"], cwd=MARKETING_DIR,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    d = json.loads(r.stdout)
    return d["BREVO_API_KEY"], d["EMAIL_FROM"], d.get("EMAIL_TO", "sinijini1@naver.com")


def send_mail(subject: str, body: str) -> bool:
    try:
        key, frm, to = _vars()
        req = urllib.request.Request(
            "https://api.brevo.com/v3/smtp/email",
            data=json.dumps({"sender": {"email": frm, "name": "유클 업무 허브"}, "to": [{"email": to}],
                             "subject": subject, "textContent": body}, ensure_ascii=False).encode("utf-8"),
            headers={"api-key": key, "content-type": "application/json", "accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return 200 <= resp.status < 300
    except Exception as e:  # 알림 실패가 점검 자체를 막지 않게
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "monitor.log"), "a", encoding="utf-8") as f:
            f.write(f"메일 발송 실패: {type(e).__name__}\n")
        return False


if __name__ == "__main__":
    print("sent" if send_mail("[허브] 알림 테스트", "서버 감시 알림 메일 테스트입니다.") else "failed")
