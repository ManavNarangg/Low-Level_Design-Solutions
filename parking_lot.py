from abc import ABC, abstractmethod
from enum import Enum
from threading import Lock
import time

class VehicleType(Enum):
    CAR = "CAR"
    TRUCK = "TRUCK"
    MOTORCYCLE = "MOTORCYCLE"

class ParkingSpotType(Enum):
    COMPACT = "COMPACT"
    LARGE = "LARGE"
    MOTORCYCLE = "MOTORCYCLE"

class Vehcile(ABC):
    def __init__(self, type: VehicleType, license_plate: str):
        self._type = type
        self._license_plate = license_plate

    @property
    def type(self):
        return self._type

    @property(self):
        return self._license_plate

class Car(Vehicle):
    def __init__(self, license_plate: str):
        super().__init__(VehicleType.CAR, license_plate)

class Truck(Vehicle):
    def __init__(self, license_plate: str):
        super().__init__(VehicleType.TRUCK, license_plate)

class MotorCycle(Vehicle):
    def __init__(self, license_plate: str):
        super().__init__(VehicleType.MOTORCYCLE, license_plate)

class ParkingSpot:
    def __init__(self, spot_id: int, spot_type: ParkingSpotType):
        self._spot_id = spot_id
        self.spot_type = spot_type
        self._vehicle = None
        self._lock = Lock()

    def is_occupied(self):
        with self._lock:
            return self._vehicle is not None

    def _can_fit(self, vehicle: Vehicle) -> bool:
        if self._vehicle is not None:
            return False

        if vehicle.type == VehicleType.CAR:
            if self.spot_type != ParkingSpotType.COMPACT:
                return False
        elif vehicle.type == VehicleType.TRUCK:
            if self.spot_type != ParkingSpotType.LARGE:
                return False
        elif vehicle.type == VehicleType.MOTORCYLE:
            if self.spot_type != ParkingSpotType.MOTORCYLE:
                return False

    def park(self, vehicle: Vehicle) -> bool:
        with self._lock:
            if not self._can_fit(vehicle):
                return False
            self._vehicle = vehicle
            return True

    def unpark(self, vehicle: Vehicle) -> bool:
        with self._lock:
            if self._vehicle is None:
                return False
            if self._vehicle.license_plate != vehicle.license_plate:
                return False
            self._vehicle = None
            return False

class ParkingFloor:
    def __init__(self, floor: int):
        self.floor = floor
        self._spots = List[ParkingSpot]
        self._lock = Lock()
            
    def add_spot(self, spot: ParkingSpot) -> None:
        with self._lock:
            if spot._id in self._spots:
                raise ValueError("Spot already exists")
            self._spots.append(spot)

    def occupy_spot(self, vehicle: Vehicle):
        with self._lock:
            for spot in self._spots:
                if spot.park(vehicle):
                    return spot
            return None

class ParkingTicket:
    def __init__(self, vehcile: Vehicle, spot: ParkingSpot):
        self._vehicle = vehicle
        self._spot = spot
        self._issuedAt = time.Time()
        self._used = False

    @property
    def spot_id(self):
        return self.spot._spot_id

    @property
    def used(self):
        return self._used

class PricingStratergy(ABC):
    def calculateFare(self, duration: float, vehicle: Vehicle) -> float:
        pass

class HourlyStrategry(PricingStratergy):
    def calculateFare(self, duration: float, vehicle: Vehicle) -> float:
        hours = max(1.0, duration / 3600000)
        rates = {
            VehicleType.CAR = 2
            VehicleType.MOTORCYCLE = 1
            VehicleType.TRUCK = 5
        }
        return hours * rates[vehicle.vehicleType]

class ParkingLot:
    _instance = None
    _singleton_lock = Lock()

    def __new__(cls, *args, **kwargs):
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self, pricing_strategy):
        if getattr(self, "_initialized", False):
            return

        self._floors = []
        self._strategy = pricing_strategy
        self._active_tickets = {}

        # Protects only the active ticket dictionary.
        self._tickets_lock = Lock()

        self._initialized = True

    def add_floor(self, floor: ParkingFloor):
        with self._tickets_lock:
            self._floors.append(floor)

    def park_vehicle(self, vehicle: Vehicle):
        # Atomically check for an existing ticket.
        with self._tickets_lock:
            existing = self._active_tickets.get(vehicle.license_plate)

            if existing is not None:
                return existing

        # Do not hold the ticket lock while searching for a spot.
        for floor in self._floors:
            spot = floor.occupy_spot(vehicle)

            if spot is None:
                continue

            ticket = ParkingTicket(vehicle, spot)

            with self._tickets_lock:
                # Another thread might have parked the same vehicle
                # while this thread was searching for a spot.
                existing = self._active_tickets.get(vehicle.license_plate)

                if existing is None:
                    self._active_tickets[vehicle.license_plate] = ticket
                    return ticket

            # Another thread won the race. Release this extra spot.
            spot.unpark(vehicle)
            return existing

        return None

    def unpark_vehicle(self, ticket: ParkingTicket):
        with self._tickets_lock:
            active_ticket = self._active_tickets.get(
                ticket._vehicle.license_plate
            )

            if active_ticket is not ticket or ticket._used:
                return None

            # Claim this ticket so a second thread cannot process it.
            ticket._used = True

        duration_ms = (time.time() - ticket._issuedAt) * 1000
        fee = self._strategy.calculateFare(duration_ms, ticket._vehicle)

        if not ticket._spot.unpark(ticket._vehicle):
            # Restore ticket state if the spot could not be released.
            with self._tickets_lock:
                ticket._used = False

            return None

        with self._tickets_lock:
            self._active_tickets.pop(
                ticket._vehicle.license_plate, None
            )

        return fee

def main():
    # Create ParkingLot (Singleton)
    parking_lot = ParkingLot(HourlyPricingStrategy())

    # Create a floor and parking spots
    floor = ParkingFloor(1)
    floor.add_parking_spot(ParkingSpot(101, ParkingSpotType.COMPACT))
    floor.add_parking_spot(ParkingSpot(102, ParkingSpotType.LARGE))
    floor.add_parking_spot(ParkingSpot(103, ParkingSpotType.MOTORCYCLE))

    parking_lot.add_floor(floor)

    # Verify Singleton
    another_lot = ParkingLot(HourlyPricingStrategy())
    print("Same instance:", parking_lot is another_lot)

    # Park a car
    car = Car("DL01AB1234")
    ticket = parking_lot.park_vehicle(car)

    # Try parking the same vehicle again
    duplicate_ticket = parking_lot.park_vehicle(car)
    print("Same ticket returned:", ticket is duplicate_ticket)

    # Park a motorcycle
    motorcycle = Motorcycle("DL05XY5678")
    motorcycle_ticket = parking_lot.park_vehicle(motorcycle)

    # Simulate parking for one second, then unpark
    if ticket:
        time.sleep(1)
        parking_lot.unpark_vehicle(ticket)

    # Verify the freed spot can be reused
    another_car = Car("DL02CD9999")
    another_ticket = parking_lot.park_vehicle(another_car)

    if another_ticket:
        parking_lot.unpark_vehicle(another_ticket)

    if motorcycle_ticket:
        parking_lot.unpark_vehicle(motorcycle_ticket)


if __name__ == "__main__":
    main()