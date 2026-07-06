#!/usr/bin/env python3
import sys
import time

import paramiko

HOST = "91.184.249.229"
USER = "root"
PASSWORD = sys.argv[1]
LOCAL_SCRIPT = sys.argv[2]
REMOTE_SCRIPT = "/root/remote_fix.sh"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=30)

    sftp = client.open_sftp()
    with open(LOCAL_SCRIPT, "r", encoding="utf-8") as f:
        data = f.read().replace("\r\n", "\n")
    with sftp.file(REMOTE_SCRIPT, "w") as remote:
        remote.write(data)
    sftp.close()

    stdin, stdout, stderr = client.exec_command(
        f"chmod +x {REMOTE_SCRIPT} && bash {REMOTE_SCRIPT}",
        get_pty=True,
    )

    start = time.time()
    while True:
        if stdout.channel.recv_ready():
            sys.stdout.write(stdout.channel.recv(8192).decode("utf-8", errors="replace"))
            sys.stdout.flush()
        if stdout.channel.recv_stderr_ready():
            sys.stderr.write(
                stdout.channel.recv_stderr(8192).decode("utf-8", errors="replace")
            )
            sys.stderr.flush()
        if stdout.channel.exit_status_ready():
            while stdout.channel.recv_ready():
                sys.stdout.write(
                    stdout.channel.recv(8192).decode("utf-8", errors="replace")
                )
            break
        if time.time() - start > 1200:
            print("TIMEOUT", file=sys.stderr)
            return 1
        time.sleep(0.3)

    code = stdout.channel.recv_exit_status()
    client.close()
    print(f"\nEXIT {code}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
