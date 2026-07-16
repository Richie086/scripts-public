import os
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from .models import (
    SensorsResponse, SensorReading, PresenceResponse, FirmwareInfo, 
    SystemResetResponse, PortStatus, PortStateUpdate, VLANConfig, LLDPNeighbor
)
from . import database as db

router = APIRouter(prefix="/api/sys")

# --- OpenBMC Endpoints ---

@router.get("/sensors", response_model=SensorsResponse)
def get_sensors():
    return SensorsResponse(
        scm=[
            SensorReading(name="SCM_TEMP_C", value=38.5, unit="C"),
            SensorReading(name="SCM_VOLT_12V", value=12.02, unit="V"),
            SensorReading(name="SCM_VOLT_3V3", value=3.31, unit="V")
        ],
        smb=[
            SensorReading(name="SMB_TEMP_C", value=42.1, unit="C"),
            SensorReading(name="SMB_VOLT_12V", value=11.98, unit="V")
        ],
        pem1=[
            SensorReading(name="PEM1_TEMP_C", value=36.0, unit="C"),
            SensorReading(name="PEM1_VOLT_IN", value=230.1, unit="V"),
            SensorReading(name="PEM1_WATT_OUT", value=120.5, unit="W")
        ],
        pem2=[
            SensorReading(name="PEM2_TEMP_C", value=35.8, unit="C"),
            SensorReading(name="PEM2_VOLT_IN", value=229.8, unit="V"),
            SensorReading(name="PEM2_WATT_OUT", value=118.2, unit="W")
        ],
        psu1=[
            SensorReading(name="PSU1_TEMP_C", value=37.2, unit="C"),
            SensorReading(name="PSU1_FAN_SPEED", value=8200.0, unit="RPM")
        ],
        psu2=[
            SensorReading(name="PSU2_TEMP_C", value=36.9, unit="C"),
            SensorReading(name="PSU2_FAN_SPEED", value=8150.0, unit="RPM")
        ],
        fans=[
            SensorReading(name="FAN1_SPEED_RPM", value=8500.0, unit="RPM"),
            SensorReading(name="FAN2_SPEED_RPM", value=8450.0, unit="RPM"),
            SensorReading(name="FAN3_SPEED_RPM", value=8600.0, unit="RPM"),
            SensorReading(name="FAN4_SPEED_RPM", value=8550.0, unit="RPM")
        ]
    )

@router.get("/presence/{device}", response_model=PresenceResponse)
def get_presence(device: str):
    valid_devices = ["scm", "psu", "pem", "fan"]
    device_lower = device.lower()
    if device_lower not in valid_devices:
        raise HTTPException(status_code=400, detail=f"Invalid device type. Must be one of {valid_devices}")
    
    return PresenceResponse(device=device_lower, present=True)

@router.get("/firmware_info/all", response_model=FirmwareInfo)
def get_firmware_info():
    return FirmwareInfo()

@router.post("/switch_reset", response_model=SystemResetResponse)
def post_switch_reset():
    # Drop and recreate tables, seeding defaults
    db.init_db(force_recreate=True)
    return SystemResetResponse(
        status="success",
        message="Wedge 400 ASIC reset executed. Database configurations re-initialized to defaults."
    )

# --- Switch Management Endpoints ---

@router.get("/ports", response_model=List[PortStatus])
def get_all_ports():
    return db.get_ports()

@router.get("/ports/{port_id:path}", response_model=PortStatus)
def get_port(port_id: str):
    port = db.get_port(port_id)
    if not port:
        raise HTTPException(status_code=404, detail=f"Port '{port_id}' not found")
    return port

