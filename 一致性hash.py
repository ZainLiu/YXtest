import binascii


class Map:
    hash_func = binascii.crc32
    replicas = 1

    def __init__(self, hash_func=None, replicas=None):
        if hash_func:
            self.hash_func = hash_func
        if replicas:
            self.replicas = replicas
        self.keys = []
        self.hash_map = dict()

    def add(self, keys_t):
        for key in keys_t:
            for i in range(self.replicas):
                hash = self.hash_func(bytes(f"{i}{key}".encode()))
                self.keys.append(hash)
                self.hash_map[hash] = key
        sorted(self.keys)

    def search(self, n, f):
        i, j = 0, n
        while i < j:
            h = abs(i + j) >> 1
            if not f(h):
                i = h + 1
            else:
                j = h
        return i

    def get(self, key):
        if len(self.keys) == 0:
            return ""
        hash = self.hash_func(bytes(key.encode()))
        idx = self.search(len(self.keys), lambda i: self.keys[i] >= hash)

        return self.hash_map[self.keys[idx % len(self.keys)]]


if __name__ == '__main__':
    map = Map(replicas=2)
    map.add(["233", "666"])
    for i in range(10):
        print(map.get(str(i)))
    print("_____________________________________")
    map.add(["well", "888"])
    for i in range(10):
        print(map.get(str(i)))
    print(binascii.crc32("fwsrqwerwerqwrwrwre".encode())%1000)
