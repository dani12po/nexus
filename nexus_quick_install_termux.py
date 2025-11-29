# nexus_quick_install_termux.py (update 2025-11)
"""Helper buat jalanin Nexus CLI di Termux (native / Ubuntu proot).

Bisa di-import dari bot.py ATAU dijalankan langsung:

  python nexus_quick_install_termux.py preflight
  python nexus_quick_install_termux.py start --node-id <ID>
  python nexus_quick_install_termux.py status
  python nexus_quick_install_termux.py logs
  python nexus_quick_install_termux.py stop
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path
import re

PROOT_DISTRO = "ubuntu"
PROOT_RUN_DIR = "$HOME/.nexus-run"   # di dalam Ubuntu (proot)
PROOT_BIN = "$HOME/.nexus/bin/nexus-network"


# =======================
# Util
# =======================
def run(cmd, env=None, print_cmd=True):
    """Jalankan perintah shell, tangkap stdout/stderr. Return (ok, out, err, code)."""
    if print_cmd:
        print(f"\n>>> {cmd}")
    p = subprocess.run(
        cmd, shell=True, text=True, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    ok = (p.returncode == 0)
    if not ok:
        print(f"[!] Command gagal (exit={p.returncode}): {cmd}")
        if p.stdout:
            print("--- stdout ---")
            print(p.stdout.strip())
        if p.stderr:
            print("--- stderr ---")
            print(p.stderr.strip())
    return ok, (p.stdout or ""), (p.stderr or ""), p.returncode


def is_command_available(name: str) -> bool:
    return shutil.which(name) is not None


def is_termux() -> bool:
    return is_command_available("pkg")


def pkg_ensure(pkgs):
    if not is_termux():
        return
    run("pkg update -y")
    for p in pkgs:
        if is_command_available(p):
            continue
        ok, *_ = run(f"dpkg -s {p} >/dev/null 2>&1", print_cmd=False)
        if not ok:
            run(f"pkg install -y {p}")


def append_once(file: Path, text: str):
    file.parent.mkdir(parents=True, exist_ok=True)
    current = ""
    if file.exists():
        try:
            current = file.read_text(encoding="utf-8")
        except Exception:
            current = ""
    if text.strip() not in current:
        with file.open("a", encoding="utf-8") as f:
            f.write("\n" + text.rstrip() + "\n")


def shell_rc_candidates():
    h = Path.home()
    return [h / ".zshrc", h / ".bashrc", h / ".profile"]


def ensure_path_to_nexus_bin():
    nexus_bin = Path.home() / ".nexus" / "bin"
    if not nexus_bin.exists():
        return False
    export_line = 'export PATH="$HOME/.nexus/bin:$PATH"'
    for rc in shell_rc_candidates():
        append_once(rc, export_line)
    os.environ["PATH"] = f"{str(nexus_bin)}:" + os.environ.get("PATH", "")
    return True


def ensure_network():
    ok, *_ = run("curl -sSfI https://cli.nexus.xyz", print_cmd=False)
    return ok


# =======================
# Nexus CLI (native)
# =======================
def install_cli_termux():
    """Coba install CLI di Termux; kalau tidak kompatibel, test_cli() akan False dan kita fallback proot."""
    if not is_termux():
        return False
    if test_cli():
        print("[=] Nexus CLI sudah tersedia, lewati instalasi.")
        return True

    pkg_ensure(["curl"])
    if not ensure_network():
        print("[!] Tidak bisa akses https://cli.nexus.xyz. Periksa koneksi.")
        return False

    run("curl https://cli.nexus.xyz/ | sh")
    ensure_path_to_nexus_bin()

    if test_cli():
        print("[+] Nexus CLI terpasang.")
        return True
    print("[x] Nexus CLI belum terdeteksi setelah instalasi.")
    return False


def _pick_cmd_path() -> str:
    if is_command_available("nexus-network"):
        return "nexus-network"
    candidate = Path.home() / ".nexus" / "bin" / "nexus-network"
    if candidate.exists():
        return f'"{candidate}"'
    return "nexus-network"


def test_cli() -> bool:
    """TRUE jika binari usable (bukan sekadar ada). Hindari kasus 'Bad system call'."""
    cmd = _pick_cmd_path()
    ok, out, err, code = run(f"{cmd} --version", print_cmd=False)
    text = (out + err).lower()
    if (not ok) or code < 0 or ("bad system call" in text) or ("not executable" in text):
        return False
    return True


def _show_help_snippet():
    cmd = _pick_cmd_path()
    run(f"{cmd} --help", print_cmd=False)
    run(f"{cmd} start --help", print_cmd=False)
    run(f"{cmd} node start --help", print_cmd=False)


def start_node_smart(node_id: str) -> bool:
    """Coba beberapa variasi perintah start (native)."""
    ensure_path_to_nexus_bin()
    cmd_base = _pick_cmd_path()

    if len(node_id) < 10:
        print(f"[?] Peringatan: node-id '{node_id}' tampak pendek. Pastikan benar.")

    variants = [
        f'{cmd_base} start --node-id "{node_id}"',
        f'{cmd_base} start --node_id "{node_id}"',
        f'{cmd_base} start --nodeId "{node_id}"',
        f'{cmd_base} start -n "{node_id}"',
        f'{cmd_base} node start --node-id "{node_id}"',
        f'{cmd_base} node start --node_id "{node_id}"',
        f'{cmd_base} node start --nodeId "{node_id}"',
        f'{cmd_base} node start -n "{node_id}"',
        f'{cmd_base} run --node-id "{node_id}"',
        f'{cmd_base} run --node_id "{node_id}"',
    ]

    ok_h, help_out, *_ = run(f"{cmd_base} --help", print_cmd=False)
    if ok_h and re.search(r"\bnode\s+start\b", help_out, re.IGNORECASE):
        variants = [v for v in variants if "node start" in v] + [v for v in variants if "node start" not in v]

    for cmd in variants:
        ok, out, err, _ = run(cmd)
        if ok:
            print("[✓] Node berhasil dijalankan dengan:", cmd)
            return True
        joined = (out + "\n" + err).lower()
        if any(k in joined for k in ["login", "authenticate", "authorization"]):
            print("[!] CLI minta login. Lihat help berikut lalu login, kemudian jalankan ulang.")
            _show_help_snippet()
    _show_help_snippet()
    return False


# =======================
# PROOT (Ubuntu)
# =======================
def ensure_proot_distro() -> bool:
    if not is_termux():
        return False
    if is_command_available("proot-distro"):
        return True
    pkg_ensure(["proot-distro"])
    return is_command_available("proot-distro")


def _proot(cmd_inside: str):
    """Jalankan perintah di dalam Ubuntu (proot)."""
    return run(
        f'proot-distro login {PROOT_DISTRO} -- bash -lc "{cmd_inside}"'
    )


def start_in_proot_detached(node_id: str):
    """Start node di proot Ubuntu dalam mode detached (nohup), simpan PID & LOG."""
    if not ensure_proot_distro():
        print("[x] proot-distro belum siap / bukan Termux.")
        return

    # Install Ubuntu (idempotent) dan dependency, lalu jalankan di background
    run(f"proot-distro install {PROOT_DISTRO} || true")

    cmd = f'''
set -e
export DEBIAN_FRONTEND=noninteractive
apt-get update -yq
apt-get install -yq curl ca-certificates procps
update-ca-certificates || true

# install Nexus CLI
curl -fsSL https://cli.nexus.xyz/ -o /tmp/nexus_install.sh
bash /tmp/nexus_install.sh

export PATH="$HOME/.nexus/bin:$PATH"
mkdir -p {PROOT_RUN_DIR}

# jalankan background + PID + LOG
nohup {PROOT_BIN} start --node-id "{node_id}" > {PROOT_RUN_DIR}/node.log 2>&1 &
echo $! > {PROOT_RUN_DIR}/node.pid

sleep 1
if [ -s {PROOT_RUN_DIR}/node.pid ] && ps -p $(cat {PROOT_RUN_DIR}/node.pid) >/dev/null 2>&1; then
  echo "[✓] Node berjalan (PID $(cat {PROOT_RUN_DIR}/node.pid))."
  echo "[i] Log: {PROOT_RUN_DIR}/node.log"
else
  echo "[x] Gagal menjalankan node di background. Cek log jika ada."
  [ -f {PROOT_RUN_DIR}/node.log ] && tail -n 80 {PROOT_RUN_DIR}/node.log || true
  exit 1
fi
'''
    _proot(cmd)


def proot_status():
    """Cek status proses di proot."""
    cmd = f'''
PID_FILE={PROOT_RUN_DIR}/node.pid
if [ -s "$PID_FILE" ]; then
  PID=$(cat "$PID_FILE")
  if ps -p "$PID" >/dev/null 2>&1; then
    echo "STATUS: RUNNING (PID $PID)"
  else
    echo "STATUS: NOT RUNNING (pid file ada, proses tidak aktif)"
  fi
else
  echo "STATUS: NOT RUNNING (pid file tidak ada)"
fi
'''
    _proot(cmd)


def proot_logs(tail_n: int = 80):
    """Tampilkan log terakhir dari node di proot."""
    cmd = f'''
LOG={PROOT_RUN_DIR}/node.log
if [ -f "$LOG" ]; then
  echo "=== tail -n {tail_n} $LOG ==="
  tail -n {tail_n} "$LOG"
else
  echo "[i] Belum ada log: $LOG"
fi
'''
    _proot(cmd)


def proot_stop():
    """Hentikan node di proot (berdasarkan PID)."""
    cmd = f'''
PID_FILE={PROOT_RUN_DIR}/node.pid
if [ -s "$PID_FILE" ]; then
  PID=$(cat "$PID_FILE")
  if ps -p "$PID" >/dev/null 2>&1; then
    kill "$PID" || true
    sleep 1
    if ps -p "$PID" >/dev/null 2>&1; then
      kill -9 "$PID" || true
    fi
    echo "[✓] Node dihentikan."
  else
    echo "[i] Proses tidak aktif. Hapus pid file."
  fi
  rm -f "$PID_FILE"
else
  echo "[i] Tidak ada pid file. Node kemungkinan tidak berjalan."
fi
'''
    _proot(cmd)


# =======================
# Preflight
# =======================
def preflight_ensure_ready():
    """Termux: coba install CLI (boleh gagal), siapkan proot-distro. Non-Termux: cek CLI saja."""
    status = {"termux": is_termux(), "cli_ready": False, "proot_ready": False}
    if status["termux"]:
        status["cli_ready"] = install_cli_termux()
        status["proot_ready"] = ensure_proot_distro()
    else:
        status["cli_ready"] = test_cli()
    print(f"[i] Status preflight: {status}")
    return status


# =======================
# CLI entrypoint (optional)
# =======================
def _parse_cli(argv=None):
    import argparse

    parser = argparse.ArgumentParser(
        description="Helper Nexus CLI untuk Termux (native + Ubuntu proot)"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_pref = sub.add_parser("preflight", help="Cek & siapkan environment saja")
    p_pref.set_defaults(cmd="preflight")

    p_start = sub.add_parser("start", help="Start node dengan node-id (native/proot)")
    p_start.add_argument("--node-id", required=True, help="Node ID dari dashboard Nexus")
    p_start.set_defaults(cmd="start")

    p_status = sub.add_parser("status", help="Cek status node (proot/native)")
    p_status.set_defaults(cmd="status")

    p_logs = sub.add_parser("logs", help="Tail log node (proot)")
    p_logs.add_argument("--lines", type=int, default=80, help="Jumlah baris log (default: 80)")
    p_logs.set_defaults(cmd="logs")

    p_stop = sub.add_parser("stop", help="Stop node (proot/native)")
    p_stop.set_defaults(cmd="stop")

    return parser.parse_args(argv)


def _main_cli(argv=None):
    args = _parse_cli(argv)
    status = preflight_ensure_ready()
    termux = status["termux"]
    cli_ready = status["cli_ready"]
    proot_ready = status["proot_ready"]

    if args.cmd == "preflight":
        # sudah di-print di preflight_ensure_ready()
        return

    if args.cmd == "start":
        node_id = args.node_id
        if termux and not cli_ready and proot_ready:
            start_in_proot_detached(node_id)
            return
        # coba native dulu
        ok = start_node_smart(node_id)
        if not ok and termux and proot_ready:
            print("[i] Fallback ke Ubuntu proot ...")
            start_in_proot_detached(node_id)
        return

    if args.cmd == "status":
        if termux and proot_ready:
            proot_status()
        else:
            cmd = _pick_cmd_path()
            run(f"{cmd} status || {cmd} ps || {cmd} --version")
        return

    if args.cmd == "logs":
        if termux and proot_ready:
            proot_logs(args.lines)
        else:
            print("[i] Logs hanya didukung otomatis untuk mode proot di Termux.")
        return

    if args.cmd == "stop":
        if termux and proot_ready:
            proot_stop()
        else:
            cmd = _pick_cmd_path()
            run(f"{cmd} stop || true")
        return


if __name__ == "__main__":
    _main_cli(sys.argv[1:])
