import uuid
from abc import ABC, abstractmethod
from datetime import date, timedelta
from enum import Enum
from threading import RLock, Thread


class LoanStatus(Enum):
    ACTIVE = "ACTIVE"
    RETURNED = "RETURNED"


class Member:
    def __init__(self, name: str, member_id: int):
        self.name = name
        self.member_id = member_id


class Book:
    def __init__(self, book_id: int, title: str, author: str, total_copies: int):
        self.book_id = book_id
        self.title = title
        self.author = author
        self.total_copies = total_copies
        self.available_copies = total_copies

    def add_copies(self, count: int) -> None:
        if count <= 0:
            raise ValueError("Count must be positive")
        self.total_copies += count
        self.available_copies += count

    def is_available(self) -> bool:
        return self.available_copies > 0

    def borrow_copy(self) -> bool:
        if not self.is_available():
            return False
        self.available_copies -= 1
        return True

    def return_copy(self) -> None:
        if self.available_copies >= self.total_copies:
            raise ValueError("All copies are already available")
        self.available_copies += 1


# Strategy pattern
class FineStrategy(ABC):
    @abstractmethod
    def calculate_fine(self, due_date: date, return_date: date) -> float:
        pass


class StandardFine(FineStrategy):
    FINE_PER_OVERDUE_DAY = 2.0

    def calculate_fine(self, due_date: date, return_date: date) -> float:
        if return_date <= due_date:
            return 0.0
        overdue_days = (return_date - due_date).days
        return overdue_days * self.FINE_PER_OVERDUE_DAY


class Loan:
    def __init__(self, book_id: int, loan_id: str, member_id: int, due_date: date):
        self.book_id = book_id
        self.loan_id = loan_id
        self.member_id = member_id
        self.due_date = due_date
        self.return_date = None
        self.status = LoanStatus.ACTIVE

    def is_active(self) -> bool:
        return self.status == LoanStatus.ACTIVE

    def mark_returned(self, return_date: date) -> None:
        if not self.is_active():
            raise ValueError("Loan has already been returned")
        self.return_date = return_date
        self.status = LoanStatus.RETURNED


class Library:
    LOAN_PERIOD_DAYS = 14

    def __init__(self, strategy: FineStrategy):
        self._strategy = strategy
        self.loans: dict[str, Loan] = {}
        self.books: dict[int, Book] = {}
        self.members: dict[int, Member] = {}
        self._lock = RLock()

    def add_member(self, member: Member) -> None:
        with self._lock:
            if member.member_id in self.members:
                raise ValueError("Member already exists")
            self.members[member.member_id] = member

    def add_book(self, book: Book) -> None:
        with self._lock:
            if book.book_id in self.books:
                raise ValueError("Book already exists")
            self.books[book.book_id] = book

    def search_by_title(self, query: str) -> list[Book]:
        with self._lock:
            query = query.lower()
            return [
                book for book in self.books.values()
                if query in book.title.lower()
            ]

    def borrow_book(self, member_id: int, book_id: int, today: date) -> Loan | None:
        with self._lock:
            if member_id not in self.members:
                return None

            if book_id not in self.books:
                return None

            # One active loan per member
            for loan in self.loans.values():
                if loan.member_id == member_id and loan.is_active():
                    print("Member already has an active loan")
                    return None

            book = self.books[book_id]
            if not book.borrow_copy():
                return None

            loan_id = str(uuid.uuid4())
            loan = Loan(
                book_id=book_id,
                loan_id=loan_id,
                member_id=member_id,
                due_date=today + timedelta(days=self.LOAN_PERIOD_DAYS),
            )
            self.loans[loan_id] = loan
            return loan

    def return_book(self, loan_id: str, today: date) -> float | None:
        with self._lock:
            loan = self.loans.get(loan_id)
            if loan is None or not loan.is_active():
                return None

            fine = self._strategy.calculate_fine(loan.due_date, today)
            self.books[loan.book_id].return_copy()
            loan.mark_returned(today)
            return fine


def main():
    library = Library(StandardFine())

    library.add_book(Book(1, "Clean Code", "Robert Martin", 2))
    library.add_book(Book(2, "Clean Architecture", "Robert Martin", 1))
    library.add_book(Book(3, "Refactoring", "Martin Fowler", 1))

    library.add_member(Member("Aman", 101))
    library.add_member(Member("Riya", 102))
    library.add_member(Member("Karan", 103))

    today = date(2026, 1, 1)

    print("=== Search ===")
    for book in library.search_by_title("clean"):
        print(f"{book.title} by {book.author} ({book.available_copies}/{book.total_copies})")

    print("\n=== Borrowing ===")
    loan1 = library.borrow_book(101, 1, today)
    loan2 = library.borrow_book(102, 1, today)
    print("Aman borrows Clean Code:", "OK" if loan1 else "Failed")
    print("Riya borrows Clean Code:", "OK" if loan2 else "Failed")
    print("Copies left:", library.books[1].available_copies)

    print("\n=== Edge cases ===")
    print("Aman borrows a 2nd book:", library.borrow_book(101, 3, today))
    print("Unknown member:", library.borrow_book(999, 3, today))
    print("Unknown book:", library.borrow_book(103, 999, today))

    # Karan takes the only copy of Refactoring, then nobody else can
    loan3 = library.borrow_book(103, 3, today)
    print("Karan borrows Refactoring:", "OK" if loan3 else "Failed")
    print("Refactoring available:", library.books[3].is_available())

    print("\n=== Returning ===")
    on_time = library.return_book(loan1.loan_id, date(2026, 1, 10))
    print(f"Aman returns on time, fine: Rs. {on_time:.2f}")

    late = library.return_book(loan2.loan_id, date(2026, 1, 20))  # due Jan 15 -> 5 days late
    print(f"Riya returns 5 days late, fine: Rs. {late:.2f}")

    print("Double return:", library.return_book(loan1.loan_id, date(2026, 1, 11)))
    print("Invalid loan id:", library.return_book("does-not-exist", today))
    print("Copies of Clean Code:", library.books[1].available_copies)

    print("\n=== Concurrency: 20 members race for 1 copy ===")
    race_lib = Library(StandardFine())
    race_lib.add_book(Book(1, "Last Copy", "Someone", 1))
    for i in range(20):
        race_lib.add_member(Member(f"User{i}", i))

    results = []

    def attempt(member_id: int):
        results.append(race_lib.borrow_book(member_id, 1, today))

    threads = [Thread(target=attempt, args=(i,)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    successes = sum(1 for r in results if r is not None)
    print("Successful borrows:", successes)
    print("Available copies:", race_lib.books[1].available_copies)


if __name__ == "__main__":
    main()