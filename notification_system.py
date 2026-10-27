from abc import ABC, abstractmethod
from enum import Enum
from concurrent.futures import ThreadPoolExecutor # manages multipleworker threads concurrently
from time import sleep
from uuid import uuid4

class ChannelType(Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH"

class Notification:
    def __init__(self, recipient, channel, body, subject=""):
        if not recipient or not body:
            raise ValueError("Recipient and body are required")

        self.notification_id = str(uuid4())
        self.recipient = recipient
        self.channel = channel
        self.body = body
        self.subject = subject


# Strategy
class NotificationChannel(ABC):
    @abstractmethod
    def send(self, notification):
        pass


class EmailChannel(NotificationChannel):
    def send(self, notification):
        print(
            f"EMAIL to {notification.recipient}: "
            f"{notification.subject} - {notification.body}"
        )


class SMSChannel(NotificationChannel):
    def send(self, notification):
        print(f"SMS to {notification.recipient}: {notification.body}")


class PushChannel(NotificationChannel):
    def send(self, notification):
        print(f"PUSH to {notification.recipient}: {notification.body}")


# Observer
class Observer(ABC):
    @abstractmethod
    def update(self, event):
        pass


class NotificationObserver(Observer):
    def __init__(self, service):
        self.service = service

    def update(self, event):
        message = f"Order {event['order_id']} has been shipped!"

        notification = Notification(
            recipient=event["email"],
            channel=ChannelType.EMAIL,
            subject="Order Update",
            body=message
        )

        self.service.send_async(notification)


# Notification service: publisher + delivery
class NotificationService:
    def __init__(self, workers=5):
        self.executor = ThreadPoolExecutor(max_workers=workers)
        self.observers = {}
        self.closed = False

    def subscribe(self, event_type, observer):
        self.observers.setdefault(event_type, []).append(observer)

    def publish(self, event_type, event):
        for observer in self.observers.get(event_type, []):
            observer.update(event)

    # Strategy selection
    def get_channel(self, channel_type):
        if channel_type == ChannelType.EMAIL:
            return EmailChannel()
        elif channel_type == ChannelType.SMS:
            return SMSChannel()
        elif channel_type == ChannelType.PUSH:
            return PushChannel()

        raise ValueError("Unsupported channel")

    # Asynchronous submission
    def send_async(self, notification):
        if self.closed:
            raise RuntimeError("Service is closed")

        return self.executor.submit(self.deliver, notification)

    # Retry up to 3 attempts
    def deliver(self, notification):
        for attempt in range(3):
            try:
                channel = self.get_channel(notification.channel)
                channel.send(notification)
                return True
            except Exception as error:
                print(f"Attempt {attempt + 1} failed: {error}")

                if attempt < 2:
                    sleep(0.2 * (2 ** attempt))

        print(f"Notification {notification.notification_id} failed")
        return False

    def shutdown(self):
        self.closed = True
        self.executor.shutdown(wait=True)


def main():
    service = NotificationService()

    observer = NotificationObserver(service)
    service.subscribe("ORDER_SHIPPED", observer)

    service.publish(
        "ORDER_SHIPPED",
        {
            "order_id": "ORD-101",
            "email": "user@example.com",
            "phone": "9999999999"
        }
    )

    service.send_async(
        Notification(
            recipient="device-token-123",
            channel=ChannelType.PUSH,
            body="Your order is on its way!"
        )
    )

    # Wait for submitted notifications before exiting
    service.shutdown()


if __name__ == "__main__":
    main()
