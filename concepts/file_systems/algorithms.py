from typing import List, Dict, Any, Optional
import copy

class File:
    def __init__(self, name: str, size: int, content: str = ""):
        self.name = name
        self.size = size
        self.content = content
        self.blocks: List[int] = []  # Block indices allocated to this file

class Directory:
    def __init__(self, name: str, parent: Optional['Directory'] = None):
        self.name = name
        self.parent = parent
        self.files: List[File] = []
        self.subdirectories: List['Directory'] = []

    def add_file(self, file: File):
        self.files.append(file)

    def add_subdirectory(self, directory: 'Directory'):
        self.subdirectories.append(directory)

    def get_path(self) -> str:
        if self.parent is None:
            return "/"
        path = self.parent.get_path()
        return path + self.name + "/" if path != "/" else "/" + self.name + "/"

class DiskBlock:
    def __init__(self, index: int):
        self.index = index
        self.allocated = False
        self.file: Optional[File] = None
        self.next_block: Optional[int] = None  # For linked allocation

class FileSystem:
    def __init__(self, total_blocks: int = 100, block_size: int = 1024):
        self.total_blocks = total_blocks
        self.block_size = block_size
        self.disk: List[DiskBlock] = [DiskBlock(i) for i in range(total_blocks)]
        self.root = Directory("")
        self.allocation_method = "contiguous"  # contiguous, linked, indexed

    def allocate_contiguous(self, file: File) -> bool:
        """Contiguous allocation: find consecutive free blocks."""
        required_blocks = (file.size + self.block_size - 1) // self.block_size
        start_block = -1
        consecutive = 0

        for i, block in enumerate(self.disk):
            if not block.allocated:
                if start_block == -1:
                    start_block = i
                consecutive += 1
                if consecutive == required_blocks:
                    # Allocate blocks
                    for j in range(start_block, start_block + required_blocks):
                        self.disk[j].allocated = True
                        self.disk[j].file = file
                        file.blocks.append(j)
                    return True
            else:
                start_block = -1
                consecutive = 0

        return False  # No contiguous space found

    def allocate_linked(self, file: File) -> bool:
        """Linked allocation: allocate any free blocks and link them."""
        required_blocks = (file.size + self.block_size - 1) // self.block_size
        allocated = 0
        prev_block = -1

        for block in self.disk:
            if not block.allocated:
                block.allocated = True
                block.file = file
                file.blocks.append(block.index)
                if prev_block != -1:
                    self.disk[prev_block].next_block = block.index
                prev_block = block.index
                allocated += 1
                if allocated == required_blocks:
                    return True

        # If we allocated some but not all, deallocate them
        for block_idx in file.blocks:
            self.disk[block_idx].allocated = False
            self.disk[block_idx].file = None
            self.disk[block_idx].next_block = None
        file.blocks.clear()
        return False

    def allocate_indexed(self, file: File) -> bool:
        """Indexed allocation: use first block as index."""
        required_blocks = (file.size + self.block_size - 1) // self.block_size
        if required_blocks > self.total_blocks - 1:  # Need space for index block too
            return False

        # Find index block
        index_block = None
        data_blocks = []

        for block in self.disk:
            if not block.allocated:
                if index_block is None:
                    index_block = block
                else:
                    data_blocks.append(block)
                    if len(data_blocks) == required_blocks:
                        break

        if len(data_blocks) < required_blocks:
            return False

        # Allocate
        index_block.allocated = True
        index_block.file = file
        file.blocks.append(index_block.index)

        for i, block in enumerate(data_blocks):
            block.allocated = True
            block.file = file
            file.blocks.append(block.index)
            # Store data block index in index block (simplified)
            index_block.next_block = block.index if i == 0 else index_block.next_block

        return True

    def create_file(self, path: str, name: str, size: int) -> bool:
        """Create a file in the specified directory."""
        directory = self.navigate_to_directory(path)
        if directory is None:
            return False

        # Check if file already exists
        if any(f.name == name for f in directory.files):
            return False

        file = File(name, size)
        if self.allocation_method == "contiguous":
            success = self.allocate_contiguous(file)
        elif self.allocation_method == "linked":
            success = self.allocate_linked(file)
        elif self.allocation_method == "indexed":
            success = self.allocate_indexed(file)
        else:
            return False

        if success:
            directory.add_file(file)
            return True
        return False

    def delete_file(self, path: str, name: str) -> bool:
        """Delete a file and deallocate its blocks."""
        directory = self.navigate_to_directory(path)
        if directory is None:
            return False

        file = next((f for f in directory.files if f.name == name), None)
        if file is None:
            return False

        # Deallocate blocks
        for block_idx in file.blocks:
            self.disk[block_idx].allocated = False
            self.disk[block_idx].file = None
            self.disk[block_idx].next_block = None

        directory.files.remove(file)
        return True

    def navigate_to_directory(self, path: str) -> Optional[Directory]:
        """Navigate to directory by path."""
        if path == "/" or path == "":
            return self.root

        parts = [p for p in path.split("/") if p]
        current = self.root

        for part in parts:
            found = False
            for subdir in current.subdirectories:
                if subdir.name == part:
                    current = subdir
                    found = True
                    break
            if not found:
                return None
        return current

    def create_directory(self, path: str, name: str) -> bool:
        """Create a subdirectory."""
        directory = self.navigate_to_directory(path)
        if directory is None:
            return False

        if any(d.name == name for d in directory.subdirectories):
            return False

        new_dir = Directory(name, directory)
        directory.add_subdirectory(new_dir)
        return True

    def get_disk_usage(self) -> Dict[str, Any]:
        """Get disk usage statistics."""
        allocated_blocks = sum(1 for b in self.disk if b.allocated)
        free_blocks = self.total_blocks - allocated_blocks
        return {
            'total_blocks': self.total_blocks,
            'allocated_blocks': allocated_blocks,
            'free_blocks': free_blocks,
            'usage_percentage': (allocated_blocks / self.total_blocks) * 100
        }

