```
 ██╗    ██╗██╗███████╗██╗    ██████╗ ██████╗  ██████╗ ██████╗ ███████╗
 ██║    ██║██║██╔════╝██║    ██╔══██╗██╔══██╗██╔═══██╗██╔══██╗██╔════╝
 ██║ █╗ ██║██║█████╗  ██║    ██████╔╝██████╔╝██║   ██║██████╔╝█████╗  
 ██║███╗██║██║██╔══╝  ██║    ██╔═══╝ ██╔══██╗██║   ██║██╔══██╗██╔══╝  
 ╚███╔███╔╝██║██║     ██║    ██║     ██║  ██║╚██████╔╝██████╔╝███████╗
  ╚══╝╚══╝ ╚═╝╚═╝     ╚═╝    ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝
```

# WIF1-PR0B3 — WiFi Reconnaissance Toolkit

> A powerful WiFi network scanner, analyzer, and signal strength visualizer with a hacker-themed GUI. Built with Python and Tkinter.

![Python](https://img.shields.io/badge/Python-3.8%2B-00ff41?style=for-the-badge&logo=python&logoColor=00ff41&labelColor=0a0a0a)
![Platform](https://img.shields.io/badge/Platform-Windows-00e5ff?style=for-the-badge&logo=windows&logoColor=00e5ff&labelColor=0a0a0a)
![License](https://img.shields.io/badge/License-MIT-ffb800?style=for-the-badge&labelColor=0a0a0a)

---

## 🖥️ Screenshots

<details>
<summary>Click to expand</summary>

> The app features a full hacker-themed dark UI with matrix green text, ASCII art banner, animated matrix rain ticker, and neon accents.

| Tab | Description |
|-----|-------------|
| `[SCAN]` | Network scanner with real-time WiFi discovery |
| `[ANALYZE]` | Dashboard with charts and statistics |
| `[SIGNAL]` | Live signal strength monitor with graph |
| `[CONN]` | Current connection details |
| `[PROFILES]` | Saved WiFi profiles viewer |

</details>

---

## ⚡ Features

### 🔍 Network Scanner
- Scans **all nearby WiFi networks** using the Windows Native WLAN API (`pywifi`)
- Displays SSID, BSSID, signal strength, channel, frequency band, authentication, and encryption
- **Real-time filtering** by name, frequency band (2.4 GHz / 5 GHz), and encryption type
- Sortable columns (click any heading)
- Color-coded signal strength: 🟢 Strong | 🟡 Fair | 🔴 Weak
- Auto-refresh mode (every 10 seconds)
- Export scan results to **CSV**

### 📊 Network Analyzer
- Dashboard with stat cards: total targets, band split, open networks, average signal, strongest network
- **Channel usage** bar chart — identify congested channels
- **Authentication type** pie chart — see WPA2/WPA3/Open distribution
- **Signal strength distribution** histogram
- Text-based fallback if matplotlib is not installed

### 📶 Signal Monitor
- Select any discovered network and **lock on** for real-time signal tracking
- Large signal percentage display with animated progress bar
- **Live signal history graph** with quality threshold lines
- Min / Max / Average signal tracking
- Color changes based on signal quality

### 🔗 Connection Info
- Full details of your **current active WiFi connection**
- SSID, BSSID, radio type, channel, authentication, cipher
- Receive/Transmit rates in Mbps
- Raw interface data dump

### 📋 Saved Profiles
- View all WiFi profiles saved on your system

### 🎨 Hacker GUI
- Pure black background with **matrix green** (`#00ff41`) text
- **ASCII art banner** header
- **Animated matrix rain** ticker at the bottom
- Live system clock
- Monospace `Consolas` font throughout
- Neon cyan, amber, and red accents
- Terminal-style labels and buttons (`>> SCAN`, `>> LOCK ON`, `FILTER>`)

---

## 🛠️ Installation

### Prerequisites
- **Python 3.8+**
- **Windows OS** (uses Windows WLAN API)

### Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/wifi-probe.git
cd wifi-probe

# Install dependencies
pip install pywifi comtypes matplotlib
```

### Dependencies

| Package | Purpose | Required |
|---------|---------|----------|
| `pywifi` | WiFi scanning via Windows Native WLAN API | ✅ Yes |
| `comtypes` | COM interface for pywifi on Windows | ✅ Yes |
| `matplotlib` | Charts and signal graphs | ❌ Optional (text fallback) |
| `tkinter` | GUI framework | ✅ Bundled with Python |

---

## 🚀 Usage

```bash
python wifi_toolkit.py
```

The app launches with a full GUI. It will automatically scan for nearby networks on startup.

### Quick Guide

| Action | How |
|--------|-----|
| Scan networks | Click `>> SCAN` or enable `AUTO-REFRESH` |
| Filter results | Type in the `FILTER>` box or select `BAND>` / `ENC>` |
| Monitor signal | Go to `[SIGNAL]` tab → select network → click `>> LOCK ON` |
| Export data | Click `>> EXPORT` to save results as CSV |
| View connection | Go to `[CONN]` tab → click `>> REFRESH` |
| View profiles | Go to `[PROFILES]` tab → click `>> LOAD PROFILES` |

---

## 📁 Project Structure

```
wifi-probe/
├── wifi_toolkit.py    # Main application (single file)
├── README.md          # This file
└── LICENSE            # MIT License
```

---

## ❓ Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: pywifi` | Run `pip install pywifi comtypes` |
| Only 1 network found | You're using `netsh` fallback — install `pywifi` for full scanning |
| No WiFi adapter found | Ensure your WiFi adapter is enabled and drivers are installed |
| Charts not showing | Install `matplotlib`: `pip install matplotlib` |
| App won't start | Ensure Python 3.8+ is installed and `tkinter` is available |

---

## ⚠️ Disclaimer

This tool is designed for **legitimate network diagnostics and analysis** of WiFi networks. It only performs passive scanning — it does not connect to, intercept, or interfere with any network. Use responsibly and only on networks you own or have permission to analyze.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions are welcome! Feel free to:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

---

<p align="center">
  <code>[ WIF1-PR0B3 v3.7 | RECON MODULE ]</code>
</p>
