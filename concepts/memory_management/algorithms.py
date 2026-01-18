from typing import List, Dict, Any, Optional
import copy

class MemoryBlock:
    def __init__(self, start: int, size: int, process_id: str = None):
        self.start = start
        self.size = size
        self.process_id = process_id
        self.is_free = process_id is None

    def __repr__(self):
        return f"MemoryBlock(start={self.start}, size={self.size}, process='{self.process_id}', free={self.is_free})"

class PageTableEntry:
    def __init__(self, page_number: int, frame_number: int = None, valid: bool = False):
        self.page_number = page_number
        self.frame_number = frame_number
        self.valid = valid
        self.referenced = False
        self.modified = False

class SegmentTableEntry:
    def __init__(self, segment_number: int, base: int, limit: int):
        self.segment_number = segment_number
        self.base = base
        self.limit = limit

class MemoryManager:
    @staticmethod
    def first_fit(blocks: List[MemoryBlock], process_size: int, process_id: str) -> Optional[int]:
        """First Fit allocation strategy."""
        for i, block in enumerate(blocks):
            if block.is_free and block.size >= process_size:
                # Allocate
                allocated_size = process_size
                remaining_size = block.size - allocated_size

                # Update current block
                block.size = allocated_size
                block.process_id = process_id
                block.is_free = False

                # Create remaining free block if any
                if remaining_size > 0:
                    new_block = MemoryBlock(block.start + allocated_size, remaining_size)
                    blocks.insert(i + 1, new_block)

                return block.start
        return None

    @staticmethod
    def best_fit(blocks: List[MemoryBlock], process_size: int, process_id: str) -> Optional[int]:
        """Best Fit allocation strategy."""
        best_index = -1
        best_size = float('inf')

        for i, block in enumerate(blocks):
            if block.is_free and block.size >= process_size:
                if block.size < best_size:
                    best_size = block.size
                    best_index = i

        if best_index != -1:
            block = blocks[best_index]
            allocated_size = process_size
            remaining_size = block.size - allocated_size

            block.size = allocated_size
            block.process_id = process_id
            block.is_free = False

            if remaining_size > 0:
                new_block = MemoryBlock(block.start + allocated_size, remaining_size)
                blocks.insert(best_index + 1, new_block)

            return block.start
        return None

    @staticmethod
    def worst_fit(blocks: List[MemoryBlock], process_size: int, process_id: str) -> Optional[int]:
        """Worst Fit allocation strategy."""
        worst_index = -1
        worst_size = -1

        for i, block in enumerate(blocks):
            if block.is_free and block.size >= process_size:
                if block.size > worst_size:
                    worst_size = block.size
                    worst_index = i

        if worst_index != -1:
            block = blocks[worst_index]
            allocated_size = process_size
            remaining_size = block.size - allocated_size

            block.size = allocated_size
            block.process_id = process_id
            block.is_free = False

            if remaining_size > 0:
                new_block = MemoryBlock(block.start + allocated_size, remaining_size)
                blocks.insert(worst_index + 1, new_block)

            return block.start
        return None

    @staticmethod
    def deallocate_memory(blocks: List[MemoryBlock], process_id: str) -> bool:
        """Deallocate memory for a process and merge adjacent free blocks."""
        # Find and deallocate blocks for this process
        deallocated = False
        for block in blocks:
            if block.process_id == process_id:
                block.process_id = None
                block.is_free = True
                deallocated = True

        # Merge adjacent free blocks
        i = 0
        while i < len(blocks) - 1:
            if blocks[i].is_free and blocks[i + 1].is_free:
                blocks[i].size += blocks[i + 1].size
                blocks.pop(i + 1)
            else:
                i += 1

        return deallocated

