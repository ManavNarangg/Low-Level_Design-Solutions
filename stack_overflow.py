import uuid
import threading
from enum import Enum
from abc import ABC, abstractmethod
from datetime import datetime


# ==================== ENUMS ====================

class VoteType(Enum):
    UPVOTE = 1
    DOWNVOTE = -1


# ==================== USER ====================

class User:
    def __init__(self, name: str):
        self.id = str(uuid.uuid4())
        self.name = name
        self.reputation = 0
        self.notifications = []
        self._lock = threading.Lock()

    def update_reputation(self, points: int):
        with self._lock:
            self.reputation += points

    def get_reputation(self) -> int:
        with self._lock:
            return self.reputation

    def notify(self, message: str):
        with self._lock:
            self.notifications.append(message)

    def __str__(self):
        return f"User({self.name}, reputation={self.get_reputation()})"


# ==================== TAG ====================

class Tag:
    def __init__(self, name: str):
        self.id = str(uuid.uuid4())
        self.name = name
        self.questions = set()


# ==================== COMMENT ====================

class Comment:
    def __init__(self, author: User, body: str):
        self.id = str(uuid.uuid4())
        self.author = author
        self.body = body
        self.created_at = datetime.now()


# ==================== VOTE ====================

class Vote:
    def __init__(self, user: User, post_id: str, vote_type: VoteType):
        self.id = str(uuid.uuid4())
        self.user_id = user.id
        self.post_id = post_id
        self.type = vote_type
        self.created_at = datetime.now()


# ==================== OBSERVER PATTERN ====================

class Observer(ABC):
    @abstractmethod
    def update(self, event: str, post, actor: User):
        pass


class NotificationObserver(Observer):
    def update(self, event: str, post, actor: User):
        recipient = post.author

        if recipient.id == actor.id:
            return

        if event == "upvoted":
            message = f"{actor.name} upvoted your post."

        elif event == "answered":
            message = (
                f"{actor.name} answered your question: "
                f"{post.title}"
            )

        else:
            return

        recipient.notify(message)
        print(f"Notification for {recipient.name}: {message}")


class Subject:
    def __init__(self):
        self._observers = []
        self._observer_lock = threading.Lock()

    def subscribe(self, observer: Observer):
        with self._observer_lock:
            if observer not in self._observers:
                self._observers.append(observer)

    def unsubscribe(self, observer: Observer):
        with self._observer_lock:
            if observer in self._observers:
                self._observers.remove(observer)

    def notify_observers(self, event: str, post, actor: User):
        with self._observer_lock:
            observers = self._observers.copy()

        for observer in observers:
            observer.update(event, post, actor)


# ==================== POST ====================

class Post(Subject, ABC):
    def __init__(self, author: User, body: str):
        super().__init__()

        self.id = str(uuid.uuid4())
        self.author = author
        self.body = body
        self.created_at = datetime.now()
        self.voters = {}
        self.comments = []

        self._lock = threading.Lock()

    @property
    def vote_count(self) -> int:
        with self._lock:
            return sum(vote.type.value for vote in self.voters.values())

    @abstractmethod
    def vote_reward(self) -> int:
        pass

    def vote(self, user: User, vote_type: VoteType):
        if not isinstance(vote_type, VoteType):
            raise ValueError("Invalid vote type")

        if user.id == self.author.id:
            raise ValueError("Users cannot vote on their own posts")

        with self._lock:
            old_vote = self.voters.get(user.id)

            # Voting the same way again changes nothing.
            if old_vote and old_vote.type == vote_type:
                return

            old_value = old_vote.type.value if old_vote else 0
            new_vote = Vote(user, self.id, vote_type)
            self.voters[user.id] = new_vote

            # Calculate the change in vote value.
            delta = new_vote.type.value - old_value
            self.author.update_reputation(delta * self.vote_reward())

        if vote_type == VoteType.UPVOTE:
            self.notify_observers("upvoted", self, user)

    def add_comment(self, comment: Comment):
        with self._lock:
            self.comments.append(comment)


# ==================== QUESTION ====================

class Question(Post):
    def __init__(self, author: User, body: str, title: str):
        super().__init__(author, body)

        self.title = title
        self.answers = {}
        self.tags = set()

    def vote_reward(self) -> int:
        return 5

    def answer_question(self, answer):
        if answer.question.id != self.id:
            raise ValueError("Answer belongs to a different question")

        with self._lock:
            if answer.id in self.answers:
                raise ValueError("Answer already exists")

            self.answers[answer.id] = answer

        # Notify the question author that someone answered.
        self.notify_observers("answered", self, answer.author)


