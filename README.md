# bot.py — Nexus CLI Node Wrapper (Termux & Linux/macOS)

Skrip **`bot.py`** ini membungkus langkah resmi dari dokumentasi Nexus (install script + start/register) supaya Anda bisa menjalankan **node CLI Nexus** cukup dengan satu perintah: `python bot.py ...`.  
Mendukung:

- **Termux (Android)** → otomatis pakai helper `nexus_quick_install_termux.py`
- **Linux/macOS** → langsung pakai `nexus-network` di host (tanpa proot)

---

## 🔧 Apa yang dilakukan skrip?

- Mendeteksi lingkungan:
  - Jika **Linux/macOS biasa**:
    - Memasang Nexus CLI via: `curl https://cli.nexus.xyz/ | sh` (sesuai dokumen resmi).
    - Menjalankan node langsung via `~/.nexus/bin/nexus-network` atau `nexus-network` di `PATH`.
  - Jika **Termux (Android)**:
    - Menggunakan helper **`nexus_quick_install_termux.py`** untuk:
      - Cek / install Nexus CLI **native** di Termux.
      - Jika binari tidak kompatibel (`Bad system call`, dll) → otomatis siapkan **Ubuntu proot** dan jalankan node dari sana.
      - Menyediakan manajemen node di proot: **status**, **logs**, **stop**.
- Menyediakan sub-perintah praktis:
  - `--node-id`
  - `--wallet` (lebih disarankan dijalankan dari Linux/macOS)
  - `--login`
  - `--status`
  - `--stop`
  - `--logs` (khusus Termux + mode proot)

> **Catatan:** “Dashboard” utama pengelolaan node/points ada di **app.nexus.xyz**. Dari CLI Anda bisa lihat status via `--status`.

---

## ✅ Prasyarat Singkat

### Termux (Android)

- Termux terbaru (disarankan dari F-Droid).
- Python terpasang (jika perlu: `pkg install python`).
- Skrip akan otomatis memasang:
  - `curl`
  - `proot-distro` (untuk Ubuntu proot)
- File berikut berada di folder yang sama:
  - `bot.py`
  - `nexus_quick_install_termux.py`

### Linux/macOS

- Python terpasang (`python` atau `python3`).
- `curl` tersedia.
- Hanya butuh file `bot.py` (helper termux opsional/tidak wajib).

---

## 🚀 Quick Start

> Asumsikan file tersimpan di `~/nexus/`. Jika beda lokasi, sesuaikan path.

### 1. Linux/macOS

**Start dengan Node ID yang sudah ada:**

```bash
cd ~/nexus
python bot.py --node-id <NODE_ID_ANDA>
# contoh:
# python bot.py --node-id 8404744
```

**(Opsional) Alur daftar dari wallet di Linux/macOS:**

```bash
# Dengan env var:
export WALLET_ADDRESS=0xAlamatAnda
python bot.py --wallet $WALLET_ADDRESS

# Atau langsung argumen:
python bot.py --wallet 0xAlamatAnda
```

Mode `--wallet` akan mencoba:
1. `register-user` dari wallet address  
2. `register-node`  
3. Menjalankan node  

Node ID yang dihasilkan bisa dipakai nanti di Termux dengan `--node-id`.

---

### 2. Termux (Android)

**Rekomendasi alur praktis:**

1. **Daftar + buat Node ID di PC / Linux** (pakai metode `--wallet` di atas, atau langsung dari dokumentasi resmi).
2. Catat **Node ID** Anda.
3. Di Termux:

```bash
cd ~/nexus
python bot.py --node-id <NODE_ID_ANDA>
```

Saat pertama kali, skrip akan:

- Cek / install Nexus CLI native.
- Jika native tidak kompatibel → install `proot-distro`, setup **Ubuntu proot**, lalu:
  - Install Nexus CLI di dalam Ubuntu.
  - Menjalankan node di background dalam proot.
  - Menyimpan log di: `$HOME/.nexus-run/node.log` (di dalam Ubuntu).

