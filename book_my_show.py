from enum import Enum
from threading import Lock
from dataclasses import dataclass
from uuid import uuid4
from abc import ABC, abstractmethod

class SeatType(Enum):
    REGULAR = "REGULAR"
    PREMIUM = "PREMIUM"
    RECLINER = "RECLINER"

class SeatStatus(Enum):
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    BOOKED = "BOOKED"

class BookingStatus(Enum):
    PEDNING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"

class City:
    def __init__(self, name):
        self.name = name

class Seat:
    def __init__(self, type: SeatType):
        self.id = uuid.uuid4()
        self.type = type

class Screen:
    def __init__(self, id: int, seats: List[Seat]):
        self.id = id
        self.seats = {seat.id for seat in seats}

class Cinema:
    def __init__(self, name: str, city: City):
        self.id == uuid.uuid4()
        self.name = name
        self.city = city

class Movie:
    def __init__(self, title: str):
        self.id = uuid.uuid4()
        self.title = title

@dataclass
class ShowSeat:
    seat: Seat
    status: SeatStatus = SeatStatus.AVAILABLE

class Show:
    def __init__(self, movie: Movie, screen: Screen, start_time: time):
        self.id = uuid.uuid4()
        self.screen = screen
        self.movie = movie
        self.start_time = start_time
        self.show_seats = {
            id: ShowSeat(seat)
            for id, seat in screen.seats.items()
        }
        self.lock = Lock()

class User:
    def __init__(self, name: str):
        self.id == uuid.uuid4()
        self.name = name

@dataclass
class Booking:
    id: uuid.uuid4()
    user: User
    show: Show
    status: BookingStatus = BookingStatus.PENDING
    amount: float
    seats: List[Seat]

class PricingStratergy(ABC):
    @abstractmethod
    def calculate_price(self, seat, show):
        pass

class SeatTypePricing(PricingStratergy):
    def __init__(self, prices):
        self.prices = prices

    def calculate_price(self, seat, show):
        return self.prices[seat.seat_type]

class PaymentStratergy(ABC):
    @abstractmethod
    def pay(self, amount):
        pass

class UpiPayment(PaymentStrategy):
    def pay(self, amount):
        print(f"Processing UPI payment: ₹{amount}")
        return True


class CardPayment(PaymentStrategy):
    def pay(self, amount):
        print(f"Processing card payment: ₹{amount}")
        return True

class BookingService:
    def __init__(self, pricing_stratergy: PricingStratergy):
        self.pricing_stratergy = pricing_stratergy
        self.bookings: Dict[int, Booking] = {}
        self.cinemas: Dict[int, Cinema] = {}
        self.Shows: Dict[int, Show] = {}

    def search_shows(self, shows, movie_title, city_name):
        return [
            show for show in shows
            if show.movie.title.lower() == movie_title.lower()
            and show.city.lower() == city_name.lower()
        ]

    def book_seat(self, seat_ids: List[int], show: Show, user: User, payment_stratergy: PaymentStratergy) -> Booking:
        if not seat_ids:
            raise ValueError("Select at least one seat")
        
        with show.lock:
            selected = []

            for seat_id in seat_ids:
                show_seat = show.show_seats.get(id)

                if show_seat is None:
                    raise ValueError(f"Invalid seat: {seat_id}")

                if show_seat.status != SeatStatus.AVAILABLE:
                    raise ValueError(f"Seat {seat_id} is unavailable")
                
                selected.append(show_seat)
            
            for show_seat in selected:
                show_seat.status = SeatStatus.RESERVED 
        
        booking = None

        try:
            amount = sum(
                self.pricing_stratergy.calculate_price(item.seat, show)
                for item in selected    
            )
            booking = Booking(user, show, amount, seats = [item.seat for item in selected])
            self.bookings[booking.id] = booking

            if not payment_strategy.pay(amount):
                booking.status = BookingStatus.FAILED
                raise ValueError("Payment failed")

            with show.lock:
                for item in selected:
                    item.status = SeatStaus.BOOKED
            booking.status = BookingStatus.CONFIRMED
            return booking
        except Exception:
            with show.lock:
                for item in selected:
                    if item.status = SeatStatus.RESERVED:
                        item.status = SeatStatus.AVAILABLE
            if booking is not None:
                booking.status = BookingStatus.FAILED
            raise
            
def main():
    city = City("Delhi")
    cinema = Cinema("PVR", city)

    seats = [
        Seat("A1", SeatType.REGULAR),
        Seat("A2", SeatType.PREMIUM),
        Seat("A3", SeatType.RECLINER),
    ]

    screen = Screen(1, seats)
    movie = Movie("Interstellar")

    show = Show(movie, screen, "18:00")

    user1 = User("Rahul")
    user2 = User("Amit")

    pricing = SeatTypePricing({
        SeatType.REGULAR: 200,
        SeatType.PREMIUM: 350,
        SeatType.RECLINER: 500,
    })

    service = BookingService(pricing)

    def book(user):
        try:
            booking = service.book_seat(
                seat_ids=[seats[0].id],
                show=show,
                user=user,
                payment_stratergy=UpiPayment(),
            )

            print(
                f"{user.name}: Booking successful! "
                f"Amount = {booking.amount}"
            )

        except ValueError as e:
            print(f"{user.name}: Booking failed - {e}")

    t1 = Thread(target=book, args=(user1,))
    t2 = Thread(target=book, args=(user2,))

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    print("Final seat status:", show.show_seats[seats[0].id].status)


if __name__ == "__main__":
    main()