class PageReplacement:
    @staticmethod
    def fifo(page_sequence: List[int], num_frames: int) -> Dict[str, Any]:
        """FIFO page replacement algorithm."""
        frames = []
        page_faults = 0
        page_table = {}
        history = []

        for page in page_sequence:
            step_info = {
                'page': page,
                'frames': frames.copy(),
                'fault': False,
                'replaced': None
            }

            if page not in frames:
                page_faults += 1
                step_info['fault'] = True

                if len(frames) < num_frames:
                    frames.append(page)
                else:
                    replaced = frames.pop(0)
                    frames.append(page)
                    step_info['replaced'] = replaced

            page_table[page] = frames.index(page) if page in frames else None
            history.append(step_info)

        return {
            'page_faults': page_faults,
            'total_pages': len(page_sequence),
            'fault_rate': page_faults / len(page_sequence),
            'history': history,
            'final_frames': frames
        }

    @staticmethod
    def lru(page_sequence: List[int], num_frames: int) -> Dict[str, Any]:
        """LRU page replacement algorithm."""
        frames = []
        page_faults = 0
        recent_use = {}  # page -> last used time
        time = 0
        history = []

        for page in page_sequence:
            time += 1
            step_info = {
                'page': page,
                'frames': frames.copy(),
                'fault': False,
                'replaced': None
            }

            if page in frames:
                recent_use[page] = time
            else:
                page_faults += 1
                step_info['fault'] = True

                if len(frames) < num_frames:
                    frames.append(page)
                    recent_use[page] = time
                else:
                    # Find least recently used
                    lru_page = min(frames, key=lambda p: recent_use[p])
                    idx = frames.index(lru_page)
                    frames[idx] = page
                    recent_use[page] = time
                    del recent_use[lru_page]
                    step_info['replaced'] = lru_page

            history.append(step_info)

        return {
            'page_faults': page_faults,
            'total_pages': len(page_sequence),
            'fault_rate': page_faults / len(page_sequence),
            'history': history,
            'final_frames': frames
        }

    @staticmethod
    def optimal(page_sequence: List[int], num_frames: int) -> Dict[str, Any]:
        """Optimal page replacement algorithm."""
        frames = []
        page_faults = 0
        history = []

        def find_optimal_victim(current_idx: int) -> int:
            """Find the page that will be used farthest in the future."""
            farthest = -1
            victim_idx = -1

            for i, page in enumerate(frames):
                try:
                    next_use = page_sequence.index(page, current_idx + 1)
                except ValueError:
                    next_use = float('inf')

                if next_use > farthest:
                    farthest = next_use
                    victim_idx = i

            return victim_idx

        for idx, page in enumerate(page_sequence):
            step_info = {
                'page': page,
                'frames': frames.copy(),
                'fault': False,
                'replaced': None
            }

            if page not in frames:
                page_faults += 1
                step_info['fault'] = True

                if len(frames) < num_frames:
                    frames.append(page)
                else:
                    victim_idx = find_optimal_victim(idx)
                    replaced = frames[victim_idx]
                    frames[victim_idx] = page
                    step_info['replaced'] = replaced

            history.append(step_info)

        return {
            'page_faults': page_faults,
            'total_pages': len(page_sequence),
            'fault_rate': page_faults / len(page_sequence),
            'history': history,
            'final_frames': frames
        }

class VirtualMemorySimulator:
    def __init__(self, num_frames: int, page_size: int = 4096):
        self.num_frames = num_frames
        self.page_size = page_size
        self.page_table = {}  # page_number -> PageTableEntry
        self.frames = [None] * num_frames  # frame_number -> page_number
        self.next_frame = 0

    def translate_address(self, virtual_address: int) -> Optional[int]:
        """Translate virtual address to physical address."""
        page_number = virtual_address // self.page_size
        offset = virtual_address % self.page_size

        if page_number not in self.page_table:
            return None  # Page fault

        entry = self.page_table[page_number]
        if not entry.valid:
            return None  # Invalid page

        frame_number = entry.frame_number
        physical_address = frame_number * self.page_size + offset
        return physical_address

    def allocate_page(self, page_number: int) -> bool:
        """Allocate a frame for a page (simplified - no replacement)."""
        if page_number in self.page_table and self.page_table[page_number].valid:
            return True  # Already allocated

        # Find free frame
        free_frame = None
        for i, frame in enumerate(self.frames):
            if frame is None:
                free_frame = i
                break

        if free_frame is None:
            return False  # No free frames

        # Allocate
        self.frames[free_frame] = page_number
        self.page_table[page_number] = PageTableEntry(page_number, free_frame, True)
        return True

class SegmentationSimulator:
    def __init__(self):
        self.segment_table = {}  # segment_number -> SegmentTableEntry

    def translate_address(self, segment_number: int, offset: int) -> Optional[int]:
        """Translate segment:offset to physical address."""
        if segment_number not in self.segment_table:
            return None  # Segment not found

        entry = self.segment_table[segment_number]
        if offset >= entry.limit:
            return None  # Offset out of bounds

        physical_address = entry.base + offset
        return physical_address

    def allocate_segment(self, segment_number: int, size: int, base_address: int) -> bool:
        """Allocate a segment."""
        if segment_number in self.segment_table:
            return False  # Segment already exists

        self.segment_table[segment_number] = SegmentTableEntry(segment_number, base_address, size)
        return True