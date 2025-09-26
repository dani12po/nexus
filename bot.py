# bot.py
from nexus_quick_install_termux import (
    preflight_ensure_ready,
    start_node,
    start_in_proot,
    test_cli,
)

def main():
    print("=== Menjalankan Nexus Node via bot.py (auto-check & auto-install) ===")

    # Pastikan semua kebutuhan siap (idempotent)
    ready_env = preflight_ensure_ready()

    node_id = input("Masukkan node-id kamu: ").strip()
    if not node_id:
        print("[!] Node-id kosong, keluar.")
        return

    # Jika CLI tersedia native, jalankan langsung; jika tidak, fallback proot Ubuntu
    if test_cli():
        print("[+] Nexus CLI terdeteksi. Menjalankan node...")
        start_node(node_id)
    else:
        if ready_env.get("proot_ready", False):
            print("[!] Nexus CLI belum tersedia native. Menjalankan via Ubuntu (proot-distro)...")
            start_in_proot(node_id)
        else:
            print("[x] Gagal menemukan Nexus CLI & proot-distro tidak siap. Cek koneksi / izin Termux.")

if __name__ == "__main__":
    main()
