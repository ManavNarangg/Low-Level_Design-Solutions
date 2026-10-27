from abc import ABC, abstractmethod
from enum import Enum, auto
import threading
from typing import Dict, Optional


# ==================== ENUM ====================

class OperationType(Enum):
    DEPOSIT_CASH = auto()
    WITHDRAW_CASH = auto()
    CHECK_BALANCE = auto()


# ==================== DOMAIN CLASSES ====================

class Card:
    def __init__(self, card_number: str, pin: str) -> None:
        self._card_number = card_number
        self._pin = pin

    @property
    def card_number(self) -> str:
        return self._card_number

    @property
    def pin(self) -> str:
        return self._pin


class Account:
    def __init__(self, account_number: str, balance: float) -> None:
        if balance < 0:
            raise ValueError("Initial balance cannot be negative")

        self._account_number = account_number
        self._balance = balance
        self._lock = threading.Lock()

    def withdraw(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Amount must be positive")

        with self._lock:
            if amount > self._balance:
                raise ValueError("Insufficient funds")
            self._balance -= amount

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Amount must be positive")

        with self._lock:
            self._balance += amount

    def balance(self) -> float:
        with self._lock:
            return self._balance


# ==================== BANK SERVICE ====================

class BankService:
    def __init__(self) -> None:
        self.cards: Dict[str, Card] = {}
        self.accounts: Dict[str, Account] = {}
        self.card_account_map: Dict[Card, Account] = {}

        # Test setup: in a real system, the bank would manage these records.
        account = Account("ACC1", 1000)
        card = Card("1234-5678", "4321")

        self.accounts[account._account_number] = account
        self.cards[card.card_number] = card
        self.card_account_map[card] = account

    def get_card(self, card_number: str) -> Optional[Card]:
        return self.cards.get(card_number)

    def authenticate(self, card: Optional[Card], pin: str) -> bool:
        return card is not None and card.pin == pin

    def _get_account(self, card: Card) -> Account:
        account = self.card_account_map.get(card)
        if account is None:
            raise ValueError("No account is linked to this card")
        return account

    def get_balance(self, card: Card) -> float:
        return self._get_account(card).balance()

    def deposit(self, card: Card, amount: float) -> None:
        self._get_account(card).deposit(amount)

    def withdraw(self, card: Card, amount: float) -> None:
        self._get_account(card).withdraw(amount)


# ==================== CHAIN OF RESPONSIBILITY ====================

class DispenseChain(ABC):
    @abstractmethod
    def set_next(self, next_chain: Optional["DispenseChain"]) -> None:
        pass

    @abstractmethod
    def can_dispense(self, amount: int) -> bool:
        pass

    @abstractmethod
    def dispense(self, amount: int) -> None:
        pass


class NoteDispenser(DispenseChain):
    def __init__(self, note_value: int, num_notes: int) -> None:
        self._note_value = note_value
        self._num_notes = num_notes
        self._next_chain: Optional[DispenseChain] = None

    def set_next(self, next_chain: Optional[DispenseChain]) -> None:
        self._next_chain = next_chain

    def can_dispense(self, amount: int) -> bool:
        if amount < 0:
            return False

        notes_used = min(amount // self._note_value, self._num_notes)
        remaining_amount = amount - notes_used * self._note_value

        if remaining_amount == 0:
            return True

        return (
            self._next_chain is not None
            and self._next_chain.can_dispense(remaining_amount)
        )

    def dispense(self, amount: int) -> None:
        # Call can_dispense before this method so the chain can handle
        # the full amount before any inventory is changed.
        if not self.can_dispense(amount):
            raise ValueError("Cannot dispense the requested amount")

        notes_used = min(amount // self._note_value, self._num_notes)

        if notes_used:
            self._num_notes -= notes_used
            print(f"Dispensing {notes_used} x ₹{self._note_value}")

        remaining_amount = amount - notes_used * self._note_value

        if remaining_amount > 0 and self._next_chain is not None:
            self._next_chain.dispense(remaining_amount)


class NoteDispenser100(NoteDispenser):
    def __init__(self, num_notes: int) -> None:
        super().__init__(100, num_notes)


class NoteDispenser50(NoteDispenser):
    def __init__(self, num_notes: int) -> None:
        super().__init__(50, num_notes)


class NoteDispenser20(NoteDispenser):
    def __init__(self, num_notes: int) -> None:
        super().__init__(20, num_notes)


class CashDispenser:
    def __init__(self, first_handler: DispenseChain) -> None:
        self._first_handler = first_handler

    def can_dispense(self, amount: int) -> bool:
        return amount > 0 and self._first_handler.can_dispense(amount)

    def dispense(self, amount: int) -> None:
        if not self.can_dispense(amount):
            raise ValueError(
                "Cannot dispense the requested amount with available notes"
            )
        self._first_handler.dispense(amount)


# ==================== STATE PATTERN ====================

class ATMState(ABC):
    @abstractmethod
    def insert_card(self, atm: "ATM", card_number: str) -> None:
        pass

    @abstractmethod
    def enter_pin(self, atm: "ATM", pin: str) -> None:
        pass

    @abstractmethod
    def select_operation(
        self, atm: "ATM", operation: OperationType, *args
    ) -> None:
        pass

    @abstractmethod
    def eject_card(self, atm: "ATM") -> None:
        pass


class IdleState(ATMState):
    def insert_card(self, atm: "ATM", card_number: str) -> None:
        card = atm._bank_service.get_card(card_number)
        if card is None:
            print("Card not recognized")
            return

        atm._current_card = card
        atm.change_state(HasCardState())
        print("Card inserted. Enter PIN.")

    def enter_pin(self, atm: "ATM", pin: str) -> None:
        print("Insert card first")

    def select_operation(
        self, atm: "ATM", operation: OperationType, *args
    ) -> None:
        print("Insert card first")

    def eject_card(self, atm: "ATM") -> None:
        print("No card to eject")


class HasCardState(ATMState):
    def insert_card(self, atm: "ATM", card_number: str) -> None:
        print("Card already inserted")

    def enter_pin(self, atm: "ATM", pin: str) -> None:
        if atm.authenticate(pin):
            atm.change_state(AuthenticatedState())
            print("Authenticated")
        else:
            print("Incorrect PIN")
            self.eject_card(atm)

    def select_operation(
        self, atm: "ATM", operation: OperationType, *args
    ) -> None:
        print("Enter PIN first")

    def eject_card(self, atm: "ATM") -> None:
        atm._current_card = None
        atm.change_state(IdleState())
        print("Card ejected")


class AuthenticatedState(ATMState):
    def insert_card(self, atm: "ATM", card_number: str) -> None:
        print("Session in progress")

    def enter_pin(self, atm: "ATM", pin: str) -> None:
        print("Already authenticated")

    def select_operation(
        self, atm: "ATM", operation: OperationType, *args
    ) -> None:
        try:
            if operation == OperationType.WITHDRAW_CASH:
                if len(args) != 1:
                    raise ValueError("Withdrawal amount is required")
                atm.withdraw_cash(args[0])
            elif operation == OperationType.DEPOSIT_CASH:
                if len(args) != 1:
                    raise ValueError("Deposit amount is required")
                atm.deposit_cash(args[0])
            elif operation == OperationType.CHECK_BALANCE:
                print(f"Current balance: ₹{atm.check_balance():.2f}")
        except (ValueError, KeyError, IndexError) as error:
            print(f"Operation failed: {error}")
        finally:
            self.eject_card(atm)

    def eject_card(self, atm: "ATM") -> None:
        atm._current_card = None
        atm.change_state(IdleState())
        print("Card ejected")


# ==================== ATM SINGLETON ====================

class ATM:
    _instance: Optional[ATM] = None
    _instance_lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._bank_service = BankService()
        self._current_state: ATMState = IdleState()
        self._current_card: Optional[Card] = None

        c100 = NoteDispenser100(10)
        c50 = NoteDispenser50(20)
        c20 = NoteDispenser20(30)

        c100.set_next(c50)
        c50.set_next(c20)

        self._cash_dispenser = CashDispenser(c100)
        self._initialized = True

    @classmethod
    def get_instance(cls) -> ATM:
        return cls()

    def insert_card(self, card_number: str) -> None:
        self._current_state.insert_card(self, card_number)

    def enter_pin(self, pin: str) -> None:
        self._current_state.enter_pin(self, pin)

    def select_operation(self, operation: OperationType, *args) -> None:
        self._current_state.select_operation(self, operation, *args)

    def authenticate(self, pin: str) -> bool:
        return self._bank_service.authenticate(self._current_card, pin)

    def withdraw_cash(self, amount: int) -> None:
        if not isinstance(amount, int) or amount <= 0:
            raise ValueError("Withdrawal amount must be a positive integer")

        if not self._cash_dispenser.can_dispense(amount):
            raise ValueError(
                "ATM cannot dispense this amount with its available notes"
            )

        # Debit the account only after confirming that the ATM can make the amount.
        self._bank_service.withdraw(self._current_card, amount)
        self._cash_dispenser.dispense(amount)
        print(f"Successfully withdrew ₹{amount}")

    def deposit_cash(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self._bank_service.deposit(self._current_card, amount)
        print(f"Successfully deposited ₹{amount:.2f}")

    def check_balance(self) -> float:
        return self._bank_service.get_balance(self._current_card)

    def change_state(self, new_state: ATMState) -> None:
        self._current_state = new_state


# ==================== DEMO / TEST SETUP ====================

def main() -> None:
    atm = ATM.get_instance()
    bank = atm._bank_service
    

    print("--- Withdraw ₹270 ---")
    atm.insert_card("1234-5678")
    atm.enter_pin("4321")
    atm.select_operation(OperationType.WITHDRAW_CASH, 270)

    print("\n--- Check balance ---")
    atm.insert_card("1234-5678")
    atm.enter_pin("4321")
    atm.select_operation(OperationType.CHECK_BALANCE)

    print("\n--- Wrong PIN ---")
    atm.insert_card("1234-5678")
    atm.enter_pin("0000")

    print("\n--- Amount ATM cannot dispense: ₹45 ---")
    atm.insert_card("1234-5678")
    atm.enter_pin("4321")
    atm.select_operation(OperationType.WITHDRAW_CASH, 45)

    print("\n--- Singleton check ---")
    print("Same instance:", atm is ATM.get_instance())


if __name__ == "__main__":
    main()