class Answer(Post):
    def __init__(self, author: User, question: Question, body: str):
        super().__init__(author, body)
        self.question = question

    def vote_reward(self) -> int:
        return 10


class StackOverFlowService:
    def __init__(self):
        self.users = {}
        self.questions = {}
        self.answers = {}
        self.tags = {}

        self.notification_observer = NotificationObserver()
        self._lock = threading.Lock()

    def register_user(self, name: str) -> User:
        user = User(name)

        with self._lock:
            self.users[user.id] = user

        return user

    def _register_observer(self, post: Post):
        post.subscribe(self.notification_observer)

    def ask_question(
        self,
        user: User,
        body: str,
        title: str,
        tag_names=None
    ) -> Question:
        if not title.strip() or not body.strip():
            raise ValueError("Question title and body cannot be empty")

        question = Question(user, body, title)
        self._register_observer(question)

        with self._lock:
            for tag_name in tag_names or []:
                normalized_name = tag_name.strip().lower()

                if not normalized_name:
                    continue

                if normalized_name not in self.tags:
                    self.tags[normalized_name] = Tag(normalized_name)

                tag = self.tags[normalized_name]
                question.tags.add(tag)
                tag.questions.add(question.id)

            self.questions[question.id] = question

        return question

    def answer_question(
        self,
        user: User,
        question: Question,
        body: str
    ) -> Answer:
        if not body.strip():
            raise ValueError("Answer body cannot be empty")

        with self._lock:
            if question.id not in self.questions:
                raise ValueError("Question does not exist")

        answer = Answer(user, question, body)
        self._register_observer(answer)

        # Adds the answer and notifies the question author.
        question.answer_question(answer)

        with self._lock:
            self.answers[answer.id] = answer

        return answer

    def add_comment(self, user: User, post: Post, body: str) -> Comment:
        if not body.strip():
            raise ValueError("Comment cannot be empty")

        if not isinstance(post, Post):
            raise ValueError("Comments can only be added to posts")

        comment = Comment(user, body)
        post.add_comment(comment)
        return comment

    def vote(self, user: User, post: Post, vote_type: VoteType):
        if not isinstance(post, Post):
            raise ValueError("Votes can only be added to posts")

        post.vote(user, vote_type)

    def search_questions(self, query=None, tag_name=None):
        with self._lock:
            questions = list(self.questions.values())

        results = []

        for question in questions:
            if query:
                search_text = (
                    question.title + " " + question.body
                ).lower()

                if query.lower() not in search_text:
                    continue

            if tag_name:
                tag_names = {tag.name for tag in question.tags}

                if tag_name.lower() not in tag_names:
                    continue

            results.append(question)

        return results


# ==================== MAIN ====================

def main():
    service = StackOverFlowService()

    # Register users.
    alice = service.register_user("Alice")
    bob = service.register_user("Bob")
    charlie = service.register_user("Charlie")

    # Alice asks a question.
    question = service.ask_question(
        user=alice,
        title="How does Python threading work?",
        body="Can Python threads execute CPU-bound tasks in parallel?",
        tag_names=["python", "threading"]
    )

    # Bob answers Alice's question.
    answer = service.answer_question(
        user=bob,
        question=question,
        body="In standard CPython, the GIL limits parallel execution "
             "of Python bytecode by multiple threads."
    )

    # Charlie upvotes the question and answer.
    service.vote(charlie, question, VoteType.UPVOTE)
    service.vote(charlie, answer, VoteType.UPVOTE)

    # Alice comments on Bob's answer.
    service.add_comment(
        alice,
        answer,
        "Thanks, that clarifies it!"
    )

    # Display results.
    print("\n--- Results ---")
    print("Question score:", question.vote_count)
    print("Answer score:", answer.vote_count)

    print("Alice's reputation:", alice.get_reputation())
    print("Bob's reputation:", bob.get_reputation())

    print("\nAlice's notifications:")
    for notification in alice.notifications:
        print("-", notification)

    print("\nBob's notifications:")
    for notification in bob.notifications:
        print("-", notification)

    print("\nSearch results:")
    for result in service.search_questions(tag_name="python"):
        print("-", result.title)

    # Demonstrate concurrent voting.
    print("\n--- Concurrent Voting ---")

    voters = [
        service.register_user(f"Voter{i}")
        for i in range(10)
    ]

    threads = []

    for voter in voters:
        thread = threading.Thread(
            target=service.vote,
            args=(voter, question, VoteType.UPVOTE)
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    print("Question score after concurrent votes:", question.vote_count)
    print("Alice's reputation after concurrent votes:", alice.get_reputation())


if __name__ == "__main__":
    main()