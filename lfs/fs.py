import os, stat, time, errno, json
from fuse import FUSE, FuseOSError, Operations
from lfs.disk import Disk, BLOCK_SIZE
from lfs.inode_map import InodeMap
from lfs.checkpoint import Checkpoint

class SegWriter:
    def __init__(self):
        self.cur_seg = 1
        self.cur_blk = 0

    def append(self, disk, data):
        from lfs.disk import BLOCKS_PER_SEGMENT
        if self.cur_blk >= BLOCKS_PER_SEGMENT:
            self.cur_seg += 1
            self.cur_blk = 0
        seg, blk = self.cur_seg, self.cur_blk
        disk.write_block(seg, blk, data[:BLOCK_SIZE])
        self.cur_blk += 1
        return seg, blk

def _make_inode(mode, uid=1000, gid=1000, size=0):
    now = time.time()
    return {
        'mode': mode, 'uid': uid, 'gid': gid,
        'size': size, 'atime': now, 'mtime': now, 'ctime': now,
        'nlink': 1, 'blocks': [],
        'children': {}
    }

def _enc(obj):
    return json.dumps(obj).encode().ljust(BLOCK_SIZE, b'\x00')

def _dec(raw):
    return json.loads(raw.rstrip(b'\x00').decode())

class LFS(Operations):
    def __init__(self, disk_path):
        self.disk = Disk(disk_path)
        self.imap = InodeMap()
        self.sw = SegWriter()
        self.cp = Checkpoint()
        self._cache = {}
        if not self.cp.load(self.disk, self.imap, self.sw):
            self._mkfs()

    def _mkfs(self):
        root = _make_inode(stat.S_IFDIR | 0o755)
        root['nlink'] = 2
        self._write_inode(1, root)
        self.imap.next_ino = 2
        self.cp.save(self.disk, self.imap, self.sw)

    def _write_inode(self, ino, inode):
        self._cache[ino] = inode
        seg, blk = self.sw.append(self.disk, _enc(inode))
        self.imap.set(ino, seg, blk)

    def _read_inode(self, ino):
        if ino in self._cache:
            return self._cache[ino]
        loc = self.imap.get(ino)
        if loc is None:
            raise FuseOSError(errno.ENOENT)
        raw = self.disk.read_block(*loc)
        inode = _dec(raw)
        self._cache[ino] = inode
        return inode

    def _resolve(self, path):
        if path == '/':
            return 1
        parts = [p for p in path.split('/') if p]
        ino = 1
        for name in parts:
            inode = self._read_inode(ino)
            if name not in inode['children']:
                raise FuseOSError(errno.ENOENT)
            ino = inode['children'][name]
        return ino

    def getattr(self, path, fh=None):
        ino = self._resolve(path)
        inode = self._read_inode(ino)
        return {
            'st_mode': inode['mode'],
            'st_ino': ino,
            'st_nlink': inode['nlink'],
            'st_uid': inode['uid'],
            'st_gid': inode['gid'],
            'st_size': inode['size'],
            'st_atime': inode['atime'],
            'st_mtime': inode['mtime'],
            'st_ctime': inode['ctime'],
        }

    def readdir(self, path, fh):
        ino = self._resolve(path)
        inode = self._read_inode(ino)
        return ['.', '..'] + list(inode['children'].keys())

    def mkdir(self, path, mode):
        parent_path, name = os.path.split(path)
        p_ino = self._resolve(parent_path or '/')
        p_inode = self._read_inode(p_ino)
        ino = self.imap.alloc_ino()
        inode = _make_inode(stat.S_IFDIR | mode)
        inode['nlink'] = 2
        p_inode['children'][name] = ino
        self._write_inode(ino, inode)
        self._write_inode(p_ino, p_inode)
        self.cp.save(self.disk, self.imap, self.sw)

    def create(self, path, mode, fi=None):
        parent_path, name = os.path.split(path)
        p_ino = self._resolve(parent_path or '/')
        p_inode = self._read_inode(p_ino)
        ino = self.imap.alloc_ino()
        inode = _make_inode(stat.S_IFREG | mode)
        p_inode['children'][name] = ino
        self._write_inode(ino, inode)
        self._write_inode(p_ino, p_inode)
        self.cp.save(self.disk, self.imap, self.sw)
        return 0

    def write(self, path, data, offset, fh):
        ino = self._resolve(path)
        inode = self._read_inode(ino)
        content = b'\x00' * inode['size']
        content = content[:offset] + data + content[offset + len(data):]
        seg, blk = self.sw.append(self.disk, content[:BLOCK_SIZE])
        inode['blocks'] = [[seg, blk]]
        inode['size'] = len(content)
        inode['mtime'] = time.time()
        self._write_inode(ino, inode)
        self.cp.save(self.disk, self.imap, self.sw)
        return len(data)

    def read(self, path, size, offset, fh):
        ino = self._resolve(path)
        inode = self._read_inode(ino)
        if not inode['blocks']:
            return b''
        seg, blk = inode['blocks'][0]
        data = self.disk.read_block(seg, blk)
        return data[offset:offset + size]

    def unlink(self, path):
        parent_path, name = os.path.split(path)
        p_ino = self._resolve(parent_path or '/')
        p_inode = self._read_inode(p_ino)
        ino = p_inode['children'].pop(name)
        self.imap.delete(ino)
        self._cache.pop(ino, None)
        self._write_inode(p_ino, p_inode)
        self.cp.save(self.disk, self.imap, self.sw)

    def rmdir(self, path):
        self.unlink(path)

    def rename(self, old, new, flags=0):
        old_parent, old_name = os.path.split(old)
        new_parent, new_name = os.path.split(new)
        op_ino = self._resolve(old_parent or '/')
        op_inode = self._read_inode(op_ino)
        ino = op_inode['children'].pop(old_name)
        np_ino = self._resolve(new_parent or '/')
        np_inode = self._read_inode(np_ino)
        np_inode['children'][new_name] = ino
        self._write_inode(op_ino, op_inode)
        if op_ino != np_ino:
            self._write_inode(np_ino, np_inode)
        self.cp.save(self.disk, self.imap, self.sw)

    def truncate(self, path, length, fh=None):
        ino = self._resolve(path)
        inode = self._read_inode(ino)
        inode['size'] = length
        self._write_inode(ino, inode)
        self.cp.save(self.disk, self.imap, self.sw)

    def destroy(self, path):
        self.cp.save(self.disk, self.imap, self.sw)
        self.disk.close()