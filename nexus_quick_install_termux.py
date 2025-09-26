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
    """Jalankan perintah shell, selalu tangkap stdout/stderr. Kembalikan (ok, stdout, stderr, code)."""
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
    if not is_termux():
        return
    run("pkg update -y")
    for p in pkgs:
        # Jika sudah ada bin-nya, lewati
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
    # Terapkan ke proses saat ini juga (agar langsung terpakai)
    os.environ["PATH"] = f"{str(nexus_bin)}:" + os.environ.get("PATH", "")
    return True

def ensure_network():
    ok, *_ = run("curl -sSfI https://cli.nexus.xyz", print_cmd=False)
    return ok

# =======================
# Nexus CLI
# =======================
def install_cli_termux():
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

def test_cli():
    # Cek via which
    if is_command_available("nexus-network"):
        ok, out, _, _ = run("nexus-network --version")
        return ok
    # Cek di path default installer
    candidate = Path.home() / ".nexus" / "bin" / "nexus-network"
    if candidate.exists():
        ok, *_ = run(f'"{candidate}" --version')
        return ok
    return False

def _nexus_bin_cmd():
    """Kembalikan string command untuk memanggil nexus-network (absolute jika perlu)."""
    if is_command_available("nexus-network"):
        return "nexus-network"
    candidate = Path.home() / ".nexus" / "bin" / "nexus-network"
    if candidate.exists():
        return f'"{candidate}"'
    return "nexus-network"  # fallback, biar error ter-print jelas

def _show_help_snippet():
    cmd = _nexus_bin_cmd()
    run(f"{cmd} --help")
    # Coba bantuan sub-command jika ada
    run(f"{cmd} start --help", print_cmd=False)
    run(f"{cmd} node start --help", print_cmd=False)

def start_node_smart(node_id: str) -> bool:
    """
    Coba berbagai variasi perintah start. Cetak error nyata jika gagal.
    Return True jika salah satu variasi sukses.
    """
    env = os.environ.copy()
    ensure_path_to_nexus_bin()
    cmd_base = _nexus_bin_cmd()

    # Validasi sederhana: beri peringatan jika node_id terlihat terlalu pendek
    if len(node_id) < 10:
        print(f"[?] Peringatan: node-id '{node_id}' tampak pendek. Pastikan formatnya sesuai yang diminta CLI.")

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

    # Jika help menyebut pola tertentu, bisa dinaikkan prioritasnya (heuristik ringan)
    ok_h, help_out, help_err, _ = run(f"{cmd_base} --help", print_cmd=False)
    if ok_h:
        if re.search(r"\bnode\s+start\b", help_out, re.IGNORECASE):
            # Prioritaskan varian yang mengandung "node start"
            variants = [v for v in variants if "node start" in v] + [v for v in variants if "node start" not in v]

    # Eksekusi berurutan hingga satu berhasil
    for cmd in variants:
        ok, out, err, code = run(cmd, env=env)
        if ok:
            print("[✓] Node berhasil dijalankan dengan:", cmd)
            return True

        # Deteksi kasus umum dan beri petunjuk singkat
        joined = f"{out}\n{err}".lower()
        if "unknown option" in joined or "unknown flag" in joined or "unrecognized option" in joined:
            # lanjut coba varian lain
            continue
        if "unknown command" in joined:
            continue
        if "login" in joined or "authenticate" in joined or "authorization" in joined:
            print("[!] CLI tampaknya meminta autentikasi/login sebelum start. Coba perintah login sesuai help, lalu jalankan ulang.")
            _show_help_snippet()
            # tetap lanjut ke varian lain; jika tetap gagal, user sudah dapat petunjuk.
            continue

    # Semua varian gagal
    _show_help_snippet()
    return False

# =======================
# Fallback Ubuntu (proot)
# =======================
def ensure_proot_distro() -> bool:
    if not is_termux():
        return False
    if is_command_available("proot-distro"):
        return True
    pkg_ensure(["proot-distro"])
    return is_command_available("proot-distro")

def start_in_proot(node_id: str):
    if not ensure_proot_distro():
        print("[x] proot-distro belum siap.")
        return
    # Install Ubuntu (idempotent) lalu pasang Nexus CLI di dalamnya
    run("proot-distro install ubuntu || true")
    run((
        'proot-distro login ubuntu -- bash -lc "'
        'apt-get update -y && apt-get install -y curl && '
        'curl https://cli.nexus.xyz/ | sh && '
        f'export PATH=\\"$HOME/.nexus/bin:$PATH\\"; '
        f'nexus-network start --node-id \\"{node_id}\\""'
    ))

# =======================
# Orkestrasi preflight
# =======================
def preflight_ensure_ready():
    status = {"termux": is_termux(), "cli_ready": False, "proot_ready": False}

    if is_termux():
        status["cli_ready"] = install_cli_termux()
        status["proot_ready"] = ensure_proot_distro()
    else:
        status["cli_ready"] = test_cli()

    print(f"[i] Status preflight: {status}")
    return status
