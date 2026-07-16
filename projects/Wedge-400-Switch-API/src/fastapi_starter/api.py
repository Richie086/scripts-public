import os
from fastapi import APIRouter, HTTPException, Depends, Response, Request
from typing import List, Dict, Any
from .models import (
    SensorsResponse, SensorReading, PresenceResponse, FirmwareInfo, 
    SystemResetResponse, PortStatus, PortStateUpdate, VLANConfig, LLDPNeighbor,
    LoginRequest, ADConfigModel
)
from . import database as db
from .auth import authenticate_ad, create_token, get_current_user, require_role, COOKIE_NAME

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
def post_switch_reset(current_user: dict = Depends(require_role(["admin"]))):
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
def update_port(port_id: str, update: PortStateUpdate, current_user: dict = Depends(require_role(["admin", "operator"]))):
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
def create_vlan(config: VLANConfig, current_user: dict = Depends(require_role(["admin", "operator"]))):
    vlans = db.get_vlans()
    if any(v["vlan_id"] == config.vlan_id for v in vlans):
        raise HTTPException(status_code=400, detail=f"VLAN {config.vlan_id} already exists")
    
    ports_set = {p["port_id"] for p in db.get_ports()}
    for p in config.ports:
        if p not in ports_set:
            raise HTTPException(status_code=400, detail=f"Port '{p}' does not exist")
            
    return db.create_vlan(config.vlan_id, config.name, config.ports)

@router.post("/vlans/{vlan_id}/ports", response_model=VLANConfig)
def add_ports_to_vlan(vlan_id: int, ports: List[str], current_user: dict = Depends(require_role(["admin", "operator"]))):
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
def add_dynamic_route(route: Dict[str, Any], current_user: dict = Depends(require_role(["admin"]))):
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

# --- Authentication & AD Settings Router ---

auth_router = APIRouter(prefix="/api/auth")

@auth_router.post("/login")
def login(login_req: LoginRequest, response: Response):
    user_info = authenticate_ad(login_req.username, login_req.password)
    if not user_info:
        raise HTTPException(status_code=401, detail="Authentication failed: Invalid credentials")
    
    config = db.get_ad_config()
    secret = config.get("jwt_secret", "default_jwt_secret_key_change_me_in_production")
    token = create_token(user_info["username"], user_info["role"], secret)
    
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=28800
    )
    return {"status": "success", "username": user_info["username"], "role": user_info["role"]}

@auth_router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key=COOKIE_NAME)
    return {"status": "success", "message": "Successfully logged out"}

@auth_router.get("/session")
def get_session(current_user: dict = Depends(get_current_user)):
    return current_user

@auth_router.get("/config", response_model=ADConfigModel)
def get_config(current_user: dict = Depends(require_role(["admin"]))):
    config = db.get_ad_config()
    if config.get("ad_bind_password"):
        config["ad_bind_password"] = "********"
    return ADConfigModel(**config)

@auth_router.post("/config")
def post_config(new_config: ADConfigModel, current_user: dict = Depends(require_role(["admin"]))):
    current_config = db.get_ad_config()
    config_dict = new_config.model_dump()
    if config_dict["ad_bind_password"] == "********":
        config_dict["ad_bind_password"] = current_config.get("ad_bind_password", "")
    db.update_ad_config(config_dict)
    return {"status": "success", "message": "AD configuration updated."}

@auth_router.post("/test_connection")
def test_connection(config: ADConfigModel, current_user: dict = Depends(require_role(["admin"]))):
    import ldap3
    is_simulate = config.ad_simulate.lower() == "true"
    if is_simulate:
        return {"status": "success", "message": "Simulation Mode: Connection check bypassed."}
        
    try:
        server = ldap3.Server(config.ad_server, get_info=ldap3.ALL, connect_timeout=5)
        user = config.ad_bind_dn if config.ad_bind_dn else None
        password = config.ad_bind_password if config.ad_bind_dn else None
        if user and password == "********":
            current_config = db.get_ad_config()
            password = current_config.get("ad_bind_password", "")
            
        conn = ldap3.Connection(server, user=user, password=password, authentication=ldap3.SIMPLE)
        if conn.bind():
            conn.unbind()
            return {"status": "success", "message": "LDAP Connection test successful!"}
        else:
            return {"status": "error", "message": "LDAP Bind failed. Verify credentials."}
    except Exception as e:
        return {"status": "error", "message": f"LDAP Connection failed: {e}"}
