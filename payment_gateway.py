
from abc import ABC, abstractmethod
from enum import Enum
from threading import Lock
from uuid import uuid4


# ---------- Enums ----------

class PaymentMethod(Enum):
    UPI = "UPI"
    CARD = "CARD"
    PAYPAL = "PAYPAL"


class PaymentStatus(Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


# ---------- Payment ----------

class Payment:
    def __init__(self, amount: float, method: PaymentMethod):
        if amount <= 0:
            raise ValueError("Amount must be positive")

        if not isinstance(method, PaymentMethod):
            raise ValueError("Invalid payment method")

        self._id = uuid4()
        self.amount = amount
        self.method = method
        self.status = PaymentStatus.PENDING
        self.attempts = 0

        self._processing = False
        self._lock = Lock()

    @property
    def payment_id(self):
        return str(self._id)

    def start_processing(self):
        with self._lock:
            if self._processing:
                return False

            if self.status in (
                PaymentStatus.SUCCESS,
                PaymentStatus.FAILED
            ):
                return False

            self._processing = True
            self.status = PaymentStatus.PROCESSING
            return True

    def record_attempt(self):
        with self._lock:
            self.attempts += 1
            return self.attempts

    def finish(self, status):
        with self._lock:
            self.status = status
            self._processing = False

    def get_status(self):
        with self._lock:
            return self.status

    def get_attempts(self):
        with self._lock:
            return self.attempts


# ---------- Observer Pattern ----------

class PaymentObserver(ABC):
    @abstractmethod
    def on_payment_update(self, payment, status):
        pass


class CustomerNotifier(PaymentObserver):
    def on_payment_update(self, payment, status):
        print(
            f"[Customer] Payment {payment.payment_id}: "
            f"{status.value}"
        )


class MerchantNotifier(PaymentObserver):
    def on_payment_update(self, payment, status):
        print(
            f"[Merchant] Payment {payment.payment_id}: "
            f"{status.value}"
        )


# ---------- Strategy Pattern ----------

class PaymentProcessor(ABC):
    @abstractmethod
    def process(self, payment):
        """Perform one payment attempt."""
        pass


class CardProcessor(PaymentProcessor):
    def process(self, payment):
        print("Processing credit card payment")
        return True


class PayPalProcessor(PaymentProcessor):
    def process(self, payment):
        print("Processing PayPal payment")
        return True


class UPIProcessor(PaymentProcessor):
    def process(self, payment):
        print("Processing UPI payment")
        # Integrate the UPI provider here.
        return True


class PaymentGateway:
    def __init__(self, max_attempts=3):
        if max_attempts < 1:
            raise ValueError("max_attempts must be positive")

        self._max_attempts = max_attempts

        self._observers = []
        self._observer_lock = Lock()

        self._processors = {
            PaymentMethod.CARD: CardProcessor(),
            PaymentMethod.PAYPAL: PayPalProcessor(),
            PaymentMethod.UPI: UPIProcessor()
        }

        self.subscribe(CustomerNotifier())
        self.subscribe(MerchantNotifier())

    def subscribe(self, observer):
        with self._observer_lock:
            if observer not in self._observers:
                self._observers.append(observer)

    def unsubscribe(self, observer):
        with self._observer_lock:
            if observer in self._observers:
                self._observers.remove(observer)

    def notify_observers(self, payment, status):
        with self._observer_lock:
            observers = list(self._observers)

        for observer in observers:
            try:
                observer.on_payment_update(payment, status)
            except Exception as exc:
                print(f"Notification failed: {exc}")

    def process_payment(
        self, amount: float, method: PaymentMethod
    ):
        payment = Payment(amount, method)

        processor = self._processors.get(payment.method)

        if processor is None:
            raise ValueError("Unsupported payment method")

        if not payment.start_processing():
            return payment

        self.notify_observers(
            payment, PaymentStatus.PROCESSING
        )

        try:
            for _ in range(self._max_attempts):
                attempt = payment.record_attempt()

                print(
                    f"Attempt {attempt}/{self._max_attempts}"
                )

                try:
                    success = processor.process(payment)
                except Exception as exc:
                    print(f"Processor error: {exc}")
                    success = False

                if success:
                    payment.finish(PaymentStatus.SUCCESS)
                    self.notify_observers(
                        payment, PaymentStatus.SUCCESS
                    )
                    return payment

            payment.finish(PaymentStatus.FAILED)
            self.notify_observers(
                payment, PaymentStatus.FAILED
            )
            return payment

        except Exception:
            payment.finish(PaymentStatus.FAILED)
            self.notify_observers(
                payment, PaymentStatus.FAILED
            )
            raise


# ---------- Main ----------

if __name__ == "__main__":
    gateway = PaymentGateway(max_attempts=3)

    payment = gateway.process_payment(
        1500,
        PaymentMethod.CARD
    )

    print("\nPayment ID:", payment.payment_id)
    print("Final status:", payment.get_status().value)
    print("Total attempts:", payment.get_attempts())
