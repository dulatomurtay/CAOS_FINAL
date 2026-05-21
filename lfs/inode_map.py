import json

class InodeMap:
    def __init__(self):
        self.table = {}
        self.next_ino = 1

    def alloc_ino(self):
        ino = self.next_ino
        self.next_ino += 1
        return ino

    def set(self, ino, seg, blk):
        self.table[ino] = (seg, blk)

    def get(self, ino):
        return self.table.get(ino)

    def delete(self, ino):
        self.table.pop(ino, None)

    def to_bytes(self):
        d = {
            'next_ino': self.next_ino,
            'table': {str(k): list(v) for k, v in self.table.items()}
        }
        return json.dumps(d).encode()

    def from_bytes(self, data):
        d = json.loads(data.rstrip(b'\x00').decode())
        self.next_ino = d['next_ino']
        self.table = {int(k): tuple(v) for k, v in d['table'].items()}