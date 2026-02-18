import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import select
import threading
import time
import random
import sys
import os
import json
import ctypes

# --- CONSTANTS ---
CONFIG_FILE = "config.json"
SERVICE_NAME = "TelegramUnblocker"
SERVICE_DISPLAY = "Telegram Unblocker Service"
SERVICE_DESC = "Bypasses Telegram throttling using Chained Fragmentation Proxy."

# --- PROXY LOGIC ---
class ProxyConfig:
    def __init__(self):
        self.local_port = 10805
        self.remote_ip = ""
        self.remote_port = 0
        self.remote_user = ""
        self.remote_pass = ""

    def get_config_path(self):
        # Reliable path for both Service and Console (frozen exe)
        # sys.executable is the full path to the .exe
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        return os.path.join(exe_dir, CONFIG_FILE)

    def load(self):
        path = self.get_config_path()
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                self.local_port = data.get('local_port', 10805)
                self.remote_ip = data.get('remote_ip', "")
                self.remote_port = data.get('remote_port', 0)
                self.remote_user = data.get('remote_user', "")
                self.remote_pass = data.get('remote_pass', "")
                log_debug(f"Config Loaded: {path}")
                log_debug(f"Target: {self.remote_ip}:{self.remote_port}")
                return True
        except Exception as e:
            log_debug(f"Config Load Error: {e} | Path: {path}")
            pass
        return False

    def save(self):
        path = self.get_config_path()
        data = {
            'local_port': self.local_port,
            'remote_ip': self.remote_ip,
            'remote_port': self.remote_port,
            'remote_user': self.remote_user,
            'remote_pass': self.remote_pass
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)

# --- DEBUG LOGGER ---
def log_debug(msg):
    # Logs to 'service_log.txt' near the executable
    try:
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        log_path = os.path.join(exe_dir, "service_log.txt")
        with open(log_path, 'a') as f:
             # simple timestamp
             t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
             f.write(f"[{t}] {msg}\n")
    except:
        pass
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)

class ProxyServer:
    def __init__(self, config):
        self.config = config
        self.running = False
        self.server_socket = None
        self.chunk_min = 1
        self.chunk_max = 3
        self.delay = 0.05

    def send_fragmented(self, sock, data):
        total = 0
        while total < len(data):
            chunk_len = random.randint(self.chunk_min, self.chunk_max)
            chunk = data[total:total+chunk_len]
            try:
                sock.sendall(chunk)
                total += len(chunk)
                time.sleep(self.delay)
            except:
                break

    def handle_client(self, client_socket):
        remote_socket = None
        try:
            # 1. Local Handshake
            initial = client_socket.recv(262)
            if not initial or initial[0] != 0x05: return
            client_socket.sendall(b'\x05\x00')

            req = client_socket.recv(8192)
            if not req or len(req) < 7: return
            
            # 2. Connect Remote
            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_socket.connect((self.config.remote_ip, int(self.config.remote_port)))
            
            # 3. Fragmented Auth Negotiation
            # Offer NoAuth (0x00). If we have creds, also offer UserPass (0x02).
            methods = b'\x00'
            if self.config.remote_user:
                methods += b'\x02'
            
            # SOCKS5 Hello: Ver 5, N Methods, Method List
            handshake = b'\x05' + bytes([len(methods)]) + methods
            self.send_fragmented(remote_socket, handshake) 
            
            resp = remote_socket.recv(2)
            if not resp or resp[0] != 0x05: return
            
            selected_method = resp[1]
            
            if selected_method == 0x02:
                # Server wants User/Pass
                if not self.config.remote_user:
                     return # We don't have creds
                
                auth_payload = b'\x01' + bytes([len(self.config.remote_user)]) + self.config.remote_user.encode() + \
                               bytes([len(self.config.remote_pass)]) + self.config.remote_pass.encode()
                self.send_fragmented(remote_socket, auth_payload)
                auth_resp = remote_socket.recv(2)
                if not auth_resp or auth_resp[1] != 0x00: return
                
            elif selected_method == 0x00:
                # No Auth required
                pass
            else:
                return # Unsupported auth method
                
            # 4. Tunnel
            remote_socket.sendall(req)
            remote_reply = remote_socket.recv(8192)
            if not remote_reply or remote_reply[1] != 0x00:
                client_socket.close()
                return
            client_socket.sendall(remote_reply)
            
            # 5. Relay
            while self.running:
                r, w, e = select.select([client_socket, remote_socket], [], [], 1)
                if not r: continue

                if client_socket in r:
                    data = client_socket.recv(8192)
                    if not data: break
                    remote_socket.sendall(data)

                if remote_socket in r:
                    data = remote_socket.recv(8192)
                    if not data: break
                    client_socket.sendall(data)

        except:
            pass
        finally:
            if client_socket: 
                try: client_socket.close()
                except: pass
            if remote_socket: 
                try: remote_socket.close()
                except: pass

    def start(self):
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server_socket.bind(('127.0.0.1', self.config.local_port))
            self.server_socket.listen(50)
            
            while self.running:
                try:
                    self.server_socket.settimeout(1.0)
                    try:
                        client, addr = self.server_socket.accept()
                        t = threading.Thread(target=self.handle_client, args=(client,))
                        t.daemon = True
                        t.start()
                    except socket.timeout:
                        continue
                except:
                    break
        except Exception as e:
            pass

    def stop(self):
        self.running = False
        if self.server_socket:
            try: self.server_socket.close()
            except: pass

