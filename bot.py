# bot.py
import os
import sys
from nexus_quick_install_termux import (
    preflight_ensure_ready,
    start_node_smart,
    start_in_proot,
    test_cli,
)

def resolve_node_id() -> str:
    # Prioritas: argumen CLI -> ENV -> input
    if len(sys.argv) >= 2 and not sys.argv[1].startswith("-"):
        return sys.argv[1].strip()
    env_id = os.getenv("NODE_ID", "").strip()
    if env_id:
        return env_id
    return input("Masukkan node-id kamu: ").strip()

def main():
    print("=== Menjalankan Nexus Node via bot.py (auto-check & auto-install) ===")

    # Preflight: cek/siapkan dependensi (idempotent)
    _ = preflight_ensure_ready()

    node_id = resolve_node_id()
    if not node_id:
        print("[!] Node-id kosong, keluar.")
        return

    # 1) Coba jalankan native; jika gagal (atau binari tidak kompatibel), fallback proot
    if test_cli():
        ok = start_node_smart(node_id)
        if ok:
            return
        print("[!] Start native gagal; fallback via Ubuntu (proot-distro)...")

    # 2) Jalankan via Ubuntu (proot-distro)
    start_in_proot(node_id)

if __name__ == "__main__":
    main()
