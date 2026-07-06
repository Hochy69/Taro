#!/usr/bin/env python3
import paramiko
import sys

HOST = "91.184.249.229"
USER = "root"
PASSWORD = sys.argv[1]

def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username=USER, password=PASSWORD, timeout=30)

    cmds = [
        "cd /opt/taro && git log -1 --oneline",
        "curl -s -o /dev/null -w 'https:%{http_code}\\n' https://91-184-249-229.sslip.io/",
        "curl -s https://91-184-249-229.sslip.io/assets/index-AmvI89hR.js | grep -o 'Что между вами' | head -1",
        "curl -s https://91-184-249-229.sslip.io/assets/index-AmvI89hR.js | grep -o 'Стоимость проверки' | head -1",
        "docker compose -f /opt/taro/docker-compose.yml exec -T bot python -c \"from app.handlers.commands import start_keyboard; print(start_keyboard().inline_keyboard[1][0].text)\"",
    ]
    for cmd in cmds:
        _, o, e = c.exec_command(cmd)
        out = o.read().decode("utf-8", errors="replace")
        err = e.read().decode("utf-8", errors="replace")
        print(f"=== {cmd} ===")
        print(out or err)
    c.close()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