# --- SERVICE WRAPPER ---
class AppServerSvc (win32serviceutil.ServiceFramework):
    _svc_name_ = SERVICE_NAME
    _svc_display_name_ = SERVICE_DISPLAY
    _svc_description_ = SERVICE_DESC

    def __init__(self,args):
        win32serviceutil.ServiceFramework.__init__(self,args)
        self.hWaitStop = win32event.CreateEvent(None,0,0,None)
        self.config = ProxyConfig()
        self.config.load() # Load config from EXE directory
        self.proxy = ProxyServer(self.config)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.proxy.stop()

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_,''))
        self.main()

    def main(self):
        if not self.config.remote_ip:
             # Stop if no config
             return
             
        proxy_thread = threading.Thread(target=self.proxy.start)
        proxy_thread.start()
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
        self.proxy.stop()
        proxy_thread.join()

# --- CLI HELPERS ---
def cmd_configure():
    config = ProxyConfig()
    config.load()
    
    print("\n=== Proxy Configuration ===")
    
    # Local Port
    l_p = input(f"Local Port [{config.local_port}]: ")
    if l_p: config.local_port = int(l_p)
    
    print(f"Current Remote: {config.remote_ip}:{config.remote_port}")
    
    c_ip = input(f"Remote IP [{config.remote_ip}]: ")
    if c_ip: config.remote_ip = c_ip
    
    c_port = input(f"Remote Port [{config.remote_port}]: ")
    if c_port: config.remote_port = int(c_port)
    
    print("\n(Leave empty to keep current. Enter '-' to clear credentials)")
    
    c_user = input(f"Username [{config.remote_user}]: ")
    if c_user == '-': config.remote_user = ""
    elif c_user: config.remote_user = c_user
    
    c_pass = input(f"Password [{config.remote_pass}]: ")
    if c_pass == '-': config.remote_pass = ""
    elif c_pass: config.remote_pass = c_pass
    
    config.save()
    print("\n[OK] Configuration Saved to config.json")
    time.sleep(1)

def cmd_test():
    config = ProxyConfig()
    config.load()
    if not config.remote_ip:
        print("[!] Error: Remote IP not configured.")
        return
        
    print(f"[*] Starting Proxy on 127.0.0.1:{config.local_port}...")
    print(f"[*] Upstream: {config.remote_ip}:{config.remote_port}")
    
    print("\n" + "="*50)
    print("   HOW TO CONFIGURE TELEGRAM DESKTOP")
    print("="*50)
    print("1. Open Telegram Settings")
    print("2. Go to: Data and Storage > Connection Type (Proxy Settings)")
    print("3. Click 'Add Proxy'")
    print("4. Select 'SOCKS5'")
    print(f"5. Host: 127.0.0.1")
    print(f"6. Port: {config.local_port}")
    print("7. Username/Password: (Leave Empty)")
    print("8. Click Save")
    print("="*50 + "\n")
    
    print("[*] Proxy is RUNNING. Press Ctrl+C to stop.")
    
    srv = ProxyServer(config)
    try:
        srv.start()
    except KeyboardInterrupt:
        srv.stop()

if __name__ == '__main__':
    # 1. Service Mode Check
    try:
        # If we are being started by SCM, this will block and handle service events
        # If we are just a console app, this throws an error immediately (usually)
        # or we check args first.
        
        # If args are passed, handle them and exit (do NOT try to be a service)
        if len(sys.argv) > 1:
            if sys.argv[1] == '--configure':
                cmd_configure()
            elif sys.argv[1] == '--test':
                cmd_test()
            elif sys.argv[1] == '--install':
                # Helper for the BAT file if needed, but BAT can do 'sc create'
                print("Use Manage.bat to install.")
            else:
                # 'install'/'remove' args might be passed by pywin32 internals if we used HandleCommandLine
                # But we want to avoid that for this "Zapret-style" build.
                pass
        else:
            # No args. Are we a service?
            # Creating a service logic usually requires specific handling.
            # If run from double-click, show Hint.
            # If run from SCM, stdin/stdout might be invalid.
            
            try:
                servicemanager.Initialize()
                servicemanager.PrepareToHostSingle(AppServerSvc)
                servicemanager.StartServiceCtrlDispatcher()
            except:
                # Not a service run
                print("This is the Worker Executable.")
                print("Please run 'Manage.bat' from the parent directory.")
                time.sleep(5)
                
    except Exception as e:
        # Fallback
        pass
