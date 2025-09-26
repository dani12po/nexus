# nexus_quick_install_termux.py
import os
import subprocess
import shutil
from pathlib import Path
import re

# =======================
# Util dasar
# =======================
def run(cmd, env=None, print_cmd=True):
    """Jalankan perintah shell, selalu tangkap stdout/stderr. Kembali (ok, out, err, code)."""
    if print_cmd:
        print(f"\n>>> {cmd}")
    p = subprocess.run(
        cmd,
        shell=True,
        text=True,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
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

def is_command_available(cmd_name: str) -> bool:
    return shutil.which(cmd_name) is not None

def is_termux() -> bool:
    return is_command_available("pkg")

def pkg_ensure(pkgs):
    """Pastikan paket-paket terpasang di Termux (idempotent)."""
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
    """Tambahkan baris ke file rc bila belum ada (idempotent)."""
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
    """Inject ~/.nexus/bin ke PATH (rc files + proses saat ini)."""
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
    """Coba install Nexus CLI di Termux. Jika binari tidak kompatibel, test_cli() akan mendeteksi dan kita fallback."""
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
    """Kembalikan path/command 'nexus-network' terbaik (absolute jika ada di ~/.nexus/bin)."""
    if is_command_available("nexus-network"):
        return "nexus-network"
    candidate = Path.home() / ".nexus" / "bin" / "nexus-network"
    if candidate.exists():
        return f'"{candidate}"'
    return "nexus-network"

def test_cli() -> bool:
    """Cek apakah binari Nexus CLI *bisa dipakai* (bukan sekadar ada), hindari kasus 'Bad system call' (exit negatif)."""
    cmd = _pick_cmd_path()
    ok, out, err, code = run(f"{cmd} --version")
    text = (out + err).lower()
    if (not ok) or code < 0 or ("bad system call" in text) or ("not executable" in text):
        return False
    return True

def _show_help_snippet():
    cmd = _pick_cmd_path()
    run(f"{cmd} --help")
    # Best-effort untuk subcommand yang umum
    run(f"{cmd} start --help", print_cmd=False)
    run(f"{cmd} node start --help", print_cmd=False)

def start_node_smart(node_id: str) -> bool:
    """
    Coba berbagai variasi perintah start. Return True jika salah satu berhasil.
    Cetak stdout/stderr saat gagal untuk diagnosa.
    """
    ensure_path_to_nexus_bin()
    cmd_base = _pick_cmd_path()

    if len(node_id) < 10:
        print(f"[?] Peringatan: node-id '{node_id}' tampak pendek. Pastikan format sesuai.")

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
        ok, out, err, code = run(cmd)
        if ok:
            print("[✓] Node berhasil dijalankan dengan:", cmd)
            return True

        joined = (out + "\n" + err).lower()
        if any(key in joined for key in ["login", "authenticate", "authorization"]):
            print("[!] CLI tampaknya meminta autentikasi/login sebelum start. Jalankan perintah login sesuai help, lalu ulangi.")
            _show_help_snippet()

    _show_help_snippet()
    return False

# =======================
# Fallback Ubuntu (proot)
# =======================
def ensure_proot_distro() -> bool:
    """Pastikan `proot-distro` ada (untuk menjalankan Ubuntu di Termux)."""
    if not is_termux():
        return False
    if is_command_available("proot-distro"):
        return True
    pkg_ensure(["proot-distro"])
    return is_command_available("proot-distro")

def start_in_proot(node_id: str):
    """Jalankan node di dalam Ubuntu (proot-distro) — idempotent."""
    if not ensure_proot_distro():
        print("[x] proot-distro belum siap atau bukan Termux.")
        return

    # Install Ubuntu (idempotent) & jalankan Nexus CLI di dalamnya
    run("proot-distro install ubuntu || true")
    run((
        'proot-distro login ubuntu -- bash -lc "'
        'set -e; '
        'apt-get update -y && apt-get install -y curl ca-certificates; '
        'curl https://cli.nexus.xyz/ | sh; '
        'export PATH=\\"$HOME/.nexus/bin:$PATH\\"; '
        f'nexus-network start --node-id \\"{node_id}\\""'
    ))

# =======================
# Orkestrasi preflight
# =======================
def preflight_ensure_ready():
    """
    - Jika Termux: coba install CLI (boleh gagal jika binari tidak kompatibel), dan siapkan proot-distro.
    - Jika non-Termux: cek keberadaan CLI saja.
    """
    status = {"termux": is_termux(), "cli_ready": False, "proot_ready": False}

    if status["termux"]:
        status["cli_ready"] = install_cli_termux()  # akan False saat kasus 'bad system call'
        status["proot_ready"] = ensure_proot_distro()
    else:
        status["cli_ready"] = test_cli()

    print(f"[i] Status preflight: {status}")
    return status
