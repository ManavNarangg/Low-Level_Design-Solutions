from enum import Enum
from typing import List
from threading import Lock

class Note(Enum):
    NOTE_100 = 100
    NOTE_200 = 200
    NOTE_500 = 500

    def get_value(self) -> int:
        return self.value

class Item:
    def __init__(self, name: str, code: str, price: int):
        self.name = name
        self.code = code
        self.price = price

    @property
    def get_name(self) -> str:
        return self.name

    @property
    def get_code(self) -> str:
        return self.code

    @property
    def get_price(self) -> int:
        return self.price

class Inventory:
    def __init__(self):
        self.item_map: dict[str, Item] = {}
        self.stock_map: dict[str, int] = {}

    def add_item(self, item: Item, quantity: int):
        self.item_map[item.get_code()] = item
        self.stock_map[item.get_code()] = quantity

    def get_item(self, code: str) -> Item:
        return self.item_map[code]

    def isAvailable(self, code: str) -> bool:
        return self.stock_map.get(code, 0) > 0

    def reduceStock(self, code: str) -> void:
        self.stock_map[code] = self.stock_map[code] - 1

class VendingMachineState(ABC):
    def __init__(self, machine: VendingMachine):
        self.machine = machine

    def select_item(self, code: str):
        pass

    def add_note(self, note: Node):
        pass

    def dispense(self):
        pass

class IdleState(VendingMachineState):
    def select_item(self, code: str):
        if not self.machine.get_inventory().isAvailable(code):
            print("Item not available.")
            return
        self.machine.set_selected_item(code)
        self.machine.set_state(ItemSelectedState(self.machine))

    def add_note(self, note: Note):
        print("Please select item first")

    def dispense(self):
        print("Please select item first")

class ItemSelectedStae(VendingMachineState):
    def select_item(self, code: str):
        print("Item already selected")

    def add_note(self, note: Note):
        self.machine.add_balance(coin.get_value())
        selected_item = self.machine.get_selected_item()

        if selected_item and self.machine.get_balance() > selected_item.get_price():
            print("Insufficient balance")
            self.machine.set_state(HasMoneyState(self.machine))

    def dispense(self):
        print("Please insert sufficient money.")

class HasMoneyState(VendingMachinState):
    def select_item(self, code: str):
        print("Item alread selected")

    def add_note(self, note: Note):
        self.machine.add_balance(coin.get_value())
        print(f"Additional coin inserted: {coin.get_value()}¢ ({coin.name}) - will be returned as change.")

    def dispense(self):
        self.machine.set_state(DispenseState(self.machine))
        self.machine.dispense_item()

class DispenseState(VendingMachineState):
    
    def add_note(self, note: Note):
        print("Currently dispensing. Please wait.")
    
    def select_item(self, code: str):
        print("Currently dispensing. Please wait.")
    
    def dispense(self):
        # Already triggered by HasMoneyState
        print("Dispensing in progress...")


class VendingMachine:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(VendingMachine, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized') or not self._initialized:
            self.inventory = Inventory()
            self._initialized = True
            self.current_state = IdelState(self)
            self.selected_item_code = None
            self.balance = 0

    @classmethod
    def get_instance(cls):
        return cls()

    def add_note(self, note: Note) -> None:
        self.current_state.add_note(Note)

    def select_item(self, code: str) -> None:
        self.current_state.select_item(code)

    def dispense(self) -> None:
        self.current_state.dispense()

    def getInventory(self) -> Inventory:
        return self.inventory

    def setState(self, state: VendingMachineState) -> None:
        self.current_state = state

    def add_item(self, code: Code, name: str, price: int, quantity: int) -> Item:
        item = Item(code, name, price)
        self.inventory.add_item(item, quantity)
        return Item

    def dispense_item(self):
        item = self.inventory.get_item(self.selected_item_code)
        if self.balance >= item.get_price():
            self.inventory.reduce_stock(self.selected_item_code)
            self.balance -= item.price
        self.selected_item_code = None
        self.balance = 0

    def add_balance(self, value: int) -> None:
        self.balance += value

    def get_selected_item(self):
        self.inventory.get_item(self.selected_item_code)
        
