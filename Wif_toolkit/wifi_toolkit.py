"""
WiFi Toolkit - Scanner, Analyzer & Signal Strength Visualizer
A legitimate network diagnostics tool for Windows.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import re
import threading
import time
import csv
import os
import sys
import ctypes
import random
from collections import Counter
from datetime import datetime

# Try importing matplotlib for charts
try:
    import matplotlib
    matplotlib.use('TkAgg')
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# pywifi for reliable scanning
try:
    import pywifi
    from pywifi import const as wifi_const
    HAS_PYWIFI = True
except ImportError:
    HAS_PYWIFI = False


class WiFiNetwork:
    """Represents a discovered WiFi network."""
    def __init__(self, ssid="", bssid="", signal=0, channel=0,
                 encryption="", auth="", network_type="", band=""):
        self.ssid = ssid
        self.bssid = bssid
        self.signal = signal
        self.channel = channel
        self.encryption = encryption
        self.auth = auth
        self.network_type = network_type
        self.band = band
        self.timestamp = datetime.now().strftime("%H:%M:%S")

    @property
    def signal_quality(self):
        if self.signal >= 80:
            return "Excellent"
        elif self.signal >= 60:
            return "Good"
        elif self.signal >= 40:
            return "Fair"
        elif self.signal >= 20:
            return "Weak"
        return "Very Weak"

    @property
    def frequency_band(self):
        if self.channel <= 14:
            return "2.4 GHz"
        return "5 GHz"


def is_admin():
    """Check if running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def relaunch_as_admin():
    """Relaunch the script with administrator privileges."""
    try:
        script = os.path.abspath(sys.argv[0])
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script}"', None, 1
        )
        sys.exit(0)
    except Exception:
        return False


# Auth type mapping for pywifi
AUTH_MAP = {
    0: "Open",
    1: "WPA",
    2: "WPA-PSK",
    3: "WPA2",
    4: "WPA2-PSK",
    5: "WPA2-Enterprise",
}

CIPHER_MAP = {
    0: "None",
    1: "WEP",
    2: "TKIP",
    3: "AES/CCMP",
    4: "CCMP",
}


def freq_to_channel(freq_khz):
    """Convert frequency in kHz to channel number."""
    freq = freq_khz // 1000  # to MHz
    if 2412 <= freq <= 2484:
        if freq == 2484:
            return 14
        return (freq - 2412) // 5 + 1
    elif 5170 <= freq <= 5825:
        return (freq - 5000) // 5
    return 0


def dbm_to_percent(dbm):
    """Convert dBm signal to percentage (0-100)."""
    if dbm >= -30:
        return 100
    elif dbm <= -90:
        return 0
    return int(100 * (dbm + 90) / 60)


def scan_wifi_networks(scan_duration=4):
    """Scan for nearby WiFi networks using pywifi (Windows Native WLAN API)."""
    if not HAS_PYWIFI:
        return "PYWIFI_MISSING"

    networks = []
    try:
        wifi = pywifi.PyWiFi()
        if not wifi.interfaces():
            return "NO_INTERFACE"

        iface = wifi.interfaces()[0]

        # Trigger a fresh hardware scan
        iface.scan()
        time.sleep(scan_duration)

        results = iface.scan_results()

        # Deduplicate: keep strongest signal per SSID+BSSID
        seen = {}
        for r in results:
            ssid = r.ssid if r.ssid else "[Hidden Network]"
            bssid = r.bssid.upper() if r.bssid else "Unknown"
            key = f"{ssid}_{bssid}"

            signal_pct = dbm_to_percent(r.signal)
            channel = freq_to_channel(r.freq)
            freq_mhz = r.freq // 1000
            band = "2.4 GHz" if freq_mhz < 3000 else "5 GHz"

            # Auth info
            auth_str = "Open"
            if hasattr(r, 'akm') and r.akm:
                auth_types = [AUTH_MAP.get(a, f"Unknown({a})") for a in r.akm if a != 0]
                auth_str = "/".join(auth_types) if auth_types else "Open"

            # Cipher info
            cipher_str = "None"
            if hasattr(r, 'cipher') and r.cipher:
                cipher_str = CIPHER_MAP.get(r.cipher, f"Unknown({r.cipher})")

            if key not in seen or signal_pct > seen[key].signal:
                net = WiFiNetwork(
                    ssid=ssid,
                    bssid=bssid,
                    signal=signal_pct,
                    channel=channel,
                    encryption=cipher_str,
                    auth=auth_str,
                    network_type="Infrastructure",
                    band=band
                )
                seen[key] = net

        networks = sorted(seen.values(), key=lambda n: n.signal, reverse=True)
    except Exception as e:
        print(f"Scan error: {e}")
    return networks


