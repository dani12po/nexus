# bot.py — Nexus CLI Node Wrapper (Termux & Linux/macOS)

Skrip **`bot.py`** ini membungkus langkah resmi dari dokumentasi Nexus (install script + start/register) supaya Anda bisa menjalankan **node CLI Nexus** cukup dengan satu perintah: `python bot.py ...`.  
Mendukung **Termux (Android)** dan **Linux/macOS**.

---

## 🔧 Apa yang dilakukan skrip?
- **Memasang Nexus CLI** via: `curl https://cli.nexus.xyz/ | sh` (sesuai dokumen resmi).
- **Termux**: otomatis menyiapkan **Ubuntu proot** agar kompatibel (glibc), lalu menjalankan perintah CLI dari dalam proot.
- Menyediakan sub-perintah praktis: `--node-id`, `--wallet`, `--login`, `--status`, `--stop`.

> **Catatan:** “Dashboard” utama pengelolaan node/points ada di **app.nexus.xyz**. Dari CLI Anda bisa lihat status via `--status`.

---

## ✅ Prasyarat Singkat
### Termux (Android)
- Termux terbaru (disarankan dari F-Droid).
- Python terpasang (jika perlu: `pkg install python`).
- Skrip akan otomatis memasang `proot-distro` dan `curl` bila belum ada.

### Linux/macOS
- Python terpasang (`python` atau `python3`).
- `curl` tersedia.

---

## 🚀 Quick Start

> Asumsikan file tersimpan di `~/nexus/bot.py`. Jika beda lokasi, sesuaikan path.

### Termux (Android)
```bash
cd ~/nexus
python bot.py --node-id <NODE_ID_ANDA>
# contoh:
# python bot.py --node-id 000000
```

**Belum punya Node ID?** Jalankan alur daftar dari wallet:
```bash
# Dengan variable env (opsional):
export WALLET_ADDRESS=0xAlamatAnda
python bot.py --wallet $WALLET_ADDRESS

# Atau langsung argumen:
python bot.py --wallet 0xAlamatAnda
```
Skrip akan:
1) memasang Ubuntu proot (sekali saja)  
2) memasang Nexus CLI, lalu  
3) mendaftarkan user/node **atau** langsung start dengan `--node-id`.

### Linux/macOS
```bash
# Start dari Node ID yang sudah ada
python bot.py --node-id <NODE_ID_ANDA>

# Atau daftar dari wallet:
python bot.py --wallet 0xAlamatAnda
```

---

## 🧭 Perintah yang Didukung
- `--node-id <ID>` — Menjalankan node dengan **Node ID** yang sudah terdaftar.
- `--wallet <0xADDR>` — Daftarkan user dari wallet → register node → start.
- `--login` — Menampilkan **URL otorisasi** untuk menautkan akun (buka di browser).
- `--status` — Menampilkan status CLI/node (ringkas).
- `--stop` — Menghentikan node yang sedang berjalan.

> Anda juga bisa memakai **env var** sebagai fallback:  
> `NODE_ID=<ID>` dan/atau `WALLET_ADDRESS=0x...`

Contoh:
```bash
# Menggunakan env var
export NODE_ID=8404744
python bot.py

# Atau langsung argumen
python bot.py --node-id 8404744
```

---

## 🔐 Login (Otorisasi Akun)
Jika CLI meminta login/otorisasi, jalankan:
```bash
python bot.py --login
```
Perintah di atas akan mencetak URL. **Buka URL tersebut** di browser untuk menyelesaikan otorisasi, lalu jalankan lagi `--node-id` atau `--wallet` sesuai kebutuhan.

> **Termux**: Jika ingin, Anda dapat menyalin URL dan membuka dengan `termux-open-url "<URL>"` (opsional).

---

## 📊 Cek Status & Hentikan Node
```bash
# Lihat status ringkas
python bot.py --status

# Hentikan node
python bot.py --stop
```

---

## 🧰 Troubleshooting (Masalah Umum)

### 1) `python: can't open file '.../bot': [Errno 2] No such file or directory`
**Sebab:** Memanggil file dengan nama salah (`bot` bukannya `bot.py`) atau path-nya tidak tepat.  
**Solusi:**
```bash
cd ~/nexus
ls -l          # pastikan ada bot.py
python bot.py --node-id <ID>
# atau: python ~/nexus/bot.py --node-id <ID>
```

### 2) Mengetik `--node-id <ID>` sendirian → `command not found`
**Sebab:** `--node-id` adalah **argumen**, bukan perintah shell.  
**Solusi:** Selalu awali dengan `python bot.py`:
```bash
python bot.py --node-id 8404744
```

### 3) Pesan: `Installation complete! Restart your terminal or run: source /root/.profile`
**Makna:** Ini pesan dari **Ubuntu proot**. Skrip sudah memanggil biner dengan path penuh, jadi **tidak wajib** menjalankan `source`. Abaikan jika `--status` dan `start` sudah berfungsi.

### 4) Tidak tampil dashboard di terminal
CLI biasanya headless. Pantau pakai `--status`, dan kelola node/points di **app.nexus.xyz**.

### 5) Ingin menjalankan langsung di Ubuntu proot (manual)
```bash
proot-distro login ubuntu -- bash -lc '$HOME/.nexus/bin/nexus-network --version'
proot-distro login ubuntu -- bash -lc '$HOME/.nexus/bin/nexus-network start --node-id <ID>'
```

---

## 📁 Struktur & Perilaku
- **Termux**: Skrip otomatis `pkg install -y proot-distro curl` → `proot-distro install ubuntu` → menjalankan perintah Nexus CLI di dalam Ubuntu.
- **Linux/macOS**: Skrip memasang Nexus CLI di `~/.nexus/bin/` dan menjalankannya langsung.

---

## 📝 Contoh Sesi Cepat (Termux)
```bash
mkdir -p ~/nexus && cd ~/nexus
# (salin bot.py ke folder ini)
python bot.py --node-id 8404744
python bot.py --status
# Jika perlu login:
python bot.py --login
# Setelah login, start ulang:
python bot.py --node-id 8404744
```

---

## ❓ Q&A Singkat
- **Q:** Bisa pakai `python3`?  
  **A:** Bisa. Ganti `python` → `python3` sesuai environment Anda.

- **Q:** Apakah butuh sudo?  
  **A:** Tidak di Termux. Di Linux/macOS, install CLI via `curl | sh` berjalan di home user, **tanpa sudo**.

- **Q:** Di mana lokasi biner?  
  **A:** `~/.nexus/bin/nexus-network` (baik di proot Ubuntu maupun di host Linux/macOS).

---

Selamat menjalankan node! Jika macet, kirim output dari:
```bash
python bot.py --status
```
agar bisa dibantu diagnosa lebih lanjut.
