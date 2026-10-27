from threading import Lock

class Node:
    def __init__(self, key, value, ttl):
        self.key = key
        self.value = value
        self.ttl = time.monotonic() + ttl
        self.prev = None
        self.next = None


class DoublyLinkedList:
    def __init__(self):
        self.head = Node(None, None, None)  # Dummy head
        self.tail = Node(None, None, None)  # Dummy tail
        self.head.next = self.tail
        self.tail.prev = self.head

    def add_to_front(self, node: Node):
        node.next = self.head.next
        node.prev = self.head
        node.next.prev = node
        self.head.next = node

    def remove(self, node: Node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def move_to_front(self, node: Node):         
        self.remove(node)
        self.add_to_front(node)

    def remove_from_last(self) -> Node:
        if self.tail.prev == self.head:
            return None  # List is empty
        last = self.tail.prev
        self.remove(last)
        return last

class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = {}
        self.list = DoublyLinkedList()
        self.lock = Lock()

    def get(self, key: int) -> int:
        with self.lock:
            if key not in self.cache:
                return -1
            node = self.cache[key]
            if time.monotonic() >= node.ttl:
                # If the node has expired, remove it from the cache and list
                self.list.remove(node)
                del self.cache[key]
                return -1
            self.list.move_to_front(node)
            return node.value

    def put(self, key: int, value: int, ttl: float) -> None:
        with self.lock:
            if key in self.cache:
                node = self.cache[key]
                node.value = value
                node.ttl = time.monotonic() + ttl
                self.list.move_to_front(node)
            else:
                if len(self.cache) >= self.capacity:
                    last_node = self.list.remove_from_last()
                    if last_node:
                        del self.cache[last_node.key]
                
                node = Node(key, value)
                self.list.add_to_front(node)
                self.cache[key] = node

# Sharding based on hashing, we're creating multiple LRU caches to distribute the load and reduce contention. Each shard will handle a subset of keys based on their hash values.
class StripedLRUCache:
    def __init__(self, per_shard_capacity: int, num_shards: int = 4):
        self.num_shards = num_shards
        # each shard has it's own lock, map and DoublyLinkedList so unrelated keys never block each other
        self.shards = [LRUCache(per_shard_capacity) for _ in range(num_shards)]

    # Here's how the sharding works: we divide the total capacity by the number of shards to determine the capacity of each individual LRU cache. 
    # When we want to access or modify a key, we compute its hash and use it to determine which shard (LRU cache) should handle that key. 
    # This way, we can reduce contention and improve performance in multi-threaded scenarios.
    def _get_shard(self, key: int) -> LRUCache:
        return self.shards[hash(key) % self.num_shards]

    def get(self, key: int) -> int:
        shard = self._get_shard(key)
        return shard.get(key)

    def put(self, key: int, value: int) -> None:
        shard = self._get_shard(key)
        return shard.put(key, value)


def main():
    print("=== Striped LRU Cache Demo ===\n")

    cache = StripedLRUCache(
        per_shard_capacity=3,
        num_shards=4
    )

    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)

    print(cache.get("a"))  # 1
    print(cache.get("b"))  # 2

    cache.put("d", 4)
    print(cache.get("d"))  # 4

    print(cache.get("missing"))  # -1


if __name__ == "__main__":
    main()