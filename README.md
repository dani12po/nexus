# Nexus (Legacy Working Script)

This repository contains **Python scripts** used to run and manage **Nexus CLI**, with a primary focus on compatibility on **Termux (Android)** as well as Linux and other Unix-like systems.

This is a **legacy version** of the script that is still **STABLE and WORKING**.

---

## ✨ Main Features

- Automatic environment detection (Termux / Linux / others)
- Automatic Nexus CLI installation
- Automatic fallback to **Ubuntu (proot-distro)** on Termux if the binary is incompatible
- Run Nexus node using an existing **Node ID**
- Check node status, logs, and stop node
- Suitable for long-running usage on VPS or Android devices

---

## 📂 Repository Structure

```
├── bot.py
├── nexus_quick_install_termux.py
├── README.md
└── __pycache__/
```

### File Description

- **bot.py**  
  Main script used to install, run, and manage Nexus CLI.

- **nexus_quick_install_termux.py**  
  Helper script specifically for setting up Nexus CLI on Termux.

- **__pycache__/**  
  Python cache directory (can be ignored).

---

## ⚙️ Requirements

### General
- Python 3
- Git
- Curl

---

## 🚀 Installation Guide (Step by Step)

Below are **step-by-step installation instructions** for different environments.

---

## 🐧 Debian / Ubuntu / Linux Server (VPS)

### 1️⃣ Update system
```bash
sudo apt update && sudo apt upgrade -y
```

### 2️⃣ Install dependencies
```bash
sudo apt install -y python3 python3-pip git curl
```

### 3️⃣ Clone repository
```bash
git clone https://github.com/dani12po/nexus.git
cd nexus
```

### 4️⃣ Run the script
```bash
python3 bot.py --node-id <NODE_ID>
```

---

## 🐧 Linux Desktop (Ubuntu / Debian / Arch / Fedora)

### 1️⃣ Verify Python & Git
```bash
python3 --version
git --version
```

### 2️⃣ Install missing dependencies (Debian/Ubuntu)
```bash
sudo apt install -y python3 git curl
```

### 3️⃣ Clone repository
```bash
git clone https://github.com/dani12po/nexus.git
cd nexus
```

### 4️⃣ Run the script
```bash
python3 bot.py --node-id <NODE_ID>
```

---

## 📱 Termux (Android)

> Recommended: install Termux from **F-Droid**, not Play Store.

### 1️⃣ Update Termux packages
```bash
pkg update && pkg upgrade -y
```

### 2️⃣ Install dependencies
```bash
pkg install -y python git curl
```

### 3️⃣ Clone repository
```bash
git clone https://github.com/dani12po/nexus.git
cd nexus
```

### 4️⃣ Run the script
```bash
python bot.py --node-id <NODE_ID>
```

➡️ If Nexus CLI cannot run natively, the script will **automatically install Ubuntu using proot-distro** and run Nexus from there.

---

## 💻 Other Terminals (macOS / WSL)

### 1️⃣ Verify Python & Git
```bash
python3 --version
git --version
```

### 2️⃣ Install dependencies

**macOS (Homebrew):**
```bash
brew install python git curl
```

### 3️⃣ Clone repository
```bash
git clone https://github.com/dani12po/nexus.git
cd nexus
```

### 4️⃣ Run the script
```bash
python3 bot.py --node-id <NODE_ID>
```

---

## 🧰 Script Arguments

| Argument | Description |
|--------|------------|
| `--node-id` | Run Nexus node using a specific Node ID |
| `--status` | Check node status |
| `--logs` | View node logs |
| `--stop` | Stop running node |
| `--login` | Display Nexus login URL |

---

## 💡 Important Notes

- It is **recommended to create your Node ID on a PC or VPS first**, then run the Node ID on Termux.
- For long-term usage, VPS or non-aggressive Android battery settings are recommended.

---

## ⚠️ Disclaimer

- This repository uses a **legacy script that is still working**.
- Compatibility with future Nexus CLI updates is not guaranteed.
- Use a separate branch if you plan to develop a newer version.

---

## 📜 License

Free to use and modify for personal purposes.

---

### ✨ Legacy, simple, and still working
Focus on functionality — not fancy stuff.

