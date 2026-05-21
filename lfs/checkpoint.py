import struct
from lfs.disk import BLOCK_SIZE

CP_SEG = 0

class Checkpoint:
    def save(self, disk, inode_map, seg_writer):
        data = inode_map.to_bytes()
        meta = struct.pack('>II', seg_writer.cur_seg, seg_writer.cur_blk)
        disk.write_block(CP_SEG, 0, meta)
        disk.write_block(CP_SEG, 1, data)

    def load(self, disk, inode_map, seg_writer):
        meta = disk.read_block(CP_SEG, 0)
        if meta == b'\x00' * len(meta):
            return False
        cur_seg, cur_blk = struct.unpack('>II', meta[:8])
        data = disk.read_block(CP_SEG, 1)
        inode_map.from_bytes(data)
        seg_writer.cur_seg = cur_seg
        seg_writer.cur_blk = cur_blk
        return True