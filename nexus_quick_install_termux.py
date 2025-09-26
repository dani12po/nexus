# nexus_quick_install_termux.py
import os
import subprocess
import shutil
from pathlib import Path

# =======================
# Util dasar
# =======================
def run(cmd, check=True, capture=False, env=None):
    """Jalankan perintah shell. Return stdout (jika capture=True) atau None."""
    print(f"\n>>> {cmd}")
    result = subprocess.run(
        cmd,
        shell=True,
        text=True,
        env=env,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    if check and result.returncode != 0:
        print(f"[!] Command gagal: {cmd}")
        if capture:
            print("stdout:", result.stdout)
            print("stderr:", result.stderr)
        return None
    return result.stdout if capture else None

def is_command_available(cmd_name: str) -> bool:
    """Cek ketersediaan command di PATH."""
    return shutil.which(cmd_name) is not None

def is_termux() -> bool:
    """Deteksi Termux (ada 'pkg')."""
    return is_command_available("pkg")

def dpkg_installed(pkg: str) -> bool:
    """Cek paket via dpkg -s (Termux berbasis dpkg juga)."""
    res = run(f"dpkg -s {pkg} >/dev/null 2>&1", check=False)
    return res is not None  # returncode==0 -> res==None; gunakan command -v sebagai alternatif
    # Catatan: karena run() return None jika capture=False, gunakan command -v sebagai fallback:
    # Di bawah kita pakai kombinasi dpkg -s dan which sesuai kasus.

def pkg_ensure(pkgs):
    """Pastikan paket terpasang (idempotent)."""
    if not is_termux():
        return
    # Up-to-date index minimal sekali (ringan, aman)
    run("pkg update -y", check=False)
    for p in pkgs:
        # Cek cepat: kalau sudah ada command-nya, lewati.
        if is_command_available(p):
            continue
        # Coba dpkg -s; jika tidak terpasang, install
        status = run(f"dpkg -s {p}", check=False)
        if status is None:  # tidak terpasang
            run(f"pkg install -y {p}", check=True)

def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""

def append_once(file: Path, text: str):
    """Tambahkan baris ke file rc bila belum ada (idempotent)."""
    content = read_text(file)
    if text.strip() not in content:
        file.parent.mkdir(parents=True, exist_ok=True)
        with file.open("a", encoding="utf-8") as f:
            f.write("\n" + text.rstrip() + "\n")

def shell_rc_candidates():
    home = Path.home()
    return [home / ".zshrc", home / ".bashrc", home / ".profile"]

def ensure_path_to_nexus_bin():
    """Pastikan PATH menyertakan ~/.nexus/bin (jika ada)."""
    nexus_bin = Path.home() / ".nexus" / "bin"
    if not nexus_bin.exists():
        return False
    export_line = 'export PATH="$HOME/.nexus/bin:$PATH"'
    for rc in shell_rc_candidates():
        append_once(rc, export_line)
    # Source file yang ada (best effort)
    for rc in shell_rc_candidates():
        if rc.exists():
            run(f"source {rc}", check=False)
    return True

def ensure_network():
    """Cek koneksi minimal ke installer Nexus."""
    res = run("curl -sSfI https://cli.nexus.xyz", check=False, capture=True)
    return res is not None

# =======================
# Nexus CLI
# =======================
def install_cli_termux():
    """Install Nexus CLI di Termux (idempotent)."""
    if not is_termux():
        return False
    if test_cli():
        print("[=] Nexus CLI sudah tersedia, lewati instalasi.")
        return True

    pkg_ensure(["curl"])
    if not ensure_network():
        print("[!] Tidak bisa akses https://cli.nexus.xyz. Periksa koneksi.")
        return False

    # Jalankan installer resmi (menambah ~/.nexus/bin)
    run("curl https://cli.nexus.xyz/ | sh", check=True)
    ensure_path_to_nexus_bin()

    # Re-check
    if test_cli():
        print("[+] Nexus CLI terpasang.")
        return True
    print("[x] Nexus CLI belum terdeteksi setelah instalasi.")
    return False

def test_cli():
    """Uji Nexus CLI."""
    # Tes via command -v dulu
    if is_command_available("nexus-network"):
        # Coba --help / --version
        out = run("nexus-network --help", check=False, capture=True)
        if out and "Usage" in out:
            return True
        out_v = run("nexus-network --version", check=False, capture=True)
        return out_v is not None
    # Coba bila terpasang di ~/.nexus/bin namun PATH belum terset
    nexus_bin = Path.home() / ".nexus" / "bin" / "nexus-network"
    if nexus_bin.exists():
        out = run(f'"{nexus_bin}" --version', check=False, capture=True)
        return out is not None
    return False

def start_node(node_id: str):
    """Jalankan node secara native (PATH disuntik ~/.nexus/bin jika ada)."""
    env = os.environ.copy()
    env["PATH"] = f'{str(Path.home() / ".nexus" / "bin")}:' + env.get("PATH", "")
    cmd = f'nexus-network start --node-id "{node_id}"'
    # Bila command global tidak ada, coba panggil lewat path absolut
    if not is_command_available("nexus-network"):
        candidate = Path.home() / ".nexus" / "bin" / "nexus-network"
        if candidate.exists():
            cmd = f'"{candidate}" start --node-id "{node_id}"'
    run(cmd, check=True, env=env)

# =======================
# Fallback Ubuntu (proot)
# =======================
def ensure_proot_distro() -> bool:
    """Pastikan proot-distro ada (untuk fallback Ubuntu)."""
    if not is_termux():
        return False
    if is_command_available("proot-distro"):
        return True
    pkg_ensure(["proot-distro"])
    return is_command_available("proot-distro")

def start_in_proot(node_id: str):
    """Start node di Ubuntu proot (idempotent)."""
    if not ensure_proot_distro():
        print("[x] proot-distro belum siap.")
        return
    # Install Ubuntu (idempotent) lalu pasang Nexus CLI di dalamnya
    run("proot-distro install ubuntu || true", check=False)
    run((
        'proot-distro login ubuntu -- bash -lc "'
        'apt-get update -y && apt-get install -y curl && '
        'curl https://cli.nexus.xyz/ | sh && '
        'source ~/.bashrc || true; '
        f'nexus-network start --node-id \\"{node_id}\\""'
    ), check=True)

# =======================
# Orkestrasi preflight
# =======================
def preflight_ensure_ready():
    """
    Lakukan seluruh pengecekan & instalasi minimal.
    - Jika Termux: pastikan curl, Nexus CLI; siapkan proot-distro untuk fallback.
    - Jika bukan Termux: tetap coba jalankan jika nexus-network sudah ada di PATH user.
    Return dict ringkas status.
    """
    status = {"termux": is_termux(), "cli_ready": False, "proot_ready": False}

    if is_termux():
        # Siapkan CLI native
        status["cli_ready"] = install_cli_termux()
        # Siapkan proot untuk jaga-jaga
        status["proot_ready"] = ensure_proot_distro()
    else:
        # Non-Termux: cukup cek apakah user sudah punya nexus-network di PATH
        status["cli_ready"] = test_cli()

    print(f"[i] Status preflight: {status}")
    return status
