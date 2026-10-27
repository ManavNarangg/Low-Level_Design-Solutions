
from abc import ABC, abstractmethod
from collections import defaultdict
from enum import Enum
from threading import RLock
from uuid import uuid4

class User:
    def __init__(self, name):
        self.user_id = str(uuid4())
        self.name = name

class SplitType(Enum):
    EQUAL = "EQUAL"
    EXACT = "EXACT"
    PERCENTAGE = "PERCENTAGE"

class SplitStrategy(ABC):
    @abstractmethod
    def calculate(self, amount, participants):
        pass

class EqualSplitStrategy(SplitStrategy):
    def calculate(self, amount, participants):
        if not participants:
            raise ValueError("Participants cannot be empty")

        share = round(amount / len(participants), 2)
        splits = {uid: share for uid in participants}

        # Assign any rounding remainder to the last participant.
        last_user = list(splits)[-1]
        splits[last_user] = round(
            splits[last_user] + amount - sum(splits.values()), 2
        )
        return splits

class ExactSplitStrategy(SplitStrategy):
    def calculate(self, amount, participants):
        splits = {
            uid: round(value, 2)
            for uid, value in participants.items()
        }

        if any(value < 0 for value in splits.values()):
            raise ValueError("Split amounts cannot be negative")

        if round(sum(splits.values()), 2) != round(amount, 2):
            raise ValueError("Splits must equal the total amount")

        return splits

class PercentageSplitStrategy(SplitStrategy):
    def calculate(self, amount, participants):
        if any(value < 0 for value in participants.values()):
            raise ValueError("Percentages cannot be negative")

        if round(sum(participants.values()), 2) != 100:
            raise ValueError("Percentages must total 100")

        splits = {}
        user_ids = list(participants)
        remaining = round(amount, 2)

        for uid in user_ids[:-1]:
            share = round(amount * participants[uid] / 100, 2)
            splits[uid] = share
            remaining = round(remaining - share, 2)

        splits[user_ids[-1]] = remaining
        return splits

class Expense:
    def __init__(self, description, amount, payer_id, splits, group_id=None):
        self.expense_id = str(uuid4())
        self.description = description
        self.amount = round(amount, 2)
        self.payer_id = payer_id
        self.splits = splits
        self.group_id = group_id

class Group:
    def __init__(self, name, creator_id):
        self.group_id = str(uuid4())
        self.name = name
        self.member_ids = {creator_id}
        self.expenses = []

    def add_member(self, user_id):
        self.member_ids.add(user_id)

class ExpenseObserver(ABC):
    @abstractmethod
    def on_expense_added(self, expense):
        pass


class LoggingObserver(ExpenseObserver):
    def on_expense_added(self, expense):
        print(f"Expense added: {expense.description}")

class BalanceSheet:
    def __init__(self):
        # balances[creditor][debtor] = amount debtor owes creditor
        self.balances = defaultdict(lambda: defaultdict(float))

    def apply_expense(self, payer_id, splits):
        for user_id, share in splits.items():
            if user_id == payer_id:
                continue

            self.balances[payer_id][user_id] = round(
                self.balances[payer_id][user_id] + share, 2
            )
            self.balances[user_id][payer_id] = round(
                self.balances[user_id][payer_id] - share, 2
            )

    def get_balance(self, user_id):
        result = {}

        for other_id in self.balances:
            amount = self.balances[user_id][other_id]

            if amount > 0:
                result[other_id] = amount
            elif amount < 0:
                result[other_id] = -amount

        return result

class ExpenseService:
    def __init__(self):
        self.users = {}
        self.groups = {}
        self.expenses = {}
        self.balance_sheet = BalanceSheet()

        self.strategies = {
            SplitType.EQUAL: EqualSplitStrategy(),
            SplitType.EXACT: ExactSplitStrategy(),
            SplitType.PERCENTAGE: PercentageSplitStrategy(),
        }

        self.observers = []
        self.add_observer(LoggingObserver())
        self.lock = RLock()

    def add_user(self, user):
        with self.lock:
            self.users[user.user_id] = user

    def create_group(self, name, creator_id):
        with self.lock:
            if creator_id not in self.users:
                raise ValueError("Unknown creator")

            group = Group(name, creator_id)
            self.groups[group.group_id] = group
            return group

    def add_observer(self, observer):
        with self.lock:
            self.observers.append(observer)

    def add_expense(
        self, description, amount, payer_id,
        split_type, participants, group_id=None
    ):
        with self.lock:
            if amount <= 0:
                raise ValueError("Amount must be positive")

            if not participants:
                raise ValueError("Participants cannot be empty")


            if group_id is not None:
                group = self.groups.get(group_id)

                if group is None:
                    raise ValueError("Unknown group")

            strategy = self.strategies[split_type]
            splits = strategy.calculate(amount, participants)

            expense = Expense(
                description, amount, payer_id, splits, group_id
            )

            self.balance_sheet.apply_expense(payer_id, splits)
            self.expenses[expense.expense_id] = expense

            if group_id is not None:
                group.expenses.append(expense.expense_id)

            observers = list(self.observers)

        for observer in observers:
            try:
                observer.on_expense_added(expense)
            except Exception:
                pass

        return expense

if __name__ == "__main__":
    service = ExpenseService()

    alice = User("Alice")
    bob = User("Bob")
    charlie = User("Charlie")

    for user in [alice, bob, charlie]:
        service.add_user(user)

    group = service.create_group("Goa Trip", alice.user_id)
    group.add_member(bob.user_id)
    group.add_member(charlie.user_id)

    service.add_expense(
        description="Dinner",
        amount=1200,
        payer_id=alice.user_id,
        split_type=SplitType.EQUAL,
        participants={
            alice.user_id: None,
            bob.user_id: None,
            charlie.user_id: None,
        },
        group_id=group.group_id,
    )

    print("\nAlice's balances:")
    for user_id, amount in service.balance_sheet.get_balance(
        alice.user_id
    ).items():
        print(service.users[user_id].name, amount)