**Cek status & log di Termux:**

```bash
# status node
python bot.py --status

# tail log (mode proot)
python bot.py --logs   # default tail 80 baris
```

> **Catatan:**  
> `--wallet` di Termux **tidak diotomasi penuh** (akan memberi peringatan). Disarankan melakukan `register-user` & `register-node` dari sistem Linux/PC yang punya browser, lalu di Termux cukup pakai `--node-id`.

---

## 🧭 Perintah yang Didukung

- `--node-id <ID>`  
  Menjalankan node dengan **Node ID** yang sudah terdaftar.
- `--wallet <0xADDR>`  
  **Linux/macOS:** alur otomatis register-user + register-node + start.  
  **Termux:** *tidak direkomendasikan*, skrip akan memberi peringatan (daftar sebaiknya dari PC).
- `--login`  
  Menampilkan **URL otorisasi** untuk menautkan akun (buka di browser).  
  Di Termux, kalau CLI native tidak siap, skrip akan menyarankan login dari device lain.
- `--status`  
  - Linux/macOS: memanggil `nexus-network status` / `ps`.  
  - Termux:
    - Jika node berjalan di proot → cek PID di Ubuntu.
    - Jika masih native → panggil `nexus-network status`.
- `--stop`  
  - Linux/macOS: memanggil `nexus-network stop`.  
  - Termux + proot: membunuh PID yang tersimpan di `$HOME/.nexus-run/node.pid`.
- `--logs`  
  - Termux + proot: `tail` log node di `$HOME/.nexus-run/node.log`.  
  - Linux/macOS: hanya memberi info bahwa log harus dicek via mekanisme deployment masing-masing (systemd, docker, dsb).

> Anda juga bisa memakai **env var** sebagai fallback:  
> `NODE_ID=<ID>` dan/atau `WALLET_ADDRESS=0x...`

Contoh:

```bash
export NODE_ID=8404744
python bot.py

# atau:
python bot.py --node-id 8404744
```

---

## 🔐 Login (Otorisasi Akun)

Jika CLI meminta login/otorisasi, jalankan:

```bash
python bot.py --login
```

Perintah di atas akan mencetak URL. **Buka URL tersebut** di browser untuk menyelesaikan otorisasi, lalu jalankan lagi `--node-id` atau `--wallet` sesuai kebutuhan.

- **Linux/macOS:** bisa langsung klik URL di terminal (tergantung terminal).
- **Termux:** salin URL dan buka manual di browser, atau gunakan:
  ```bash
  termux-open-url "<URL>"
  ```

---

## 📊 Cek Status, Log & Stop Node

```bash
# status ringkas
python bot.py --status

# (Termux + proot) tail log
python bot.py --logs

# hentikan node
python bot.py --stop
```

Di Termux + proot, file log dan PID berada di **dalam Ubuntu**:

- PID: `$HOME/.nexus-run/node.pid`
- Log: `$HOME/.nexus-run/node.log`

---

## 🧩 Helper: nexus_quick_install_termux.py

File **`nexus_quick_install_termux.py`** bisa:

1. **Di-import** oleh `bot.py` (otomatis).
2. Dipakai **sebagai CLI terpisah** di Termux.

Contoh pakai langsung di Termux:

