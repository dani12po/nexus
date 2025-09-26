# bot.py
import os
import sys
from nexus_quick_install_termux import (
    preflight_ensure_ready,
    start_node_smart,
    start_in_proot_detached,
    proot_status,
    proot_logs,
    proot_stop,
    test_cli,
)

USAGE = """\
Pemakaian:
  python bot.py <NODE_ID>         # start (native; fallback proot) - default
  python bot.py --status          # cek status node di proot Ubuntu
  python bot.py --logs [N]        # lihat N baris log terakhir (default 80)
  python bot.py --stop            # hentikan node di proot Ubuntu
  NODE_ID=xxxx python bot.py      # juga bisa via ENV
"""

def resolve_node_id(argv) -> str:
    # Prioritas: argumen CLI -> ENV -> input
    if len(argv) >= 2 and not argv[1].startswith("-"):
        return argv[1].strip()
    env_id = os.getenv("NODE_ID", "").strip()
    if env_id:
        return env_id
    return input("Masukkan node-id kamu: ").strip()

def main(argv):
    if len(argv) >= 2 and argv[1] in {"-h", "--help"}:
        print(USAGE)
        return

    # Subcommand ringan
    if len(argv) >= 2 and argv[1] == "--status":
        proot_status()
        return
    if len(argv) >= 2 and argv[1] == "--logs":
        tail_n = 80
        if len(argv) >= 3 and argv[2].isdigit():
            tail_n = int(argv[2])
        proot_logs(tail_n)
        return
    if len(argv) >= 2 and argv[1] == "--stop":
        proot_stop()
        return

    print("=== Menjalankan Nexus Node via bot.py (auto-check & auto-install) ===")

    # Preflight env (idempotent)
    _ = preflight_ensure_ready()

    node_id = resolve_node_id(argv)
    if not node_id:
        print("[!] Node-id kosong.\n")
        print(USAGE)
        return

    # 1) Coba native; jika gagal atau tidak kompatibel, fallback proot (DETACHED)
    if test_cli():
        ok = start_node_smart(node_id)
        if ok:
            return
        print("[!] Start native gagal; fallback via Ubuntu (proot-distro)...")

    # 2) Jalankan di proot Ubuntu (DETACHED + PID + LOG)
    start_in_proot_detached(node_id)

if __name__ == "__main__":
    main(sys.argv)
