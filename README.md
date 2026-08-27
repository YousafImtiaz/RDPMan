# RDPMan (RDP Manager)

  <img src="https://img.shields.io/badge/🔌_RDPMan-RDP_Connection_Manager-CC0000?style=for-the-badge&logo=windows&logoColor=white" alt="RDPMan" />

RDPMan stores all connection details in one place, allowing for efficient switching between RDP sessions. This is ideal for large corporate networks like the OSEP challenge labs and the exam.

# Usage

> python3 rdpman.py

RDPMan

--- RDP Connection Manager ---
1. List saved connections
2. Add new connection
3. Delete a connection
4. Connect to a saved connection
5. Exit

Enter your choice (1-5): 2

Adding a new connection:
1. Enter IP address: 192.168.x.x
2. Enter username: anonymous
3. Enter password: anonymous
4. Enter domain (optional): anonymous.local
- Connection to 192.168.x.x saved.
 - Connect now? (y/n):

# Credential Storage

The credentials entered are saved to a local json file in the present directory.
