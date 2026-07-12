import logging

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class OperationalHours(BaseModel):
    is_24h: bool
    open: str  # Format "HH:MM"
    close: str # Format "HH:MM"

    def is_open(self, current_time: str) -> bool:
        """
        Check if the facility is open at the given time (format "HH:MM")
        """
        if self.is_24h:
            return True
        try:
            curr_h, curr_m = map(int, current_time.split(":"))
            open_h, open_m = map(int, self.open.split(":"))
            close_h, close_m = map(int, self.close.split(":"))
            
            curr_val = curr_h * 60 + curr_m
            open_val = open_h * 60 + open_m
            close_val = close_h * 60 + close_m
            
            if close_val < open_val:  # Spans overnight
                return curr_val >= open_val or curr_val <= close_val
            return open_val <= curr_val <= close_val
        except ValueError as e:
            logger.warning(
                "Format waktu tidak valid di is_open('%s'): %s",
                current_time, e
            )
            return False

class BaseNode(BaseModel):
    id: str
    name: str
    type: str
    lat: float
    lon: float
    stock: Dict[str, int]  # e.g. {"A": 5, "B": 10}
    operational_hours: OperationalHours
    
    def has_stock(self, blood_type: str, qty: int) -> bool:
        return self.stock.get(blood_type, 0) >= qty

class BDRS(BaseNode):
    type: str = "BDRS"

class UTD_PMI(BaseNode):
    type: str = "UTD_PMI"

class DonorSukarela(BaseNode):
    type: str = "DonorSukarela"
