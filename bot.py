# bot.py
from nexus_quick_install_termux import install_cli_termux, source_shell, test_cli, fallback_proot, start_node

def main():
    print("=== Menjalankan Nexus Node via bot.py ===")
    install_cli_termux()
    source_shell()

    node_id = input("Masukkan node-id kamu: ").strip()
    if not node_id:
        print("[!] Node-id kosong, keluar.")
        return

    if test_cli():
        print("[+] Nexus CLI berjalan di Termux, mulai node...")
        start_node(node_id)
    else:
        print("[!] Nexus CLI tidak support di Termux, fallback ke Ubuntu...")
        fallback_proot(node_id)

if __name__ == "__main__":
    main()
