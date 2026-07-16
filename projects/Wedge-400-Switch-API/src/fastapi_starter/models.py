from pydantic import BaseModel, Field
from typing import List, Dict, Optional

# --- OpenBMC Models ---

class SensorReading(BaseModel):
    name: str = Field(..., description="Name of the sensor")
    value: float = Field(..., description="Current value of the sensor")
    unit: str = Field(..., description="Unit of measurement (e.g. C, RPM, V, W)")
    status: str = Field("OK", description="Sensor threshold status: OK, Warning, Critical")

class SensorsResponse(BaseModel):
    scm: List[SensorReading] = Field(default_factory=list)
    smb: List[SensorReading] = Field(default_factory=list)
    pem1: List[SensorReading] = Field(default_factory=list)
    pem2: List[SensorReading] = Field(default_factory=list)
    psu1: List[SensorReading] = Field(default_factory=list)
    psu2: List[SensorReading] = Field(default_factory=list)
    fans: List[SensorReading] = Field(default_factory=list)

class PresenceResponse(BaseModel):
    device: str = Field(..., description="Type of device (e.g. scm, psu, pem, fan)")
    present: bool = Field(..., description="Whether the device is physically present")

class FirmwareInfo(BaseModel):
    cpld: str = Field("v2.4", description="CPLD version")
    fpga: str = Field("v1.12", description="FPGA version")
    scm: str = Field("v1.5", description="SCM version")

class SystemResetResponse(BaseModel):
    status: str = Field("success", description="Status of the reset command")
    message: str = Field(..., description="Information message about the reset")

# --- Switch Management Models ---

class PortStateUpdate(BaseModel):
    admin_state: Optional[str] = Field(None, description="Admin state: 'up' or 'down'")
    speed_gbps: Optional[int] = Field(None, description="Port speed in Gbps: 100, 200, 400")
    mtu: Optional[int] = Field(None, ge=64, le=9216, description="Maximum Transmission Unit")

class PortStatus(BaseModel):
    port_id: str
    name: str
    admin_state: str
    oper_state: str
    speed_gbps: int
    mtu: int
    transceiver_present: bool
    rx_power_dbm: float
    tx_power_dbm: float
    errors_in: int
    errors_out: int

class VLANConfig(BaseModel):
    vlan_id: int = Field(..., ge=1, le=4094, description="VLAN ID")
    name: str = Field(..., description="Name of the VLAN")
    ports: List[str] = Field(default_factory=list, description="Associated ports")

class LLDPNeighbor(BaseModel):
    local_port: str
    neighbor_id: str
    neighbor_port: str
    neighbor_system_name: str

# --- Dynamic API Models ---

class DynamicEndpoint(BaseModel):
    path: str
    method: str
    simulated_payload: Dict

# --- Authentication and AD Settings Models ---

class LoginRequest(BaseModel):
    username: str
    password: str

class ADConfigModel(BaseModel):
    ad_server: str
    ad_domain: str
    ad_base_dn: str
    ad_bind_dn: str
    ad_bind_password: str
    ad_group_admin: str
    ad_group_operator: str
    ad_group_viewer: str
    ad_simulate: str
    jwt_secret: Optional[str] = None

