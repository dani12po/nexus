# bot.py
import os
import sys
from nexus_quick_install_termux import (
    preflight_ensure_ready,
    start_node_smart,
    test_cli,
)

def resolve_node_id():
    # Urutan prioritas: argumen CLI -> ENV -> input
    if len(sys.argv) >= 2 and not sys.argv[1].startswith("-"):
        return sys.argv[1].strip()
    env_id = os.getenv("NODE_ID", "").strip()
    if env_id:
        return env_id
    return input("Masukkan node-id kamu: ").strip()

def main():
    print("=== Menjalankan Nexus Node via bot.py (auto-check & auto-install) ===")

    # Pastikan semua kebutuhan siap (idempotent)
    _ = preflight_ensure_ready()

    node_id = resolve_node_id()
    if not node_id:
        print("[!] Node-id kosong, keluar.")
        return

    if not test_cli():
        print("[x] Nexus CLI belum siap walau instalasi dicoba. Cek koneksi/izin Termux, lalu ulangi.")
        return

    # Jalankan dengan auto-deteksi format perintah dan tampilkan error nyata bila gagal
    ok = start_node_smart(node_id)
    if not ok:
        print("\n[x] Gagal menjalankan node setelah mencoba beberapa variasi perintah.")
        print("    Cek pesan error di atas (stdout/stderr). Jika ada info seperti 'login', jalankan perintah login sesuai petunjuk CLI.")

if __name__ == "__main__":
    main()
