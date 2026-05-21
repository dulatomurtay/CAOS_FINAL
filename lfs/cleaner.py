from lfs.disk import BLOCKS_PER_SEGMENT

class Cleaner:
    def __init__(self, disk, inode_map, seg_writer, checkpoint):
        self.disk = disk
        self.inode_map = inode_map
        self.seg_writer = seg_writer
        self.checkpoint = checkpoint

    def _live_blocks(self, seg):
        live = set()
        live_map = {}
        for ino, (s, b) in self.inode_map.table.items():
            if s == seg:
                live.add(b)
                live_map[b] = ino
        return live, live_map

    def clean(self, seg):
        live, live_map = self._live_blocks(seg)
        if not live:
            return
        for blk in sorted(live):
            data = self.disk.read_block(seg, blk)
            ns, nb = self.seg_writer.append(self.disk, data)
            ino = live_map[blk]
            self.inode_map.set(ino, ns, nb)
        self.checkpoint.save(self.disk, self.inode_map, self.seg_writer)

    def utilization(self, seg):
        live, _ = self._live_blocks(seg)
        return len(live) / BLOCKS_PER_SEGMENT