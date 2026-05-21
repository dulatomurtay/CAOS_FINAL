# Log-Structured File System via FUSE

Our project is a custom file system written in Python.
It works like a real file system: you can create files,
folders, read and delete them. Runs on Linux / WSL2.

## What is LFS?

A regular file system (ext4, NTFS) overwrites data in place:
- File was in block 5 → changed it → block 5 is overwritten

LFS (Log-Structured File System) works differently:
- File was in block 5 → changed it → new data written to block 6
- Block 5 becomes dead garbage
- Disk fills up like a diary — only forward, nothing is erased

This makes writes fast and simplifies crash recovery.

## How the disk is organized

The file lfs.img is our virtual disk (256 MB).
Inside it is divided into 4 MB segments:

```
lfs.img (256 MB)
├── Segment 0 — checkpoint (map of all files)
├── Segment 1 — data is written here first
├── Segment 2 — then here
├── Segment 3 — then here
└── ... (64 segments total)
```

Each segment is divided into 4 KB blocks.
One segment contains 1024 blocks.

## Project structure

```
lfs_fuse/
├── lfs/
│   ├── disk.py        — reads and writes blocks in lfs.img
│   ├── inode_map.py   — table: file number → where it is on disk
│   ├── checkpoint.py  — saves state on shutdown / crash recovery
│   ├── cleaner.py     — removes dead blocks (garbage collector)
│   └── fs.py          — all operations: read, write, mkdir, rm, mv
├── main.py            — starts the file system
├── mkfs.py            — creates empty disk lfs.img
├── test_lfs.sh        — automated tests
├── Makefile           — convenient commands
├── README.md          — this instruction
└── AI_USAGE.md        — description of AI tool usage
```

## Requirements

- Ubuntu or WSL2 on Windows
- Python 3
- fusepy

## Installation

### Step 1 — Install WSL2 (Windows only)

Open PowerShell as administrator:
```bash
wsl --install
```
Restart your computer. Ubuntu will open — create a username and password.

### Step 2 — Install dependencies

In Ubuntu terminal:
```bash
sudo apt install -y python3 python3-pip fuse libfuse-dev git
pip3 install fusepy --break-system-packages
```

### Step 3 — Clone the project

```bash
git clone https://github.com/dulatomurtay/CAOS_FINAL.git
cd CAOS_FINAL
```

## Run

### Start with one command:
```bash
make run
```

What happens inside:
1. Creates lfs.img (virtual disk 256 MB)
2. Creates folder /tmp/lfs_mount
3. Our FS is mounted to that folder

The terminal will be busy — that is normal. Open a second terminal.

### Work with the file system (second terminal):

```bash
# Create a file
echo "hello LFS" > /tmp/lfs_mount/test.txt

# Read a file
cat /tmp/lfs_mount/test.txt

# Create a folder
mkdir /tmp/lfs_mount/mydir

# List contents
ls /tmp/lfs_mount

# Delete a file
rm /tmp/lfs_mount/test.txt

# Rename a file
mv /tmp/lfs_mount/old.txt /tmp/lfs_mount/new.txt
```

### Stop the file system:
```bash
make umount
```

## Tests

```bash
make test
```

Runs 5 automated tests:
- Test 1 — write and read a file
- Test 2 — create directories
- Test 3 — create multiple files
- Test 4 — delete a file
- Test 5 — rename a file

Expected result:
```
=== All tests passed! ===
```

## Commands

| Command | Description |
|---|---|
| `make run` | Start the file system |
| `make umount` | Stop the file system |
| `make test` | Run all tests |
| `make clean` | Delete lfs.img and start fresh |

## How file writing works

When you type `echo "hello" > /tmp/lfs_mount/test.txt`:

1. Linux calls our program `fs.py`
2. `fs.py` creates an inode — a file card with metadata
3. `SegWriter` writes "hello" to the next free block
4. `inode_map` remembers where this file is located
5. `checkpoint` saves the entire state to disk

When you read `cat /tmp/lfs_mount/test.txt`:

1. `fs.py` receives a read command
2. Looks in `inode_map` — where is test.txt?
3. Reads the required block from disk
4. Returns the content: "hello"

## Team

- Dulat
- Yerlan
- Meirzhan
- Denis

## AI Tools Used

See AI_USAGE.md
```
