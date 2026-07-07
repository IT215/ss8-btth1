from datetime import date
from enum import Enum
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

app = FastAPI(title="Logistics Management API")

# ==========================
# Sample Data
# ==========================

carriers = [
    {
        "id": 1,
        "code": "GHN",
        "name": "Giao Hang Nhanh",
        "max_weight_capacity": 5000,
        "status": "ACTIVE",
    },
    {
        "id": 2,
        "code": "GHTK",
        "name": "Giao Hang Tiet Kiem",
        "max_weight_capacity": 3000,
        "status": "ACTIVE",
    },
    {
        "id": 3,
        "code": "VTP",
        "name": "Viettel Post",
        "max_weight_capacity": 10000,
        "status": "SUSPENDED",
    },
]

shipments = [
    {
        "id": 1,
        "carrier_id": 1,
        "order_reference": "ORD-2026-001",
        "total_weight": 4200,
        "dispatch_date": "2026-07-01",
        "shift": "MORNING",
    }
]


# ==========================
# Enum
# ==========================

class CarrierStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class Shift(str, Enum):
    MORNING = "MORNING"
    AFTERNOON = "AFTERNOON"
    EVENING = "EVENING"


# ==========================
# Models
# ==========================

class CarrierCreate(BaseModel):
    code: str
    name: str
    max_weight_capacity: int = Field(gt=0)
    status: CarrierStatus

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Name must be at least 3 characters")
        return value


class ShipmentCreate(BaseModel):
    carrier_id: int
    order_reference: str
    total_weight: int = Field(gt=0)
    dispatch_date: date
    shift: Shift


# ==========================
# Helper Functions
# ==========================

def get_carrier(carrier_id: int):
    for carrier in carriers:
        if carrier["id"] == carrier_id:
            return carrier
    return None


# ==========================
# Carrier APIs
# ==========================

@app.post("/carriers", status_code=201)
def create_carrier(carrier: CarrierCreate):

    for item in carriers:
        if item["code"].lower() == carrier.code.lower():
            raise HTTPException(
                status_code=400,
                detail="Carrier code already exists"
            )

    new_carrier = carrier.model_dump()
    new_carrier["id"] = max([c["id"] for c in carriers], default=0) + 1

    carriers.append(new_carrier)
    return new_carrier


@app.get("/carriers")
def get_carriers(
    keyword: Optional[str] = Query(None),
    status: Optional[CarrierStatus] = Query(None),
    min_weight: Optional[int] = Query(None),
):

    result = carriers.copy()

    if keyword:
        keyword = keyword.lower()
        result = [
            c for c in result
            if keyword in c["code"].lower()
            or keyword in c["name"].lower()
        ]

    if status:
        result = [
            c for c in result
            if c["status"] == status.value
        ]

    if min_weight is not None:
        result = [
            c for c in result
            if c["max_weight_capacity"] >= min_weight
        ]

    return result


@app.get("/carriers/{carrier_id}")
def get_carrier_by_id(carrier_id: int):
    carrier = get_carrier(carrier_id)

    if carrier is None:
        raise HTTPException(
            status_code=404,
            detail="Carrier not found"
        )

    return carrier


@app.put("/carriers/{carrier_id}")
def update_carrier(carrier_id: int, updated: CarrierCreate):

    carrier = get_carrier(carrier_id)

    if carrier is None:
        raise HTTPException(
            status_code=404,
            detail="Carrier not found"
        )

    for item in carriers:
        if (
            item["id"] != carrier_id
            and item["code"].lower() == updated.code.lower()
        ):
            raise HTTPException(
                status_code=400,
                detail="Carrier code already exists"
            )

    carrier.update(updated.model_dump())

    return carrier


@app.delete("/carriers/{carrier_id}")
def delete_carrier(carrier_id: int):

    carrier = get_carrier(carrier_id)

    if carrier is None:
        raise HTTPException(
            status_code=404,
            detail="Carrier not found"
        )

    carriers.remove(carrier)

    return {"message": "Carrier deleted successfully"}


# ==========================
# Shipment APIs
# ==========================

@app.post("/shipments", status_code=201)
def create_shipment(shipment: ShipmentCreate):

    carrier = get_carrier(shipment.carrier_id)

    if carrier is None:
        raise HTTPException(
            status_code=404,
            detail="Carrier not found"
        )

    if carrier["status"] != "ACTIVE":
        raise HTTPException(
            status_code=400,
            detail="Carrier is not active"
        )

    if shipment.total_weight > carrier["max_weight_capacity"]:
        raise HTTPException(
            status_code=400,
            detail="Shipment exceeds carrier capacity"
        )

    new_shipment = shipment.model_dump()
    new_shipment["id"] = max([s["id"] for s in shipments], default=0) + 1
    new_shipment["dispatch_date"] = str(new_shipment["dispatch_date"])

    shipments.append(new_shipment)

    return new_shipment


@app.get("/shipments")
def get_shipments():
    return shipments