class FATFileSystem(FileSystem):
    """Simplified FAT file system simulation."""
    def __init__(self, total_blocks: int = 100):
        super().__init__(total_blocks)
        self.fat = [-1] * total_blocks  # FAT table: -1 = free, -2 = end of chain

    def allocate_linked(self, file: File) -> bool:
        """FAT-style linked allocation."""
        required_blocks = (file.size + self.block_size - 1) // self.block_size
        allocated = 0
        prev_block = -1

        for i, block in enumerate(self.disk):
            if self.fat[i] == -1:  # Free block
                if prev_block != -1:
                    self.fat[prev_block] = i  # Link previous to current
                else:
                    file.blocks.append(i)  # First block
                prev_block = i
                self.fat[i] = -2  # Mark as end (will be updated if more blocks)
                block.allocated = True
                block.file = file
                allocated += 1
                if allocated == required_blocks:
                    break

        if allocated == required_blocks:
            file.blocks.extend(range(file.blocks[0] + 1, file.blocks[0] + allocated))
            return True
        else:
            # Deallocate
            for block_idx in file.blocks:
                self.fat[block_idx] = -1
                self.disk[block_idx].allocated = False
                self.disk[block_idx].file = None
            file.blocks.clear()
            return False

class NTFSFileSystem(FileSystem):
    """Simplified NTFS simulation with MFT."""
    def __init__(self, total_blocks: int = 100):
        super().__init__(total_blocks)
        self.mft_entries = {}  # Simplified MFT

class Ext4FileSystem(FileSystem):
    """Simplified ext4 simulation with inodes."""
    def __init__(self, total_blocks: int = 100):
        super().__init__(total_blocks)
        self.inodes = {}  # Simplified inode table