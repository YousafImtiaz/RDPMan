import os
import json
import subprocess
import signal
import sys
import time
import shlex

# File to store saved connections
SAVE_FILE = 'saved_connections.json'

# Store active RDP processes
active_processes = []

# Clear the terminal screen
def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

# Load saved connections from the file
def load_connections():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, 'r') as f:
            return json.load(f)
    return {}

# Save connections to the file
def save_connections(connections):
    with open(SAVE_FILE, 'w') as f:
        json.dump(connections, f, indent=4)

# List saved connections
def list_connections(connections):
    if not connections:
        print("  No saved connections found.\n")
        return False
    else:
        print("\n  Saved Connections:")
        for idx, (key, value) in enumerate(connections.items(), 1):
            hostname_info = f", \033[1mHostname\033[0m: \033[1;32m{value['hostname']}\033[0m" if value.get('hostname') else ""
            print(f"  {idx}. \033[1mIP\033[0m: \033[1;32m{key}\033[0m, \033[1mUsername\033[0m: \033[1;32m{value['username']}\033[0m, \033[1mPassword\033[0m: \033[1;32m{value['password']}\033[0m{hostname_info}")
        print("")
        return True

# Delete a saved connection
def delete_connection(connections):
    if not connections:
        print("  No saved connections found.\n")
        return

    list_connections(connections)
    try:
        idx = int(input("  Enter the number of the connection to delete: "))
        ip = list(connections.keys())[idx - 1]
        del connections[ip]
        save_connections(connections)
        print(f"  Connection to {ip} deleted.\n")
    except (ValueError, IndexError):
        print("  Invalid selection. No changes made.\n")

# Add or update a saved connection
def add_connection(connections):
    print("\n  Adding a new connection:")

    ip = input("  Enter IP address: ")
    username = input("  Enter username: ")
    password = input("  Enter password: ")
    hostname = input("  Enter hostname (optional, for display only): ").strip()

    connections[ip] = {
        'username': username, 
        'password': password,
        'hostname': hostname
    }
    save_connections(connections)
    print(f"  Connection to {ip} saved.\n")

    connect_now = input("  Connect now? (y/n): ").strip().lower()
    if connect_now == 'y':
        run_xfreerdp(ip, username, password)

# Check if a session is already running for this IP
def is_session_running(ip):
    for session in active_processes:
        if session['ip'] == ip:
            # Check if process is still running
            if session['process'].poll() is None:
                return True
            else:
                # Remove dead process from list
                active_processes.remove(session)
                return False
    return False

# Run xfreerdp3 with selected details in the background
def run_xfreerdp(ip, username, password):
    # Check if session already running
    if is_session_running(ip):
        print(f"\n  ⚠️  RDP session to {ip} is already running.\n")
        return
    
    # Build command with xfreerdp3 syntax
    command = [
        "xfreerdp3",
        "+cert:ignore",
        "+compression",
        "+auto-reconnect",
        f"+u:{username}",
        f"+p:{password}",
        f"+v:{ip}",
        "+dynamic-resolution",
        "+clipboard"
    ]
    
    print(f"\n  Connecting to {ip}...")
    
    try:
        # Run in background with output suppressed
        process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True
        )
        
        # Store the process with username
        active_processes.append({
            'ip': ip,
            'username': username,
            'process': process,
            'pid': process.pid
        })
        
        # Check if process started successfully
        time.sleep(1)
        if process.poll() is None:
            print(f"  RDP session to {ip} started successfully (PID: {process.pid})")
            print(f"  The RDP window should open shortly.\n")
        else:
            print(f"  RDP session to {ip} failed to start.\n")
            
    except FileNotFoundError:
        print("  Error: xfreerdp3 not found. Please install FreeRDP3.")
        print("     Ubuntu/Debian: sudo apt-get install freerdp3-x11")
        print("     macOS: brew install freerdp\n")
    except Exception as e:
        print(f"  Error connecting: {e}\n")

# Kill an active RDP session
def kill_session(ip):
    for session in active_processes:
        if session['ip'] == ip:
            try:
                session['process'].terminate()
                time.sleep(0.5)
                if session['process'].poll() is None:
                    session['process'].kill()
                active_processes.remove(session)
                print(f"  RDP session to {ip} terminated.\n")
                return True
            except:
                print(f"  Failed to terminate session to {ip}\n")
                return False
    print(f"  No active session found for {ip}\n")
    return False

