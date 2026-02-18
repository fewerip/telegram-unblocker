# Telegram Unblocker (Desktop Throttling Bypass)

Bypasses ISP throttling of Telegram Desktop by wrapping connection traffic in a fragmented SOCKS5 tunnel. 

## The Problem
Many ISPs throttle Telegram Desktop traffic (MTProto) at the DPI level. Standard SOCKS5 proxies are also detected and throttled because the handshake signature is widely known.

## The Solution
This tool creates a local SOCKS5 proxy that chains to your external SOCKS5 proxy. Crucially, it **fragments the SOCKS5 handshake** into small random chunks. This fragmentation breaks the signature detection of DPI systems (similar to 'Zapret'), allowing full-speed connection.

## Components
-   `Manage.bat`: The main control panel (Configuration, Installation, Removal).
-   `bin/TelegramUnblocker.exe`: The core engine (handles the traffic).
-   `bin/config.json`: Stores your proxy settings.

## How to Use

### 1. Requirements
-   A working **External SOCKS5 Proxy** (IP, Port, User, Pass).
-   Windows 10/11.

### 2. Setup
1.  Run `Manage.bat`.
2.  Choose **Option 1 (Configure Proxy)**.
    -   Enter your **Local Port** (Default: `10805`).
    -   Enter your **External Proxy IP** and **Port**.
    -   Enter **Username/Password** (or leave empty if not required).

### 3. Usage
-   **Test Mode**: Choose **Option 2**. This runs the proxy in a console window. Useful for checking if it works.
-   **Install as Service**: Choose **Option 3**. The proxy will install itself as a Windows Service (`TelegramUnblocker`) and run automatically in the background (even after reboot).
-   **Remove Service**: Choose **Option 4**.

### 4. Configure Telegram Desktop
Once the proxy is running (Test Mode or Service), configure Telegram:

1.  Open Telegram Desktop.
2.  Go to **Settings** (Three bars top left -> Settings).
3.  Click **Data and Storage**.
4.  Scroll down to **Server Settings / Connection Type**.
5.  Click **Use Proxy** (or "Add Proxy").
6.  Select **SOCKS5**.
7.  **Socket Address**: `127.0.0.1`
8.  **Port**: `10805` (or whatever you set in Config).
9.  **Username/Password**: (Leave Empty).
10. Click **Save**.

The shield icon should verify the connection.

## Building from Source

If you want to compile the EXE yourself:
1.  Install Python.
2.  Install dependencies: `pip install pyinstaller pywin32`
3.  Run `build.bat`.
