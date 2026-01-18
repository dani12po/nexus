#!/usr/bin/env python3
"""
Nexus CLI Node — super-simpel wrapper
- Mengikuti langkah resmi: curl https://cli.nexus.xyz/ | sh → start/register
- Otomatis deteksi Termux dan jalankan via Ubuntu proot (glibc)
- Pakai:  python bot.py --node-id <ID>
         python bot.py --wallet <WALLET_ADDRESS>
Opsional: --login  --status  --stop
"""
import os, sys, subprocess, shlex


def run(cmd: str) -> None:
    print(f"$ {cmd}")
    rc = subprocess.run(cmd, shell=True)
    if rc.returncode != 0:
        sys.exit(rc.returncode)


def is_termux() -> bool:
    prefix = os.environ.get("PREFIX", "")
    return prefix.endswith("/usr") and "com.termux" in prefix


def start_nexus_linux(node_id=None, wallet=None, login=False, status=False, stop=False):
    home = os.path.expanduser("~")
    nn = os.path.join(home, ".nexus", "bin", "nexus-network")

    # Pastikan CLI terpasang (sesuai docs resmi)
    if not os.path.isfile(nn):
        run("curl https://cli.nexus.xyz/ | sh")

    if login:
        run(f"{shlex.quote(nn)} login --no-open")
        return
    if status:
        run(f"{shlex.quote(nn)} status || {shlex.quote(nn)} ps || {shlex.quote(nn)} --version")
        return
    if stop:
        run(f"{shlex.quote(nn)} stop || true")
        return

    if node_id:
        run(f"{shlex.quote(nn)} start --node-id {shlex.quote(node_id)}")
    elif wallet:
        run(f"{shlex.quote(nn)} register-user --wallet-address {shlex.quote(wallet)}")
        run(f"{shlex.quote(nn)} register-node")
        run(f"{shlex.quote(nn)} start")
    else:
        print("Usage: python bot.py --node-id <ID>  |  --wallet <WALLET_ADDRESS>\nOpsional: --login, --status, --stop")
        sys.exit(2)


def start_nexus_termux(node_id=None, wallet=None, login=False, status=False, stop=False):
    # Persiapan Termux → Ubuntu proot
    run("pkg update -y && pkg install -y proot-distro curl")
    run("proot-distro install ubuntu || true")

    inner_lines = [
        "set -e",
        "apt-get update -y && apt-get install -y curl ca-certificates",
        "curl https://cli.nexus.xyz/ | sh",
        "echo 'export PATH=\"$HOME/.nexus/bin:$PATH\"' >> ~/.bashrc",
        ". ~/.bashrc",
    ]

    if login:
        inner_lines.append("$HOME/.nexus/bin/nexus-network login --no-open")
    elif status:
        inner_lines.append("$HOME/.nexus/bin/nexus-network status || $HOME/.nexus/bin/nexus-network ps || $HOME/.nexus/bin/nexus-network --version")
    elif stop:
        inner_lines.append("$HOME/.nexus/bin/nexus-network stop || true")
    elif node_id:
        inner_lines.append(f"$HOME/.nexus/bin/nexus-network start --node-id {shlex.quote(node_id)}")
    elif wallet:
        inner_lines.append(f"$HOME/.nexus/bin/nexus-network register-user --wallet-address {shlex.quote(wallet)}")
        inner_lines.append("$HOME/.nexus/bin/nexus-network register-node")
        inner_lines.append("$HOME/.nexus/bin/nexus-network start")
    else:
        inner_lines.append('echo "Set --node-id <ID> atau --wallet <ADDR>" && exit 2')

    inner_script = "\n".join(inner_lines)
    cmd = "proot-distro login ubuntu -- bash -lc " + shlex.quote(inner_script)
    run(cmd)


def parse_args(argv):
    node_id = None
    wallet = None
    login = False
    status = False
    stop = False

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--node-id" and i + 1 < len(argv):
            node_id = argv[i + 1]
            i += 1
        elif a == "--wallet" and i + 1 < len(argv):
            wallet = argv[i + 1]
            i += 1
        elif a == "--login":
            login = True
        elif a == "--status":
            status = True
        elif a == "--stop":
            stop = True
        else:
            print(f"Unknown arg: {a}")
            sys.exit(2)
        i += 1

    # Fallback dari env var
    node_id = node_id or os.getenv("NODE_ID")
    wallet = wallet or os.getenv("WALLET_ADDRESS")
    return node_id, wallet, login, status, stop


if __name__ == "__main__":
    node_id, wallet, login, status, stop = parse_args(sys.argv[1:])
    if is_termux():
        start_nexus_termux(node_id, wallet, login, status, stop)
    else:
        start_nexus_linux(node_id, wallet, login, status, stop)
