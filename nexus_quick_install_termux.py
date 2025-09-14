# nexus_quick_install_termux.py
import subprocess
import os

def run(cmd, check=True, capture=False):
    print(f"\n>>> {cmd}")
    result = subprocess.run(
        cmd, shell=True, text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None
    )
    if check and result.returncode != 0:
        print(f"[!] Command gagal: {cmd}")
        if capture:
            print("stdout:", result.stdout)
            print("stderr:", result.stderr)
        return None
    return result.stdout if capture else None

def install_cli_termux():
    run("pkg update -y && pkg upgrade -y")
    run("pkg install -y curl")
    run("curl https://cli.nexus.xyz/ | sh")

def source_shell():
    rc_file = os.path.expanduser("~/.bashrc")
    if os.path.exists(os.path.expanduser("~/.zshrc")):
        rc_file = os.path.expanduser("~/.zshrc")
    if os.path.exists(rc_file):
        run(f"source {rc_file}", check=False)
        print(f"[+] Shell config di-load dari {rc_file}")

def test_cli():
    out = run("nexus-network --help", check=False, capture=True)
    return out and "Usage" in out

def fallback_proot(node_id):
    run("pkg install -y proot-distro")
    run("proot-distro install ubuntu || true")
    run(
        f'proot-distro login ubuntu -- bash -c "apt update && apt install -y curl && '
        f'curl https://cli.nexus.xyz/ | sh && source ~/.bashrc && '
        f'nexus-network start --node-id {node_id}"'
    )

def start_node(node_id):
    run(f"nexus-network start --node-id {node_id}")