def get_current_connection():
    """Get information about the current WiFi connection."""
    info = {}
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        output = result.stdout
        for line in output.split('\n'):
            if ':' in line:
                key, _, value = line.partition(':')
                key = key.strip()
                value = value.strip()
                if key and value:
                    info[key] = value
    except Exception as e:
        info['Error'] = str(e)
    return info


def get_saved_profiles():
    """Get list of saved WiFi profiles."""
    profiles = []
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "profiles"],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        for line in result.stdout.split('\n'):
            match = re.search(r'All User Profile\s*:\s*(.+)', line)
            if match:
                profiles.append(match.group(1).strip())
    except Exception:
        pass
    return profiles


# ─── Hacker ASCII Art ───
HACKER_BANNER = r"""
 ██╗    ██╗██╗███████╗██╗    ██████╗ ██████╗  ██████╗ ██████╗ ███████╗
 ██║    ██║██║██╔════╝██║    ██╔══██╗██╔══██╗██╔═══██╗██╔══██╗██╔════╝
 ██║ █╗ ██║██║█████╗  ██║    ██████╔╝██████╔╝██║   ██║██████╔╝█████╗  
 ██║███╗██║██║██╔══╝  ██║    ██╔═══╝ ██╔══██╗██║   ██║██╔══██╗██╔══╝  
 ╚███╔███╔╝██║██║     ██║    ██║     ██║  ██║╚██████╔╝██████╔╝███████╗
  ╚══╝╚══╝ ╚═╝╚═╝     ╚═╝    ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝
"""

MATRIX_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789@#$%&*"


