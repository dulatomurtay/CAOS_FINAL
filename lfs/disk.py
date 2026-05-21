import os

SEGMENT_SIZE = 4 * 1024 * 1024
BLOCK_SIZE = 4096
BLOCKS_PER_SEGMENT = SEGMENT_SIZE // BLOCK_SIZE

class Disk:
    def __init__(self, path, num_segments=64):
        self.path = path
        self.num_segments = num_segments
        self.size = num_segments * SEGMENT_SIZE
        if not os.path.exists(path):
            with open(path, 'wb') as f:
                f.write(b'\x00' * self.size)
        self.f = open(path, 'r+b')

    def read_block(self, seg, blk):
        offset = seg * SEGMENT_SIZE + blk * BLOCK_SIZE
        self.f.seek(offset)
        return self.f.read(BLOCK_SIZE)

    def write_block(self, seg, blk, data):
        assert len(data) <= BLOCK_SIZE
        data = data.ljust(BLOCK_SIZE, b'\x00')
        offset = seg * SEGMENT_SIZE + blk * BLOCK_SIZE
        self.f.seek(offset)
        self.f.write(data)
        self.f.flush()

    def close(self):
        self.f.close()