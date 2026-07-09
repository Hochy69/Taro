#!/usr/bin/env python3
import sys
import time
import paramiko

HOST = "91.184.249.229"
USER = "root"
PASSWORD = sys.argv[1]

FILES = [
    (
        r"C:\Users\vlad_\Projects\Taro\backend\app\application\services\admin_stats_service.py",
        "/opt/taro/backend/app/application/services/admin_stats_service.py",
    ),
    (
        r"C:\Users\vlad_\Projects\Taro\backend\tests\test_admin_stats.py",
        "/opt/taro/backend/tests/test_admin_stats.py",
    ),
    (
        r"C:\Users\vlad_\Projects\Taro\frontend\src\pages\admin\AdminDashboard.tsx",
        "/opt/taro/frontend/src/pages/admin/AdminDashboard.tsx",
    ),
    (
        r"C:\Users\vlad_\Projects\Taro\scripts\remote_fix_admin_stats.sh",
        "/opt/taro/scripts/remote_fix_admin_stats.sh",
    ),
]


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
        print(f"uploaded {remote}")
    sftp.close()

    cmd = "chmod +x /opt/taro/scripts/remote_fix_admin_stats.sh && bash /opt/taro/scripts/remote_fix_admin_stats.sh"
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
    start = time.time()
    while True:
        if stdout.channel.recv_ready():
            sys.stdout.write(stdout.channel.recv(8192).decode("utf-8", errors="replace"))
            sys.stdout.flush()
        if stdout.channel.exit_status_ready():
            while stdout.channel.recv_ready():
                sys.stdout.write(stdout.channel.recv(8192).decode("utf-8", errors="replace"))
            break
        if time.time() - start > 600:
            print("TIMEOUT", file=sys.stderr)
            return 1
        time.sleep(0.3)
    code = stdout.channel.recv_exit_status()
    client.close()
    print(f"\nEXIT {code}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
