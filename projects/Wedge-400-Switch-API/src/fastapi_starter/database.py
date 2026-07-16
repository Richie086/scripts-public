import os
import json
import sqlite3
from typing import List, Dict, Any, Optional

DATABASE_PATH = os.getenv("DATABASE_PATH", "switch_config.db")

def get_db_connection():
    # If using in-memory SQLite, we must share the connection because standard :memory: drops on connection close
    # sqlite3.connect(":memory:") drops when closed. But for testing, if we use a shared database we can pass uri=True
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(force_recreate: bool = False):
    conn = get_db_connection()
    cursor = conn.cursor()

    if force_recreate:
        cursor.execute("DROP TABLE IF EXISTS ports")
        cursor.execute("DROP TABLE IF EXISTS vlans")
        cursor.execute("DROP TABLE IF EXISTS dynamic_routes")

    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ports (
            port_id TEXT PRIMARY KEY,
            name TEXT,
            admin_state TEXT,
            oper_state TEXT,
            speed_gbps INTEGER,
            mtu INTEGER,
            transceiver_present INTEGER,
            rx_power_dbm REAL,
            tx_power_dbm REAL,
            errors_in INTEGER,
            errors_out INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vlans (
            vlan_id INTEGER PRIMARY KEY,
            name TEXT,
            ports TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dynamic_routes (
            path TEXT PRIMARY KEY,
            payload TEXT
        )
    """)
    conn.commit()

    # Seed ports if empty
    cursor.execute("SELECT COUNT(*) FROM ports")
    if cursor.fetchone()[0] == 0:
        port_count = int(os.getenv("SWITCH_PORT_COUNT", "16"))
        port_speed = int(os.getenv("SWITCH_PORT_SPEED", "400"))
        
        for i in range(1, port_count + 1):
            port_id = f"Eth1/{i}"
            name = f"ethernet1/{i}"
            admin_state = "up"
            transceiver_present = 1 if i % 6 != 0 else 0
            oper_state = "up" if (i % 4 != 0 and transceiver_present == 1) else "down"
            speed_gbps = port_speed
            mtu = 1500
            rx_power_dbm = -3.2 if transceiver_present == 1 else -99.0
            tx_power_dbm = 1.1 if transceiver_present == 1 else -99.0
            errors_in = 0
            errors_out = 0

            cursor.execute("""
                INSERT INTO ports (
                    port_id, name, admin_state, oper_state, speed_gbps, mtu, 
                    transceiver_present, rx_power_dbm, tx_power_dbm, errors_in, errors_out
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                port_id, name, admin_state, oper_state, speed_gbps, mtu,
                transceiver_present, rx_power_dbm, tx_power_dbm, errors_in, errors_out
            ))
        conn.commit()

    # Seed VLANs if empty
    cursor.execute("SELECT COUNT(*) FROM vlans")
    if cursor.fetchone()[0] == 0:
        # Get all ported IDs
        cursor.execute("SELECT port_id FROM ports")
        all_ports = [row["port_id"] for row in cursor.fetchall()]
        ports_str = ",".join(all_ports)

        cursor.execute("INSERT INTO vlans (vlan_id, name, ports) VALUES (?, ?, ?)", (1, "default", ports_str))
        cursor.execute("INSERT INTO vlans (vlan_id, name, ports) VALUES (?, ?, ?)", (10, "management", ""))
        conn.commit()

    conn.close()

# --- Ports DB Helper Operations ---

def get_ports() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ports")
    rows = cursor.fetchall()
    conn.close()
    
    ports = []
    for r in rows:
        p = dict(r)
        p["transceiver_present"] = bool(p["transceiver_present"])
        ports.append(p)
    return ports

def get_port(port_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ports WHERE port_id = ?", (port_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        p = dict(row)
        p["transceiver_present"] = bool(p["transceiver_present"])
        return p
    return None

def update_port(port_id: str, admin_state: Optional[str] = None, speed_gbps: Optional[int] = None, mtu: Optional[int] = None) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get current state
    cursor.execute("SELECT * FROM ports WHERE port_id = ?", (port_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
        
    current = dict(row)
    
    new_admin = admin_state if admin_state is not None else current["admin_state"]
    new_speed = speed_gbps if speed_gbps is not None else current["speed_gbps"]
    new_mtu = mtu if mtu is not None else current["mtu"]
    
    # Calculate oper state based on admin_state and transceiver presence
    new_oper = "up" if (new_admin == "up" and current["transceiver_present"] == 1) else "down"
    
    cursor.execute("""
        UPDATE ports 
        SET admin_state = ?, oper_state = ?, speed_gbps = ?, mtu = ?
        WHERE port_id = ?
    """, (new_admin, new_oper, new_speed, new_mtu, port_id))
    conn.commit()
    
    # Fetch updated
    cursor.execute("SELECT * FROM ports WHERE port_id = ?", (port_id,))
    updated = cursor.fetchone()
    conn.close()
    
    if updated:
        p = dict(updated)
        p["transceiver_present"] = bool(p["transceiver_present"])
        return p
    return None

# --- VLAN DB Helper Operations ---

def get_vlans() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vlans")
    rows = cursor.fetchall()
    conn.close()
    
    vlans = []
    for r in rows:
        v = dict(r)
        # Convert comma-separated string back to array
        v["ports"] = [p for p in v["ports"].split(",") if p] if v["ports"] else []
        vlans.append(v)
    return vlans

def create_vlan(vlan_id: int, name: str, ports: List[str]) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    ports_str = ",".join(ports)
    cursor.execute("INSERT INTO vlans (vlan_id, name, ports) VALUES (?, ?, ?)", (vlan_id, name, ports_str))
    conn.commit()
    conn.close()
    
    return {"vlan_id": vlan_id, "name": name, "ports": ports}

def add_ports_to_vlan(vlan_id: int, ports: List[str]) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM vlans WHERE vlan_id = ?", (vlan_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
        
    current = dict(row)
    current_ports = [p for p in current["ports"].split(",") if p] if current["ports"] else []
    
    for p in ports:
        if p not in current_ports:
            current_ports.append(p)
            
    ports_str = ",".join(current_ports)
    cursor.execute("UPDATE vlans SET ports = ? WHERE vlan_id = ?", (ports_str, vlan_id))
    conn.commit()
    conn.close()
    
    return {"vlan_id": vlan_id, "name": current["name"], "ports": current_ports}

# --- Dynamic Routes DB Helper Operations ---

def get_dynamic_routes() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dynamic_routes")
    rows = cursor.fetchall()
    conn.close()
    
    routes = []
    for r in rows:
        try:
            payload = json.loads(r["payload"])
        except Exception:
            payload = {}
        routes.append({"path": r["path"], "payload": payload})
    return routes

def get_dynamic_route(path: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dynamic_routes WHERE path = ?", (path,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        try:
            return json.loads(row["payload"])
        except Exception:
            return {}
    return None

def add_dynamic_route(path: str, payload: Dict[str, Any]):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    payload_str = json.dumps(payload)
    cursor.execute("""
        INSERT OR REPLACE INTO dynamic_routes (path, payload) VALUES (?, ?)
    """, (path, payload_str))
    conn.commit()
    conn.close()
