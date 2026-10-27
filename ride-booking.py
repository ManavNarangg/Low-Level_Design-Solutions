import uuid
from abc import ABC, abstractmethod
from datetime import date, timedelta
from enum import Enum
from threading import RLock, Thread

class RideStatus(ENUM):
    REQUESTED = "REQUESTED"
    ACCEPTED = "ACCEPTED"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class DriverStatus(ENUM):
    AVAILABLE = "AVAILABLE"
    ONGOING = "ONGOING"
    RESERVED = "RESERVED"
    OFFLINE = "OFFLINE"

class Location:
    def __init__(self, latitude, longitute):
        self.latitute = latitude
        self.longitude = longitude

    def distance_to(self, other):
        lat1 = radians(self.latitude)
        lon1 = radians(self.longitude)
        lat2 = radians(other.latitude)
        lon2 = radians(other.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            sin(dlat / 2) ** 2
            + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        )

        a = max(0.0, min(1.0, a))
        return 6371 * 2 * asin(sqrt(a))

class Driver:
    def __init__(self, name, location: Location):
        self.id = uuid.uuid4()
        self.name = name
        self.status = DriverStatus.AVAILABLE
        self.location = location

class RideObserver(ABC):
    @abstractmethod
    def update(self, ride: Ride, event):
        pass

class Rider(RideObserver):
    def __init__(self, name: str):
        self.id = uuid.uuid4()
        self.name = name
        self.notifications = []
        self.lock = RLock()

    def update(self, ride, event):
        message = f"Ride accepted {ride.id}"
        with self.lock:
            self.notifications.append(message)
        
class DriverMatchingStratergy(ABC):
    @abstractmethod
    def find_driver(self, pickup: Location, drivers: List[Driver]):
        pass

class NearestDriver(DriverMatchingStratergy):
    def __init__(self, max_distance_km = 10):
        self.max_distance_km = max_distance_km

    def find_driver(self, pickup: Location, drivers: List[Driver]):
        candidates = []

        for driver in drivers:
            if driver.status != DriverStatus.AVAILABLE:
                continue
            distance = pickup.distance_to(driver.location)
            if distance <= self.max_distance_km:
                candidates.append((distance, driver))
            
        if not candidates:
            return None
        
        return min(candidates, key=lambda item: item[0])[1]

class FareStratergy(ABC):
    @abstractmethod
    def calculate_dare(self, distance_km: float):
        pass

class DistanceFare(FareStratergy):
    def __init__(self, base_fare: float = 50, fare_per_km: float = 10.0):
        self.fare_per_km = fare_per_km
        self.base_fare = base_fare

    def calculate_fare(self, distance_km: float) -> Float:
        fare = self.base_fare + (self.fare_per_km * distance_km)

class Ride:
    def __init__(self, driver: Driver, rider: Rider, pickup: Location, destination: Location):
        self.id = uuid.uuid4()
        self.driver = driver
        self.rider = rider
        self.pickup = pickup
        self.location = location
        self.distance_km = pickup.distance_to(location)
        self.fare = None
        self.status = RideStatus.REQUESTED
        self._observers = []
        self._lock = RLock()
        self.subscribe(rider)

    def subscribe(self, observer):
        with self._lock:
            if observer not in self._observers:
                self._observers.append(observer)

    def unsubscribe(self, observer):
        with self._lock:
            if observer in self._observers:
                self._observers.remove(observer)

    def notify_observers(self, event):
        with self._lock:
            observers = list(self._observers)
        for observer in observers:
            observer.update(self, event)
    
    def _complete(self, fare):
        with self._lock:
            if self.status != RideStatus.ONGOING:
                raise valueError("Error")
            self.fare = fare
            self.status = RideStatus.COMPLETED
            return f"Ride {self.id} completed"

class RideService:
    def __init__(self, matching_stratergy: RideMatchingStratergy, fare_stratergy: FareStratergy):
        self.rides: Dict[int, Ride] = {}
        self.drivers: Dict[int, Driver] = {}
        self.matching_stratergy = matching_stratergy
        self.fare_stratergy = fare_stratergy
        self._lock = RLock()

    def add_driver(self, driver: Driver) -> Driver:
        with self._lock:
            if driver.id in self.drivers:
                raise ValueError("Driver already exists")
            self.drivers[driver.id] = driver

    def _get_ride(self, ride_id):
        ride = self.rides.get(ride_id)
        if ride is not None:
            return ride
    
    def _get_driver(self, driver_id):
        driver = self.drivers.get(driver_id)
        if driver is not None:
            return driver

    def request_ride(self, rider: Rider, pickup: Location, Destination: Location):
        with self._lock:
            driver = self.matching_stratergy.find_drivers(pickup: Location, list(self.drivers.values()))
            if driver is None:
                raise ValueError("No driver found, try again later")
            driver.status = DriverStatus.RESERVED
            ride = Ride(driver, rider, pickup, destination)
            self.rides[ride.id] = ride
        ride.notify_observers("Ride, requested, driver reserved")
        return ride
    
    def accept_ride(self, driver: Driver, ride: Ride):
        with self._lock:
            if ride.status != RideStatus.REQUESTED:
                raise ValueError("Error occured")
            ride.status = RideStatus.ACCEPTED
            driver.status = DriverStatus.ONGOING
        ride.notify_observer("Ride accepted by diver, aa rha bas")

    def start_ride(self, ride: Ride):
        with self._lock:
            if ride.status != RideStatus.ACCEPTED:
                raise ValueError("Error")
            ride.status == RideStatus.ONGOING
        ride.notify_observer("Ride started")

    def complete_ride(self, driver: Driver, ride: Ride):
        with self._lock:
            if ride.status != RideStatus.ONGOING:
                raise ValueError("Error")
            ride.status = RideStatus.COMPLETED
            driver.status = DriverStatus.AVAILABLE
            fare = self.fare_stratergy(ride.distance_per_km)
        ride.notify_observer("Ride completed")
        return fare

    def cancel_ride(self, rider: Rider, ride: Ride):
        with self._lock:
            ride.status = RideStatus.CANCELLED
            driver.status = DriverStatus.AVAILABLE
        ride.notify_observer("Ride cancelled by rider")

def main():
    service = RideService(
        NearestDriverStrategy(max_distance_km=10),
        DistanceFareStrategy(base_fare=50, per_km_rate=12)
    )

    rider = Rider("Alice")

    driver1 = Driver("Bob", Location(28.6139, 77.2090))
    driver2 = Driver("Charlie", Location(28.5355, 77.3910))

    service.add_driver(driver1)
    service.add_driver(driver2)

    pickup = Location(28.6129, 77.2295)
    destination = Location(28.6304, 77.2177)

    ride = service.request_ride(rider, pickup, destination)

    print("\nAssigned driver:", ride.driver.name)
    print("Status:", ride.status.value)

    service.accept_ride(ride.ride_id, ride.driver.driver_id)
    service.start_ride(ride.ride_id, ride.driver.driver_id)

    fare = service.complete_ride(
        ride.ride_id, ride.driver.driver_id
    )

    print("\nFinal status:", ride.status.value)
    print("Distance:", round(ride.distance_km, 2), "km")
    print("Fare: Rs.", fare)
    print("Driver status:", ride.driver.status.value)


if __name__ == "__main__":
    main()


    





