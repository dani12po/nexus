#!/usr/bin/env python3
"""Nexus CLI Node — wrapper Linux + Termux (update 2025-11)

- Linux biasa  : langsung pakai ~/.nexus/bin/nexus-network (atau nexus-network di PATH)
- Termux       : pakai helper nexus_quick_install_termux:
                 * cek & install CLI kalau perlu
                 * kalau CLI tidak kompatibel (Bad system call, dll) → pakai Ubuntu proot

Usage:
  python bot.py --node-id <NODE_ID>

Opsional:
  --wallet <WALLET_ADDRESS>   # sekali pakai untuk register-user + register-node (lebih enak dari Linux biasa)
  --login                     # nexus-network login --no-open
  --status                    # cek status node
  --stop                      # stop node
  --logs                      # (Termux + proot) tail log node

Bisa juga pakai env:
  NODE_ID / WALLET_ADDRESS
"""
import os
import sys
import subprocess
import shlex
import shutil

try:
    import nexus_quick_install_termux as nq
except Exception:
    nq = None


def run(cmd: str) -> None:
    """Jalankan perintah shell sederhana + exit kalau gagal."""
    print(f"$ {cmd}")
    rc = subprocess.run(cmd, shell=True)
    if rc.returncode != 0:
        sys.exit(rc.returncode)


def is_termux() -> bool:
    """Deteksi Termux seaman mungkin."""
    if shutil.which("pkg"):
        return True
    prefix = os.environ.get("PREFIX", "")
    return prefix.endswith("/usr") and "com.termux" in prefix


def pick_nexus_binary() -> str:
    """Cari binari nexus-network di Linux biasa."""
    path_cmd = shutil.which("nexus-network")
    if path_cmd:
        return shlex.quote(path_cmd)

    home = os.path.expanduser("~")
    nn = os.path.join(home, ".nexus", "bin", "nexus-network")
    if not os.path.isfile(nn):
        # install sesuai docs resmi
        run("curl https://cli.nexus.xyz/ | sh")
    return shlex.quote(nn)


def start_nexus_linux(node_id=None, wallet=None, login=False, status=False, stop=False, logs: bool = False):
    """Jalankan nexus-network di Linux biasa (bukan Termux)."""
    nn_cmd = pick_nexus_binary()

    if login:
        run(f"{nn_cmd} login --no-open")
        return
    if status:
        run(f"{nn_cmd} status || {nn_cmd} ps || {nn_cmd} --version")
        return
    if stop:
        run(f"{nn_cmd} stop || true")
        return
    if logs:
        print("[-] Fitur --logs hanya didukung otomatis untuk mode Termux + proot.")
        print("    Di Linux biasa, cek log sesuai cara deploy kamu (systemd/journalctl, docker, dsb).")
        return

    if node_id:
        run(f"{nn_cmd} start --node-id {shlex.quote(node_id)}")
    elif wallet:
        # sekali pakai: register-user + register-node + start
        run(f"{nn_cmd} register-user --wallet-address {shlex.quote(wallet)}")
        run(f"{nn_cmd} register-node")
        run(f"{nn_cmd} start")
    else:
        print_usage()
        sys.exit(2)


def start_nexus_termux(node_id=None, wallet=None, login=False, status=False, stop=False, logs: bool = False):
    """Mode Termux: gunakan helper nexus_quick_install_termux."""
    if nq is None:
        print("[x] Modul nexus_quick_install_termux tidak ditemukan.")
        print("    Pastikan file nexus_quick_install_termux.py ada di folder yang sama dengan bot.py.")
        sys.exit(1)

    status_pre = nq.preflight_ensure_ready()
    termux = status_pre.get("termux", False)
    cli_ready = status_pre.get("cli_ready", False)
    proot_ready = status_pre.get("proot_ready", False)

    if not termux:
        # fallback: seharusnya tidak kejadian, tapi aman saja
        return start_nexus_linux(node_id, wallet, login, status, stop, logs)

    # LOGIN
    if login:
        if cli_ready:
            cmd = nq._pick_cmd_path()
            nq.run(f"{cmd} login --no-open")
        else:
            print("[!] Login sebaiknya dilakukan dari environment yang punya browser (PC / WSL).")
        return

    # STATUS
    if status:
        if proot_ready:
            nq.proot_status()
        elif cli_ready:
            cmd = nq._pick_cmd_path()
            nq.run(f"{cmd} status || {cmd} ps || {cmd} --version")
        else:
            print("[i] Belum ada node yang jalan / CLI belum siap.")
        return

    # LOGS
    if logs:
        if proot_ready:
            nq.proot_logs()
        else:
            print("[i] Fitur logs otomatis hanya tersedia kalau node dijalankan via proot Ubuntu.")
        return

    # STOP
    if stop:
        if proot_ready:
            nq.proot_stop()
        elif cli_ready:
            cmd = nq._pick_cmd_path()
            nq.run(f"{cmd} stop || true")
        else:
            print("[i] Tidak ada node yang bisa di-stop.")
        return

    # START via node-id
    if node_id:
        if cli_ready:
            ok = nq.start_node_smart(node_id)
            if ok:
                return
            if proot_ready:
                print("[i] Gagal start native, fallback ke Ubuntu proot...")
                nq.start_in_proot_detached(node_id)
                return
            print("[x] Gagal start node native, dan proot belum siap.")
        elif proot_ready:
            nq.start_in_proot_detached(node_id)
        else:
            print("[x] Nexus CLI belum siap di Termux; gagal menyiapkan proot.")
        return

    # --wallet di Termux: tidak di-otomasi penuh
    if wallet:
        print("[!] Mode --wallet di Termux belum di-otomasi.")
        print("    Disarankan register-user & register-node dari Linux/PC,")
        print("    lalu di Termux cukup pakai --node-id yang sudah jadi.")
        return

    print_usage()


def parse_args(argv):
    node_id = None
    wallet = None
    login = False
    status = False
    stop = False
    logs = False

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
        elif a == "--logs":
            logs = True
        else:
            print(f"Unknown arg: {a}")
            print_usage()
            sys.exit(2)
        i += 1

    # Fallback dari env var
    node_id = node_id or os.getenv("NODE_ID")
    wallet = wallet or os.getenv("WALLET_ADDRESS")
    return node_id, wallet, login, status, stop, logs


def print_usage():
    print(
        "Usage:\\n"
        "  python bot.py --node-id <ID>\\n"
        "  python bot.py --wallet <WALLET_ADDRESS>\\n"
        "Opsional:\\n"
        "  --login   --status   --stop   --logs\\n"
        "Atau pakai env: NODE_ID / WALLET_ADDRESS\\n"
    )


if __name__ == "__main__":
    node_id, wallet, login, status, stop, logs = parse_args(sys.argv[1:])
    if is_termux():
        start_nexus_termux(node_id, wallet, login, status, stop, logs)
    else:
        start_nexus_linux(node_id, wallet, login, status, stop, logs)