class WiFiToolkit(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("[ WIF1-PR0B3 ] // Network Reconnaissance Suite v3.7")
        self.geometry("1200x800")
        self.minsize(1000, 650)
        self.configure(bg="#0a0a0a")

        # Try to remove window decoration for extra hacker feel
        self.overrideredirect(False)

        self.networks = []
        self.scan_history = []
        self.monitoring = False
        self.matrix_after_id = None

        self._setup_styles()
        self._build_ui()
        self._start_matrix_rain()

        if not HAS_PYWIFI:
            messagebox.showwarning(
                "[!] DEPENDENCY ERROR",
                "[CRITICAL] pywifi module not found.\n\n"
                "> pip install pywifi comtypes\n\n"
                "Scanner module OFFLINE."
            )
        self.after(500, self._initial_scan)

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use('clam')

        # Hacker color palette
        bg = "#0a0a0a"          # Pure black
        fg = "#00ff41"          # Matrix green
        accent = "#00ff41"      # Neon green
        surface = "#0d1117"     # Dark surface
        green = "#00ff41"       # Matrix green
        red = "#ff0040"         # Neon red
        yellow = "#ffb800"      # Amber warning
        cyan = "#00e5ff"        # Cyan accent
        dim = "#1a3a1a"         # Dim green bg
        border = "#003300"      # Dark green border

        mono = "Consolas"       # Monospace font

        style.configure(".", background=bg, foreground=fg, font=(mono, 10))
        style.configure("TNotebook", background=bg, borderwidth=0)
        style.configure("TNotebook.Tab", background="#001a00", foreground=green,
                        padding=[16, 8], font=(mono, 10, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", "#003300")],
                  foreground=[("selected", "#00ff41")])
        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=fg, font=(mono, 10))
        style.configure("Title.TLabel", font=(mono, 14, "bold"), foreground=cyan)
        style.configure("Header.TLabel", font=(mono, 11, "bold"), foreground=green)
        style.configure("Stat.TLabel", font=(mono, 22, "bold"), foreground=cyan)
        style.configure("StatDesc.TLabel", font=(mono, 9), foreground="#00aa2a")
        style.configure("Signal.TLabel", font=(mono, 10, "bold"))
        style.configure("Banner.TLabel", font=(mono, 7), foreground=green, background=bg)

        # Buttons - hacker style
        style.configure("Accent.TButton", background="#003300", foreground=green,
                        font=(mono, 10, "bold"), padding=[12, 6],
                        borderwidth=1, relief="solid")
        style.map("Accent.TButton",
                  background=[("active", "#004400"), ("pressed", "#005500")],
                  foreground=[("active", "#00ff41")])
        style.configure("Danger.TButton", background="#330000", foreground=red,
                        font=(mono, 10, "bold"), padding=[12, 6])
        style.map("Danger.TButton",
                  background=[("active", "#440000")],
                  foreground=[("active", red)])
        style.configure("Green.TButton", background="#002200", foreground=green,
                        font=(mono, 10, "bold"), padding=[12, 6])
        style.map("Green.TButton",
                  background=[("active", "#003300")])
        style.configure("Cyan.TButton", background="#001a22", foreground=cyan,
                        font=(mono, 10, "bold"), padding=[12, 6])
        style.map("Cyan.TButton",
                  background=[("active", "#002233")])

        # Treeview - terminal style
        style.configure("Treeview", background="#0d1117", foreground=green,
                        fieldbackground="#0d1117", rowheight=26,
                        font=(mono, 9))
        style.configure("Treeview.Heading", background="#001a00", foreground=cyan,
                        font=(mono, 9, "bold"))
        style.map("Treeview",
                  background=[("selected", "#003300")],
                  foreground=[("selected", "#00ff41")])

        style.configure("TLabelframe", background=bg, foreground=green,
                        font=(mono, 10, "bold"))
        style.configure("TLabelframe.Label", background=bg, foreground=cyan)

        # Progress bars
        style.configure("Green.Horizontal.TProgressbar", troughcolor="#0d1117",
                        background=green, thickness=18)
        style.configure("Yellow.Horizontal.TProgressbar", troughcolor="#0d1117",
                        background=yellow, thickness=18)
        style.configure("Red.Horizontal.TProgressbar", troughcolor="#0d1117",
                        background=red, thickness=18)

        # Entry / Combobox
        style.configure("TEntry", fieldbackground="#0d1117", foreground=green,
                        insertcolor=green)
        style.configure("TCombobox", fieldbackground="#0d1117", foreground=green,
                        selectbackground="#003300", selectforeground=green)
        style.map("TCombobox",
                  fieldbackground=[("readonly", "#0d1117")],
                  foreground=[("readonly", green)])

        # Checkbutton
        style.configure("TCheckbutton", background=bg, foreground=green,
                        font=(mono, 9))
        style.map("TCheckbutton", background=[("active", bg)])

        # Scrollbar
        style.configure("TScrollbar", background="#001a00", troughcolor=bg,
                        arrowcolor=green)

    def _start_matrix_rain(self):
        """Animate the status bar with matrix-style random chars."""
        pass  # will animate via status updates

    def _build_ui(self):
        # ─── Top banner ───
        banner_frame = tk.Frame(self, bg="#0a0a0a")
        banner_frame.pack(fill=tk.X, padx=5, pady=(2, 0))

        self.banner_label = tk.Label(
            banner_frame, text=HACKER_BANNER, font=("Consolas", 6),
            fg="#00ff41", bg="#0a0a0a", justify=tk.LEFT, anchor=tk.W
        )
        self.banner_label.pack(side=tk.LEFT, padx=10)

        # Right side info panel
        info_frame = tk.Frame(banner_frame, bg="#0a0a0a")
        info_frame.pack(side=tk.RIGHT, padx=15, pady=5)

        self.time_var = tk.StringVar(value="")
        tk.Label(info_frame, textvariable=self.time_var, font=("Consolas", 9),
                 fg="#00e5ff", bg="#0a0a0a").pack(anchor=tk.E)

        self.status_var = tk.StringVar(value="[*] SYSTEM READY // AWAITING COMMANDS...")
        tk.Label(info_frame, textvariable=self.status_var, font=("Consolas", 8),
                 fg="#00aa2a", bg="#0a0a0a").pack(anchor=tk.E)

        self._update_clock()

        # ─── Separator line ───
        sep = tk.Frame(self, bg="#003300", height=1)
        sep.pack(fill=tk.X, padx=10, pady=(2, 2))

        # ─── Notebook ───
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 2))

        self._build_scanner_tab()
        self._build_analyzer_tab()
        self._build_signal_tab()
        self._build_connection_tab()
        self._build_profiles_tab()

        # ─── Bottom status bar ───
        bottom = tk.Frame(self, bg="#001100", height=22)
        bottom.pack(fill=tk.X, side=tk.BOTTOM)
        self.matrix_var = tk.StringVar(value="")
        tk.Label(bottom, textvariable=self.matrix_var, font=("Consolas", 7),
                 fg="#004400", bg="#001100", anchor=tk.W).pack(side=tk.LEFT, padx=10)
        tk.Label(bottom, text="[ WIF1-PR0B3 v3.7 | RECON MODULE ]",
                 font=("Consolas", 7), fg="#003300", bg="#001100").pack(side=tk.RIGHT, padx=10)

        self._animate_matrix_bar()

    def _update_clock(self):
        now = datetime.now()
        ts = now.strftime("%Y-%m-%d %H:%M:%S")
        self.time_var.set(f"[SYS] {ts}")
        self.after(1000, self._update_clock)

    def _animate_matrix_bar(self):
        rain = "".join(random.choice(MATRIX_CHARS) for _ in range(120))
        self.matrix_var.set(rain)
        self.after(150, self._animate_matrix_bar)

    # ───────── TAB 1: Scanner ─────────
    def _build_scanner_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  [SCAN]  ")

        # Toolbar
        toolbar = ttk.Frame(tab)
        toolbar.pack(fill=tk.X, padx=10, pady=6)

        ttk.Button(toolbar, text=">> SCAN", style="Accent.TButton",
                   command=self._start_scan).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(toolbar, text=">> EXPORT", style="Cyan.TButton",
                   command=self._export_csv).pack(side=tk.LEFT, padx=(0, 6))

        self.auto_scan_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(toolbar, text="AUTO-REFRESH [10s]",
                        variable=self.auto_scan_var,
                        command=self._toggle_auto_scan).pack(side=tk.LEFT, padx=8)

        self.network_count_var = tk.StringVar(value="[TARGETS: 0]")
        ttk.Label(toolbar, textvariable=self.network_count_var,
                  font=("Consolas", 10, "bold"), foreground="#00e5ff").pack(side=tk.RIGHT)

        # Filter bar
        filter_bar = ttk.Frame(tab)
        filter_bar.pack(fill=tk.X, padx=10, pady=(0, 4))

        ttk.Label(filter_bar, text="FILTER>").pack(side=tk.LEFT, padx=(0, 5))
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", lambda *a: self._apply_filter())
        filter_entry = tk.Entry(filter_bar, textvariable=self.filter_var, width=25,
                                bg="#0d1117", fg="#00ff41", insertbackground="#00ff41",
                                font=("Consolas", 10), relief=tk.FLAT,
                                highlightbackground="#003300", highlightthickness=1)
        filter_entry.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(filter_bar, text="BAND>").pack(side=tk.LEFT, padx=(0, 5))
        self.band_filter = tk.StringVar(value="All")
        band_combo = ttk.Combobox(filter_bar, textvariable=self.band_filter,
                                  values=["All", "2.4 GHz", "5 GHz"],
                                  width=10, state="readonly")
        band_combo.pack(side=tk.LEFT, padx=(0, 10))
        band_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_filter())

        ttk.Label(filter_bar, text="ENC>").pack(side=tk.LEFT, padx=(0, 5))
        self.enc_filter = tk.StringVar(value="All")
        enc_combo = ttk.Combobox(filter_bar, textvariable=self.enc_filter,
                                 values=["All", "Open", "WPA2", "WPA3", "WPA", "WEP"],
                                 width=10, state="readonly")
        enc_combo.pack(side=tk.LEFT)
        enc_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_filter())

        # Treeview
        tree_frame = ttk.Frame(tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        columns = ("ssid", "bssid", "signal", "quality", "channel", "band",
                   "auth", "encryption", "time")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings",
                                 selectmode="browse")

        headings = {
            "ssid": ("SSID", 180), "bssid": ("BSSID", 140),
            "signal": ("Signal %", 70), "quality": ("Quality", 80),
            "channel": ("Ch", 45), "band": ("Band", 70),
            "auth": ("Auth", 100), "encryption": ("Encryption", 80),
            "time": ("Time", 70)
        }
        for col, (text, width) in headings.items():
            self.tree.heading(col, text=text,
                              command=lambda c=col: self._sort_tree(c))
            self.tree.column(col, width=width, anchor=tk.CENTER if col != "ssid" else tk.W)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_network_select)

        # Detail panel
        self.detail_frame = ttk.LabelFrame(tab, text="[ TARGET DETAILS ]", padding=8)
        self.detail_frame.pack(fill=tk.X, padx=10, pady=(0, 8))
        self.detail_var = tk.StringVar(value="[*] Select target for reconnaissance...")
        ttk.Label(self.detail_frame, textvariable=self.detail_var,
                  font=("Consolas", 9), foreground="#00e5ff", wraplength=1050).pack(anchor=tk.W)

    # ───────── TAB 2: Analyzer ─────────
    def _build_analyzer_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  [ANALYZE]  ")

        # Stats row
        stats_frame = ttk.Frame(tab)
        stats_frame.pack(fill=tk.X, padx=12, pady=10)

        self.stat_vars = {}
        stat_items = [
            ("total", "TARGETS", "0"),
            ("band24", "2.4GHz", "0"),
            ("band5", "5GHz", "0"),
            ("open", "OPEN/VULN", "0"),
            ("avg_signal", "AVG SIG", "0%"),
            ("best", "STRONGEST", "N/A"),
        ]
        for i, (key, desc, default) in enumerate(stat_items):
            card = ttk.LabelFrame(stats_frame, text=f"[{desc}]", padding=8)
            card.grid(row=0, column=i, padx=6, pady=5, sticky="nsew")
            stats_frame.columnconfigure(i, weight=1)

            self.stat_vars[key] = tk.StringVar(value=default)
            ttk.Label(card, textvariable=self.stat_vars[key],
                      style="Stat.TLabel").pack()

        # Charts area
        self.chart_frame = ttk.Frame(tab)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 10))

        if HAS_MATPLOTLIB:
            self.fig = Figure(figsize=(10, 4), facecolor="#0a0a0a")
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        else:
            self.analysis_text = tk.Text(self.chart_frame, bg="#0d1117", fg="#00ff41",
                                         font=("Consolas", 10), wrap=tk.WORD,
                                         relief=tk.FLAT, padx=10, pady=10,
                                         insertbackground="#00ff41")
            self.analysis_text.pack(fill=tk.BOTH, expand=True)

    # ───────── TAB 3: Signal Monitor ─────────
    def _build_signal_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  [SIGNAL]  ")

        ctrl_frame = ttk.Frame(tab)
        ctrl_frame.pack(fill=tk.X, padx=15, pady=8)

        ttk.Label(ctrl_frame, text="TARGET>",
                  style="Header.TLabel").pack(side=tk.LEFT, padx=(0, 8))
        self.monitor_network = tk.StringVar()
        self.monitor_combo = ttk.Combobox(ctrl_frame, textvariable=self.monitor_network,
                                          width=30, state="readonly")
        self.monitor_combo.pack(side=tk.LEFT, padx=(0, 12))

        self.monitor_btn = ttk.Button(ctrl_frame, text=">> LOCK ON",
                                      style="Accent.TButton",
                                      command=self._toggle_monitoring)
        self.monitor_btn.pack(side=tk.LEFT)

        # Signal display
        sig_frame = ttk.Frame(tab)
        sig_frame.pack(fill=tk.X, padx=15, pady=5)

        self.current_signal_var = tk.StringVar(value="-- %")
        tk.Label(sig_frame, textvariable=self.current_signal_var,
                 font=("Consolas", 52, "bold"), fg="#00ff41", bg="#0a0a0a").pack()

        self.signal_bar = ttk.Progressbar(sig_frame, length=650, maximum=100,
                                          style="Green.Horizontal.TProgressbar")
        self.signal_bar.pack(pady=5)

        self.signal_quality_var = tk.StringVar(value="")
        ttk.Label(sig_frame, textvariable=self.signal_quality_var,
                  font=("Consolas", 11, "bold")).pack()

        # Signal graph
        self.signal_graph_frame = ttk.LabelFrame(tab, text="[ SIGNAL TRACE ]", padding=5)
        self.signal_graph_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(5, 10))

        if HAS_MATPLOTLIB:
            self.sig_fig = Figure(figsize=(8, 3), facecolor="#0a0a0a")
            self.sig_ax = self.sig_fig.add_subplot(111)
            self.sig_canvas = FigureCanvasTkAgg(self.sig_fig, self.signal_graph_frame)
            self.sig_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            self.signal_data = []
        else:
            self.signal_text = tk.Text(self.signal_graph_frame, bg="#0d1117",
                                       fg="#00ff41", font=("Consolas", 9),
                                       height=10, relief=tk.FLAT,
                                       insertbackground="#00ff41")
            self.signal_text.pack(fill=tk.BOTH, expand=True)
            self.signal_data = []

    # ───────── TAB 4: Connection Info ─────────
    def _build_connection_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  [CONN]  ")

        ttk.Button(tab, text=">> REFRESH", style="Accent.TButton",
                   command=self._refresh_connection).pack(padx=15, pady=8, anchor=tk.W)

        self.conn_text = tk.Text(tab, bg="#0d1117", fg="#00ff41",
                                 font=("Consolas", 10), wrap=tk.WORD,
                                 relief=tk.FLAT, padx=15, pady=15,
                                 insertbackground="#00ff41",
                                 selectbackground="#003300")
        self.conn_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

    # ───────── TAB 5: Saved Profiles ─────────
    def _build_profiles_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  [PROFILES]  ")

        ttk.Button(tab, text=">> LOAD PROFILES", style="Accent.TButton",
                   command=self._load_profiles).pack(padx=15, pady=8, anchor=tk.W)

        columns = ("name",)
        self.profiles_tree = ttk.Treeview(tab, columns=columns, show="headings")
        self.profiles_tree.heading("name", text="STORED NETWORK PROFILES")
        self.profiles_tree.column("name", width=400)
        self.profiles_tree.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

    # ───────── Scanning Logic ─────────
    def _initial_scan(self):
        self._start_scan()

    def _start_scan(self):
        self.status_var.set("[*] INITIATING SCAN...")
        threading.Thread(target=self._scan_thread, daemon=True).start()

    def _scan_thread(self):
        self.after(0, lambda: self.status_var.set("[>>] PROBING AIRSPACE // HW SCAN IN PROGRESS..."))
        result = scan_wifi_networks(scan_duration=4)
        if result == "PYWIFI_MISSING":
            self.after(0, lambda: messagebox.showerror(
                "Missing pywifi", "Install pywifi: pip install pywifi comtypes"))
            return
        if result == "NO_INTERFACE":
            self.after(0, lambda: messagebox.showerror(
                "No WiFi", "No WiFi adapter found on this machine."))
            return
        self.networks = result
        self.scan_history.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "count": len(result),
            "networks": result
        })
        self.after(0, self._update_ui)

    def _update_ui(self):
        self._populate_tree(self.networks)
        self._update_analyzer()
        self._update_monitor_combo()
        self.network_count_var.set(f"[TARGETS: {len(self.networks)}]")
        self.status_var.set(
            f"[+] SCAN COMPLETE // {len(self.networks)} targets acquired "
            f"@ {datetime.now().strftime('%H:%M:%S')}"
        )

    def _populate_tree(self, networks):
        self.tree.delete(*self.tree.get_children())
        for net in networks:
            tags = ()
            if net.signal >= 70:
                tags = ("strong",)
            elif net.signal >= 40:
                tags = ("medium",)
            else:
                tags = ("weak",)

            self.tree.insert("", tk.END, values=(
                net.ssid, net.bssid, f"{net.signal}%", net.signal_quality,
                net.channel, net.band, net.auth, net.encryption, net.timestamp
            ), tags=tags)

        self.tree.tag_configure("strong", foreground="#00ff41")
        self.tree.tag_configure("medium", foreground="#ffb800")
        self.tree.tag_configure("weak", foreground="#ff0040")

    def _apply_filter(self):
        text = self.filter_var.get().lower()
        band = self.band_filter.get()
        enc = self.enc_filter.get()

        filtered = []
        for net in self.networks:
            if text and text not in net.ssid.lower() and text not in net.bssid.lower():
                continue
            if band != "All" and net.band != band:
                continue
            if enc != "All":
                if enc == "Open" and net.encryption != "None":
                    continue
                elif enc != "Open" and enc.lower() not in net.auth.lower():
                    continue
            filtered.append(net)

        self._populate_tree(filtered)
        self.network_count_var.set(f"[TARGETS: {len(filtered)}]")

    def _sort_tree(self, col):
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        try:
            items.sort(key=lambda t: int(t[0].replace("%", "")), reverse=True)
        except ValueError:
            items.sort(key=lambda t: t[0].lower())

        for idx, (_, k) in enumerate(items):
            self.tree.move(k, "", idx)

    def _on_network_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0], "values")
        detail = (
            f"[SSID] {values[0]}  //  [BSSID] {values[1]}  //  "
            f"[SIG] {values[2]} ({values[3]})  //  [CH] {values[4]}  //  "
            f"[BAND] {values[5]}  //  [AUTH] {values[6]}  //  "
            f"[ENC] {values[7]}  //  [TIME] {values[8]}"
        )
        self.detail_var.set(detail)

    def _toggle_auto_scan(self):
        if self.auto_scan_var.get():
            self._auto_scan_loop()

    def _auto_scan_loop(self):
        if self.auto_scan_var.get():
            self._start_scan()
            self.after(10000, self._auto_scan_loop)

    # ───────── Analyzer Logic ─────────
    def _update_analyzer(self):
        nets = self.networks
        if not nets:
            return

        total = len(nets)
        band24 = sum(1 for n in nets if n.band == "2.4 GHz")
        band5 = sum(1 for n in nets if n.band == "5 GHz")
        open_nets = sum(1 for n in nets if n.encryption == "None")
        avg_sig = sum(n.signal for n in nets) // total if total else 0
        best = max(nets, key=lambda n: n.signal)

        self.stat_vars["total"].set(str(total))
        self.stat_vars["band24"].set(str(band24))
        self.stat_vars["band5"].set(str(band5))
        self.stat_vars["open"].set(str(open_nets))
        self.stat_vars["avg_signal"].set(f"{avg_sig}%")
        self.stat_vars["best"].set(best.ssid[:20])

        if HAS_MATPLOTLIB:
            self._draw_charts()
        else:
            self._draw_text_analysis()

    def _draw_charts(self):
        self.fig.clear()
        nets = self.networks

        # Chart 1: Channel distribution
        ax1 = self.fig.add_subplot(131)
        channels = Counter(n.channel for n in nets)
        ch_sorted = sorted(channels.items())
        if ch_sorted:
            ax1.bar([str(c) for c, _ in ch_sorted],
                    [cnt for _, cnt in ch_sorted],
                    color="#00ff41", edgecolor="#003300", alpha=0.85)
            ax1.set_title("CHANNEL MAP", color="#00e5ff", fontsize=9, fontfamily="monospace")
            ax1.set_facecolor("#0d1117")
            ax1.tick_params(colors="#00aa2a", labelsize=7)
            ax1.spines[:].set_color("#003300")

        # Chart 2: Encryption types pie
        ax2 = self.fig.add_subplot(132)
        auth_counts = Counter(n.auth for n in nets)
        if auth_counts:
            colors = ["#00ff41", "#00e5ff", "#ffb800", "#ff0040",
                      "#00ff88", "#44ffaa", "#ff6600"]
            ax2.pie(auth_counts.values(), labels=auth_counts.keys(),
                    autopct="%1.0f%%", colors=colors[:len(auth_counts)],
                    textprops={"color": "#00ff41", "fontsize": 7, "fontfamily": "monospace"},
                    wedgeprops={"edgecolor": "#0a0a0a", "linewidth": 1.5})
            ax2.set_title("AUTH TYPES", color="#00e5ff", fontsize=9, fontfamily="monospace")

        # Chart 3: Signal strength distribution
        ax3 = self.fig.add_subplot(133)
        signals = [n.signal for n in nets]
        ranges = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
        for s in signals:
            if s <= 20: ranges["0-20"] += 1
            elif s <= 40: ranges["21-40"] += 1
            elif s <= 60: ranges["41-60"] += 1
            elif s <= 80: ranges["61-80"] += 1
            else: ranges["81-100"] += 1
        bar_colors = ["#ff0040", "#ff6600", "#ffb800", "#00ff41", "#00e5ff"]
        ax3.bar(ranges.keys(), ranges.values(), color=bar_colors, edgecolor="#003300")
        ax3.set_title("SIGNAL DIST", color="#00e5ff", fontsize=9, fontfamily="monospace")
        ax3.set_facecolor("#0d1117")
        ax3.tick_params(colors="#00aa2a", labelsize=7)
        ax3.spines[:].set_color("#003300")

        self.fig.tight_layout(pad=2.0)
        self.canvas.draw()

    def _draw_text_analysis(self):
        self.analysis_text.delete("1.0", tk.END)
        nets = self.networks

        channels = Counter(n.channel for n in nets)
        auths = Counter(n.auth for n in nets)
        bands = Counter(n.band for n in nets)

        text = "\n  ┌───────────────────────────────────────────────┐\n"
        text += "  │           [CHANNEL FREQUENCY MAP]              │\n"
        text += "  └───────────────────────────────────────────────┘\n"
        for ch, cnt in sorted(channels.items()):
            bar = "█" * min(cnt, 20) + "░" * max(0, 20 - cnt)
            text += f"   CH {ch:>3} ║ [{bar}] {cnt}\n"

        text += "\n  ┌───────────────────────────────────────────────┐\n"
        text += "  │           [AUTHENTICATION ANALYSIS]            │\n"
        text += "  └───────────────────────────────────────────────┘\n"
        for auth, cnt in auths.most_common():
            text += f"   {auth:<25} >> {cnt} targets\n"

        text += "\n  ┌───────────────────────────────────────────────┐\n"
        text += "  │           [FREQUENCY BAND SPLIT]               │\n"
        text += "  └───────────────────────────────────────────────┘\n"
        for band, cnt in bands.items():
            pct = cnt * 100 // len(nets)
            bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
            text += f"   {band} ║ [{bar}] {cnt} ({pct}%)\n"

        text += "\n  ┌───────────────────────────────────────────────┐\n"
        text += "  │           [TOP 10 STRONGEST TARGETS]           │\n"
        text += "  └───────────────────────────────────────────────┘\n"
        for net in sorted(nets, key=lambda n: n.signal, reverse=True)[:10]:
            bar = "█" * (net.signal // 5) + "░" * (20 - net.signal // 5)
            text += f"   {net.ssid[:25]:<25} [{bar}] {net.signal}%\n"

        self.analysis_text.insert("1.0", text)

    # ───────── Signal Monitor ─────────
    def _update_monitor_combo(self):
        ssids = sorted(set(n.ssid for n in self.networks if n.ssid != "[Hidden Network]"))
        self.monitor_combo["values"] = ssids

    def _toggle_monitoring(self):
        if self.monitoring:
            self.monitoring = False
            self.monitor_btn.configure(text=">> LOCK ON")
        else:
            if not self.monitor_network.get():
                messagebox.showinfo("Select Network", "Please select a network to monitor.")
                return
            self.monitoring = True
            self.signal_data = []
            self.monitor_btn.configure(text=">> DISENGAGE")
            threading.Thread(target=self._monitor_loop, daemon=True).start()

    def _monitor_loop(self):
        while self.monitoring:
            networks = scan_wifi_networks(scan_duration=2)
            if isinstance(networks, str):
                # Error string returned
                time.sleep(3)
                continue
            target = self.monitor_network.get()
            matched = [n for n in networks if n.ssid == target]
            if matched:
                sig = max(n.signal for n in matched)
                self.signal_data.append(sig)
                if len(self.signal_data) > 60:
                    self.signal_data = self.signal_data[-60:]
                self.after(0, lambda s=sig: self._update_signal_display(s))
            else:
                self.after(0, lambda: self._update_signal_display(0))
            time.sleep(1)

    def _update_signal_display(self, signal):
        self.current_signal_var.set(f"{signal}%")
        self.signal_bar["value"] = signal

        if signal >= 70:
            self.signal_bar.configure(style="Green.Horizontal.TProgressbar")
            quality = "[+] SIGNAL LOCKED // EXCELLENT"
        elif signal >= 40:
            self.signal_bar.configure(style="Yellow.Horizontal.TProgressbar")
            quality = "[~] SIGNAL UNSTABLE // FAIR"
        else:
            self.signal_bar.configure(style="Red.Horizontal.TProgressbar")
            quality = "[!] SIGNAL WEAK // CRITICAL"
        self.signal_quality_var.set(quality)

        if HAS_MATPLOTLIB:
            self.sig_ax.clear()
            self.sig_ax.set_facecolor("#0d1117")
            if self.signal_data:
                x = list(range(len(self.signal_data)))
                self.sig_ax.fill_between(x, self.signal_data, alpha=0.2, color="#00ff41")
                self.sig_ax.plot(x, self.signal_data, color="#00ff41", linewidth=2)
                self.sig_ax.set_ylim(0, 100)
                self.sig_ax.set_ylabel("SIG %", color="#00aa2a", fontsize=8, fontfamily="monospace")
                self.sig_ax.set_xlabel("SAMPLES", color="#00aa2a", fontsize=8, fontfamily="monospace")
                self.sig_ax.tick_params(colors="#00aa2a")
                self.sig_ax.axhline(y=70, color="#00ff41", linestyle="--", alpha=0.4)
                self.sig_ax.axhline(y=40, color="#ffb800", linestyle="--", alpha=0.4)
                self.sig_ax.spines[:].set_color("#003300")
            self.sig_canvas.draw()
        else:
            self.signal_text.delete("1.0", tk.END)
            if self.signal_data:
                max_width = 50
                text = f"  [TRACE] Signal log // {len(self.signal_data)} samples captured\n\n"
                for i, s in enumerate(self.signal_data[-20:]):
                    bar_len = int(s / 100 * max_width)
                    bar = "█" * bar_len + "░" * (max_width - bar_len)
                    text += f"  {i+1:>3} ║ [{bar}] {s}%\n"
                text += f"\n  [MIN] {min(self.signal_data)}%  //  "
                text += f"[MAX] {max(self.signal_data)}%  //  "
                text += f"[AVG] {sum(self.signal_data)//len(self.signal_data)}%"
                self.signal_text.insert("1.0", text)

    # ───────── Connection Info ─────────
    def _refresh_connection(self):
        self.conn_text.delete("1.0", tk.END)
        self.conn_text.insert("1.0", "Loading...\n")
        threading.Thread(target=self._load_connection, daemon=True).start()

    def _load_connection(self):
        info = get_current_connection()
        text = "  ┌─────────────────────────────────────────────────┐\n"
        text += "  │         [ACTIVE CONNECTION INTERFACE]            │\n"
        text += "  └─────────────────────────────────────────────────┘\n\n"
        important_keys = [
            "Name", "Description", "GUID", "Physical address",
            "State", "SSID", "BSSID", "Network type", "Radio type",
            "Authentication", "Cipher", "Connection mode", "Band",
            "Channel", "Receive rate (Mbps)", "Transmit rate (Mbps)",
            "Signal", "Profile"
        ]
        for key in important_keys:
            if key in info:
                text += f"   {key:<25} >> {info[key]}\n"

        text += "\n  ┌─────────────────────────────────────────────────┐\n"
        text += "  │         [RAW INTERFACE DUMP]                     │\n"
        text += "  └─────────────────────────────────────────────────┘\n\n"
        for key, value in info.items():
            if key not in important_keys:
                text += f"   {key:<25} >> {value}\n"

        self.after(0, lambda: self._set_conn_text(text))

    def _set_conn_text(self, text):
        self.conn_text.delete("1.0", tk.END)
        self.conn_text.insert("1.0", text)

    # ───────── Saved Profiles ─────────
    def _load_profiles(self):
        self.profiles_tree.delete(*self.profiles_tree.get_children())
        profiles = get_saved_profiles()
        for p in profiles:
            self.profiles_tree.insert("", tk.END, values=(p,))

    # ───────── Export ─────────
    def _export_csv(self):
        if not self.networks:
            messagebox.showinfo("No Data", "Run a scan first.")
            return
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"wifi_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        if not filepath:
            return
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["SSID", "BSSID", "Signal", "Quality", "Channel",
                             "Band", "Auth", "Encryption", "Time"])
            for net in self.networks:
                writer.writerow([
                    net.ssid, net.bssid, f"{net.signal}%", net.signal_quality,
                    net.channel, net.band, net.auth, net.encryption, net.timestamp
                ])
        messagebox.showinfo("[+] EXPORT COMPLETE", f"Data saved >>\n{filepath}")
        self.status_var.set(f"[+] EXPORTED {len(self.networks)} targets to CSV")


if __name__ == "__main__":
    app = WiFiToolkit()
    app.mainloop()