# List active RDP sessions
def list_active_sessions():
    # Clean up any dead processes first
    for session in active_processes[:]:
        if session['process'].poll() is not None:
            active_processes.remove(session)
    
    if not active_processes:
        print("  No active RDP sessions.\n")
        return
    
    print("\n  Active RDP Sessions:")
    for idx, session in enumerate(active_processes, 1):
        # Get hostname from saved connections
        connections = load_connections()
        hostname = connections.get(session['ip'], {}).get('hostname', '')
        hostname_info = f" - \033[1mHostname\033[0m: \033[1;32m{hostname}\033[0m" if hostname else ""
        status = "Running" if session['process'].poll() is None else "Terminated"
        print(f"  {idx}. \033[1mIP\033[0m: \033[1;32m{session['ip']}\033[0m{hostname_info} (\033[1mPID\033[0m: {session['pid']}) - {status} - \033[1mUser\033[0m: \033[1;32m{session['username']}\033[0m")
    print("")

# Handle Ctrl+C - Show message but don't exit
def handle_ctrl_c(signal_received, frame):
    print(f"\n\n  \033[1;33m⚠️  Ctrl+C detected. Press 7 and ENTER for options.\033[0m")
    # Don't exit - just show the message

# Handle graceful exit from menu
def handle_exit():
    print("\n\n  \033[1;31mWARNING: Exiting will terminate all active RDP sessions.\033[0m")
    confirm = input("  Are you sure you want to exit? (y/n): ").strip().lower()
    if confirm == 'y':
        print("\n  Terminating active RDP sessions...")
        for session in active_processes:
            try:
                session['process'].terminate()
            except:
                pass
        print("  Exiting RDPMan...")
        sys.exit(0)
    else:
        print("  Exit cancelled.\n")
        return

# Main function for CLI interaction
def main():
    signal.signal(signal.SIGINT, handle_ctrl_c)  # Ctrl+C just shows a message
    
    while True:
        clear_screen()
        connections = load_connections()
        
        print("\n  \033[1;31mRDP Manager\033[0m")
        print("  " + "=" * 30)
        print("  [1] List saved connections")
        print("  [2] Add new connection")
        print("  [3] Delete a connection")
        print("  [4] Connect to a saved connection")
        print("  [5] List active RDP sessions")
        print("  [6] Terminate an RDP session")
        print("  [7] Exit")
        print("  " + "=" * 30)
        print("  > \033[1;33mRDPMan\033[0m", end=" ")
        
        try:
            choice = input().strip()
        except KeyboardInterrupt:
            # This shouldn't happen as signal handler catches it
            continue
        
        if choice == '1':
            clear_screen()
            print("\n  \033[1;34m[Saved Connections]\033[0m\n")
            list_connections(connections)
            input("  Press Enter to continue...")
        elif choice == '2':
            clear_screen()
            print("\n  \033[1;34m[Add Connection]\033[0m\n")
            add_connection(connections)
            input("  Press Enter to continue...")
        elif choice == '3':
            clear_screen()
            print("\n  \033[1;34m[Delete Connection]\033[0m\n")
            delete_connection(connections)
            input("  Press Enter to continue...")
        elif choice == '4':
            clear_screen()
            print("\n  \033[1;34m[Connect to Saved Connection]\033[0m\n")
            if list_connections(connections):
                try:
                    idx = int(input("  Enter the number of the connection to connect: "))
                    ip = list(connections.keys())[idx - 1]
                    username = connections[ip]['username']
                    password = connections[ip]['password']
                    run_xfreerdp(ip, username, password)
                except (ValueError, IndexError):
                    print("  Invalid selection. No changes made.\n")
            input("  Press Enter to continue...")
        elif choice == '5':
            clear_screen()
            print("\n  \033[1;34m[Active RDP Sessions]\033[0m\n")
            list_active_sessions()
            input("  Press Enter to continue...")
        elif choice == '6':
            clear_screen()
            print("\n  \033[1;34m[Terminate RDP Session]\033[0m\n")
            if active_processes:
                list_active_sessions()
                try:
                    idx = int(input("  Enter the number of the session to terminate: "))
                    ip = active_processes[idx - 1]['ip']
                    kill_session(ip)
                except (ValueError, IndexError):
                    print("  Invalid selection. No changes made.\n")
            else:
                print("  No active RDP sessions to terminate.\n")
            input("  Press Enter to continue...")
        elif choice == '7':
            handle_exit()
        else:
            clear_screen()
            print("\n  Invalid choice, please enter a number between 1 and 7.\n")
            input("  Press Enter to continue...")

if __name__ == "__main__":
    main()
