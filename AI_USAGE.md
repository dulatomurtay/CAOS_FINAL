# AI Usage

## Tool
Claude (claude.ai) — used throughout the entire project.

## What we used AI for
- Understanding LFS concepts (segments, inode map, checkpoint, cleaner)
- Generating project structure and all module code
- Debugging fusepy installation on WSL2
- Writing tests and documentation
- Preparing presentation slides

## Example prompts we used
- "Explain Log-Structured File System architecture"
- "Write disk.py for managing segments in LFS"
- "How does inode map work and how to save it to disk?"
- "Write FUSE operations: getattr, read, write, mkdir, create"
- "How to implement a cleaner / garbage collector for LFS?"
- "Help set up WSL2 on Windows for FUSE development"

## How AI helped solve problems
- WSL2 setup: AI explained step by step how to install and configure
- fusepy error: AI suggested --break-system-packages flag
- Makefile: AI wrote one-command startup script
- All Python modules were generated with AI assistance

## Important note
Every team member understands the code.
We can explain every function and every line at the defense.
AI was used as a development tool, not as a replacement for understanding.