#!/usr/bin/env python3
import sys
import time
import paramiko

HOST = "91.184.249.229"
USER = "root"
PASSWORD = sys.argv[1]

FILES = [
    (r"C:\Users\vlad_\Projects\Taro\bot\app\main.py", "/opt/taro/bot/app/main.py"),
]
CMD = "cd /opt/taro && docker compose restart bot && sleep 8 && docker compose logs bot --tail 6"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=30)
    sftp = client.open_sftp()
    for local, remote in FILES:
        with open(local, "r", encoding="utf-8") as f:
            data = f.read().replace("\r\n", "\n")
        with sftp.file(remote, "w") as rf:
            rf.write(data)
    sftp.close()
    stdin, stdout, stderr = client.exec_command(CMD, get_pty=True)
    start = time.time()
    while True:
        if stdout.channel.recv_ready():
            sys.stdout.write(stdout.channel.recv(8192).decode("utf-8", errors="replace"))
        if stdout.channel.exit_status_ready():
            while stdout.channel.recv_ready():
                sys.stdout.write(stdout.channel.recv(8192).decode("utf-8", errors="replace"))
            break
        if time.time() - start > 120:
            return 1
        time.sleep(0.3)
    client.close()
    return stdout.channel.recv_exit_status()


if __name__ == "__main__":
    raise SystemExit(main())