@router.patch("/ports/{port_id:path}", response_model=PortStatus)
def update_port(port_id: str, update: PortStateUpdate):
    if update.admin_state is not None:
        if update.admin_state not in ["up", "down"]:
            raise HTTPException(status_code=400, detail="Invalid admin state. Must be 'up' or 'down'")
        
    if update.speed_gbps is not None:
        if update.speed_gbps not in [100, 200, 400]:
            raise HTTPException(status_code=400, detail="Invalid speed. Must be 100, 200, or 400 Gbps")
        
    port = db.update_port(port_id, update.admin_state, update.speed_gbps, update.mtu)
    if not port:
        raise HTTPException(status_code=404, detail=f"Port '{port_id}' not found")
    return port

@router.get("/vlans", response_model=List[VLANConfig])
def get_vlans():
    return db.get_vlans()

@router.post("/vlans", response_model=VLANConfig)
def create_vlan(config: VLANConfig):
    vlans = db.get_vlans()
    if any(v["vlan_id"] == config.vlan_id for v in vlans):
        raise HTTPException(status_code=400, detail=f"VLAN {config.vlan_id} already exists")
    
    ports_set = {p["port_id"] for p in db.get_ports()}
    for p in config.ports:
        if p not in ports_set:
            raise HTTPException(status_code=400, detail=f"Port '{p}' does not exist")
            
    return db.create_vlan(config.vlan_id, config.name, config.ports)

@router.post("/vlans/{vlan_id}/ports", response_model=VLANConfig)
def add_ports_to_vlan(vlan_id: int, ports: List[str]):
    ports_set = {p["port_id"] for p in db.get_ports()}
    for p in ports:
        if p not in ports_set:
            raise HTTPException(status_code=400, detail=f"Port '{p}' does not exist")
        
    res = db.add_ports_to_vlan(vlan_id, ports)
    if not res:
        raise HTTPException(status_code=404, detail=f"VLAN {vlan_id} not found")
    return res

@router.get("/lldp", response_model=List[LLDPNeighbor])
def get_lldp_neighbors():
    return [
        LLDPNeighbor(
            local_port="Eth1/1",
            neighbor_id="00:1a:2b:3c:4d:5e",
            neighbor_port="Eth1/24",
            neighbor_system_name="spine-sw01"
        ),
        LLDPNeighbor(
            local_port="Eth1/2",
            neighbor_id="00:1a:2b:3c:4d:5f",
            neighbor_port="Eth1/24",
            neighbor_system_name="spine-sw02"
        )
    ]

# --- Dynamic Routes API CRUD Endpoints ---

@router.post("/routes")
def add_dynamic_route(route: Dict[str, Any]):
    path = route.get("path")
    payload = route.get("payload")
    if not path or payload is None:
        raise HTTPException(status_code=400, detail="Missing path or payload in request body")
        
    # Ensure path has the appropriate prefix
    if not path.startswith("/api/sys/"):
         raise HTTPException(status_code=400, detail="Dynamic path must start with '/api/sys/'")
         
    # Check that it doesn't overwrite static routes
    static_paths = [
        "/api/sys/sensors", "/api/sys/presence", "/api/sys/firmware_info/all", 
        "/api/sys/switch_reset", "/api/sys/ports", "/api/sys/vlans", "/api/sys/lldp", "/api/sys/routes"
    ]
    if any(path.startswith(static) for static in static_paths):
         raise HTTPException(status_code=400, detail=f"Path '{path}' collides with a statically defined route")
         
    db.add_dynamic_route(path, payload)
    return {"status": "success", "message": f"Dynamic route '{path}' registered."}

@router.get("/routes")
def get_dynamic_routes():
    return db.get_dynamic_routes()

# --- Wildcard Route for Discovered Dynamic API Endpoints ---

@router.api_route("/{rest_of_path:path}", methods=["GET", "POST", "PATCH", "DELETE"])
def dynamic_wildcard_route(rest_of_path: str):
    full_path = f"/api/sys/{rest_of_path}"
    
    payload = db.get_dynamic_route(full_path)
    if payload is not None:
        return payload
        
    raise HTTPException(status_code=404, detail=f"Endpoint '{full_path}' not found in static or dynamic routes.")
