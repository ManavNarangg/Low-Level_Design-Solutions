from enum import Enum
from typing import List, Optional


class Direction(Enum):
    UP = 1
    DOWN = -1
    IDLE = 0


class DoorState(Enum):
    OPEN = 1
    CLOSED = 2


class RequestType(Enum):
    INTERNAL = 1
    EXTERNAL = 2


class Request:
    def __init__(
        self,
        origin_floor: int,
        direction: Direction,
        request_type: RequestType,
        target_floor: Optional[int] = None,
        elevator_id: Optional[int] = None,
    ):
        self.origin_floor = origin_floor
        self.target_floor = target_floor
        self.direction = direction
        self.request_type = request_type
        self.elevator_id = elevator_id

class ElevatorCar:
    def __init__(self, car_id: int):
        self.id = car_id
        self.current_floor = 1
        self.direction = Direction.IDLE
        self.door_state = DoorState.CLOSED
        self.up_requests = set()
        self.down_requests = set()

    def add_request(self, floor: int) -> None:
        if floor > self.current_floor:
            self.up_requests.add(floor)
            if self.direction == Direction.IDLE:
                self.direction = Direction.UP

        elif floor < self.current_floor:
            self.down_requests.add(floor)
            if self.direction == Direction.IDLE:
                self.direction = Direction.DOWN

        else:
            self.open_doors()

    def open_doors(self) -> None:
        self.door_state = DoorState.OPEN
        print(f"Elevator {self.id}: doors OPEN at floor {self.current_floor}")

    def close_doors(self) -> None:
        self.door_state = DoorState.CLOSED

    # For moving the elevator
    def step(self) -> None:
        if self.door_state == DoorState.OPEN:
            self.close_doors()
            return

        if self.direction == Direction.UP and not self.up_requests:
            self.direction = (
                Direction.DOWN if self.down_requests else Direction.IDLE
            )

        elif self.direction == Direction.DOWN and not self.down_requests:
            self.direction = (
                Direction.UP if self.up_requests else Direction.IDLE
            )

        if self.direction == Direction.IDLE:
            if self.up_requests:
                self.direction = Direction.UP
            elif self.down_requests:
                self.direction = Direction.DOWN
            else:
                return

        if self.direction == Direction.UP:
            self.current_floor += 1
            print(f"Elevator {self.id} moving UP to {self.current_floor}")

            if self.current_floor in self.up_requests:
                self.up_requests.remove(self.current_floor)
                self.open_doors()

        elif self.direction == Direction.DOWN:
            self.current_floor -= 1
            print(f"Elevator {self.id} moving DOWN to {self.current_floor}")

            if self.current_floor in self.down_requests:
                self.down_requests.remove(self.current_floor)
                self.open_doors()


class Dispatcher:
    def select_car(
        self,
        cars: List[ElevatorCar],
        request: Request,
    ) -> ElevatorCar:
        raise NotImplementedError


class ClosestDispatcher(Dispatcher):
    def select_car(
        self,
        cars: List[ElevatorCar],
        request: Request,
    ) -> ElevatorCar:
        if not cars:
            raise RuntimeError("No elevator cars available")

        compatible = []

        for car in cars:
            if car.direction == Direction.IDLE:
                compatible.append(car)

            elif (
                car.direction == request.direction
                and request.direction == Direction.UP
                and car.current_floor <= request.origin_floor
            ):
                compatible.append(car)

            elif (
                car.direction == request.direction
                and request.direction == Direction.DOWN
                and car.current_floor >= request.origin_floor
            ):
                compatible.append(car)

        candidates = compatible if compatible else cars

        return min(
            candidates,
            key=lambda car: abs(car.current_floor - request.origin_floor),
        )


class ElevatorController:
    _instance = None
    _lock = Lock()

    def __new__(cls, dispatcher=None):
        if cls._instance is None:
            with self._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, dispatcher=None):
        if hasattr(self, "_initialized"):
            return

        self.cars: dict[int, car: ElevatorCar] = {}
        self.dispatcher = dispatcher or ClosestDispatcher()
        self._initialized = True

    def add_car(self, car: ElevatorCar) -> None:
        self.cars[car.id] = car

    def submit_request(self, request: Request) -> None:
        if request.request_type == RequestType.INTERNAL:
            car = self.cars[request.elevator_id]

            if car is None:
                raise ValueError("Elevator not found")

            if request.target_floor is None:
                raise ValueError("Target floor is required")

            car.add_request(request.target_floor)

        else:
            car = self.dispatcher.select_car(list(self.cars.values()), request)
            print(f"Elevator {car.id} assigned to floor {request.origin_floor}")
            car.add_request(request.origin_floor)

    def step(self) -> None:
        for car in self.cars.values():
            car.step()


if __name__ == "__main__":
    controller = ElevatorController()

    controller.add_car(ElevatorCar(1))
    controller.add_car(ElevatorCar(2))

    # External request
    controller.submit_request(
        Request(5, Direction.UP, RequestType.EXTERNAL)
    )

    # Internal request: elevator 1 goes to floor 8
    controller.submit_request(
        Request(
            origin_floor=1,
            target_floor=8,
            direction=Direction.UP,
            request_type=RequestType.INTERNAL,
            elevator_id=1,
        )
    )

    for _ in range(10):
        controller.step()