```bash
# Cek & siapkan environment saja (CLI + proot)
python nexus_quick_install_termux.py preflight

# Start node dengan node-id (native dulu, kalau gagal → proot)
python nexus_quick_install_termux.py start --node-id <NODE_ID>

# Status via proot/native
python nexus_quick_install_termux.py status

# Tail log (proot)
python nexus_quick_install_termux.py logs --lines 100

# Stop node
python nexus_quick_install_termux.py stop
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

---

### 2) Mengetik `--node-id <ID>` sendirian → `command not found`

**Sebab:** `--node-id` adalah **argumen**, bukan perintah shell.  

**Solusi:** Selalu awali dengan `python bot.py`:

```bash
python bot.py --node-id 8404744
```

---

### 3) Termux: `Bad system call` saat menjalankan `nexus-network`

**Sebab:** Binari Nexus CLI butuh glibc / fitur kernel yang tidak kompatibel dengan Termux langsung.

**Solusi:**

- Biarkan skrip melakukan fallback ke **Ubuntu proot**.
- Setelah itu, jalankan:

  ```bash
  python bot.py --node-id <NODE_ID>
  python bot.py --status
  python bot.py --logs
  ```

Node akan berjalan di background di dalam Ubuntu proot.

---

### 4) Pesan: `Installation complete! Restart your terminal or run: source /root/.profile`

**Makna:** Ini pesan dari **Ubuntu proot** setelah install CLI.  

Skrip sudah memanggil biner dengan **path penuh**, jadi **tidak wajib** menjalankan `source`. Abaikan jika `--status` dan `start` sudah berfungsi.

---

### 5) Ingin menjalankan langsung di Ubuntu proot (manual)

Kalau ingin mengontrol sendiri dari dalam proot:

```bash
proot-distro login ubuntu -- bash -lc '$HOME/.nexus/bin/nexus-network --version'
proot-distro login ubuntu -- bash -lc '$HOME/.nexus/bin/nexus-network start --node-id <ID>'
```

---

## 📁 Struktur & Perilaku

- **Linux/macOS**
  - Skrip memasang Nexus CLI di `~/.nexus/bin/`.
  - Menjalankan perintah langsung di host (`nexus-network start ...`).

- **Termux**
  - Coba jalan native:
    - Install CLI di `$HOME/.nexus/bin`.
    - Cek kompatibilitas (`--version`).
  - Jika native gagal (`Bad system call` / error eksekusi):
    - Install `proot-distro`.
    - Setup **Ubuntu proot**.
    - Install Nexus CLI di dalam Ubuntu.
    - Jalankan node di **background**, simpan PID & log di:
      - `$HOME/.nexus-run/node.pid`
      - `$HOME/.nexus-run/node.log`

---

## 📝 Contoh Sesi Cepat

### Termux (mode rekomendasi: pakai Node ID yang sudah ada)

```bash
mkdir -p ~/nexus && cd ~/nexus
# (salin bot.py dan nexus_quick_install_termux.py ke folder ini)

# Jalankan node
python bot.py --node-id 8404744

# Cek status
python bot.py --status

# Lihat log jika perlu
python bot.py --logs

# Stop node
python bot.py --stop
```

### Linux/macOS (daftar + start dari wallet)

```bash
mkdir -p ~/nexus && cd ~/nexus
# (salin bot.py ke folder ini)

export WALLET_ADDRESS=0xAlamatAnda
python bot.py --wallet $WALLET_ADDRESS
# setelah node terdaftar dan start, catat NODE_ID

# lain waktu, cukup:
python bot.py --node-id <NODE_ID>
```

---

## ❓ Q&A Singkat

- **Q:** Bisa pakai `python3`?  
  **A:** Bisa. Ganti `python` → `python3` sesuai environment Anda.

- **Q:** Apakah butuh sudo?  
  **A:** Tidak di Termux. Di Linux/macOS, install CLI via `curl | sh` berjalan di home user, **tanpa sudo**.

- **Q:** Di mana lokasi biner?  
  **A:** `~/.nexus/bin/nexus-network`  
  - Di host Linux/macOS.  
  - Di dalam Ubuntu proot (Termux).

---

Selamat menjalankan node! Jika macet, kirim output dari:

```bash
python bot.py --status
```

dan (kalau di Termux + proot):

```bash
python bot.py --logs
```

agar bisa dibantu diagnosa lebih lanjut.
