"""
ChainForgeLedger Difficulty Adjustment Algorithm

Implements difficulty adjustment based on block time targets.
"""

from typing import List
from chainforgeledger.core.block import Block


class DifficultyAdjuster:
    """
    Implements difficulty adjustment based on block time targets.
    
    Attributes:
        target_block_time: Target time per block in seconds
        adjustment_interval: Number of blocks between adjustments
        min_difficulty: Minimum allowed difficulty
        max_difficulty: Maximum allowed difficulty
        difficulty_change_limit: Maximum percentage change per adjustment
    """
    
    def __init__(self, target_block_time: int = 60, adjustment_interval: int = 10,
                 min_difficulty: int = 1, max_difficulty: int = 20,
                 difficulty_change_limit: float = 0.2):
        """
        Initialize a DifficultyAdjuster instance.
        
        Args:
            target_block_time: Target time per block in seconds
            adjustment_interval: Number of blocks between adjustments
            min_difficulty: Minimum allowed difficulty
            max_difficulty: Maximum allowed difficulty
            difficulty_change_limit: Maximum percentage change per adjustment (0.2 = 20%)
        """
        self.target_block_time = target_block_time
        self.adjustment_interval = adjustment_interval
        self.min_difficulty = min_difficulty
        self.max_difficulty = max_difficulty
        self.difficulty_change_limit = difficulty_change_limit
    
    def calculate_new_difficulty(self, blocks: List[Block], current_difficulty: int) -> int:
        """
        Calculate new difficulty based on recent block times.
        
        Args:
            blocks: List of recent blocks to analyze
            current_difficulty: Current blockchain difficulty
            
        Returns:
            New calculated difficulty
        """
        if len(blocks) < self.adjustment_interval:
            return current_difficulty
            
        # Get the relevant blocks for adjustment
        adjustment_blocks = blocks[-self.adjustment_interval:]
        
        # Calculate actual time taken for these blocks
        actual_time = adjustment_blocks[-1].timestamp - adjustment_blocks[0].timestamp
        
        # Calculate expected time
        expected_time = self.target_block_time * self.adjustment_interval
        
        # Calculate time difference ratio
        time_ratio = actual_time / expected_time
        
        # Adjust difficulty based on time ratio
        new_difficulty = current_difficulty / time_ratio
        
        # Apply difficulty change limit
        max_increase = current_difficulty * (1 + self.difficulty_change_limit)
        max_decrease = current_difficulty * (1 - self.difficulty_change_limit)
        new_difficulty = max(min(new_difficulty, max_increase), max_decrease)
        
        # Clamp to min/max difficulty
        new_difficulty = max(min(new_difficulty, self.max_difficulty), self.min_difficulty)
        
        # Round to integer
        return int(round(new_difficulty))
    
    def should_adjust_difficulty(self, block_index: int) -> bool:
        """
        Check if difficulty should be adjusted for the next block.
        
        Args:
            block_index: Current block index
            
        Returns:
            True if difficulty should be adjusted
        """
        return (block_index + 1) % self.adjustment_interval == 0
    
    def get_adjustment_info(self, blocks: List[Block], current_difficulty: int) -> dict:
        """
        Get detailed adjustment information.
        
        Args:
            blocks: List of recent blocks to analyze
            current_difficulty: Current blockchain difficulty
            
        Returns:
            Dictionary with adjustment details
        """
        if len(blocks) < self.adjustment_interval:
            return {
                'needs_adjustment': False,
                'blocks_remaining': self.adjustment_interval - len(blocks)
            }
            
        adjustment_blocks = blocks[-self.adjustment_interval:]
        actual_time = adjustment_blocks[-1].timestamp - adjustment_blocks[0].timestamp
        expected_time = self.target_block_time * self.adjustment_interval
        time_ratio = actual_time / expected_time
        
        new_difficulty = self.calculate_new_difficulty(blocks, current_difficulty)
        
        return {
            'needs_adjustment': True,
            'actual_time': actual_time,
            'expected_time': expected_time,
            'time_ratio': time_ratio,
            'current_difficulty': current_difficulty,
            'new_difficulty': new_difficulty,
            'difficulty_change': ((new_difficulty - current_difficulty) / current_difficulty) * 100
        }
    
    def validate_difficulty(self, block: Block, previous_block: Block) -> bool:
        """
        Validate that block difficulty is appropriate.
        
        Args:
            block: Block to validate
            previous_block: Previous block
            
        Returns:
            True if difficulty is valid
        """
        if self.should_adjust_difficulty(previous_block.index):
            # Check if difficulty was adjusted
            expected_difficulty = self.calculate_new_difficulty(
                previous_block.index + 1, previous_block.difficulty
            )
            return abs(block.difficulty - expected_difficulty) <= 1
        else:
            # Difficulty should not change
            return block.difficulty == previous_block.difficulty
    
    def set_target_block_time(self, target: int):
        """
        Set target block time.
        
        Args:
            target: Target block time in seconds
            
        Raises:
            ValueError: If target is invalid
        """
        if target <= 0:
            raise ValueError("Target block time must be positive")
            
        self.target_block_time = target
    
    def set_adjustment_interval(self, interval: int):
        """
        Set adjustment interval.
        
        Args:
            interval: Number of blocks between adjustments
            
        Raises:
            ValueError: If interval is invalid
        """
        if interval <= 0:
            raise ValueError("Adjustment interval must be positive")
            
        self.adjustment_interval = interval
    
    def set_difficulty_limits(self, min_diff: int, max_diff: int):
        """
        Set difficulty limits.
        
        Args:
            min_diff: Minimum difficulty
            max_diff: Maximum difficulty
            
        Raises:
            ValueError: If limits are invalid
        """
        if min_diff < 1 or max_diff < min_diff:
            raise ValueError("Invalid difficulty limits")
            
        self.min_difficulty = min_diff
        self.max_difficulty = max_diff
    
    def set_difficulty_change_limit(self, limit: float):
        """
        Set maximum difficulty change limit.
        
        Args:
            limit: Maximum percentage change per adjustment (0.0 to 1.0)
            
        Raises:
            ValueError: If limit is invalid
        """
        if limit < 0 or limit > 1:
            raise ValueError("Difficulty change limit must be between 0 and 1")
            
        self.difficulty_change_limit = limit
    
    def get_statistics(self, blocks: List[Block]) -> dict:
        """
        Get difficulty statistics.
        
        Args:
            blocks: List of blocks to analyze
            
        Returns:
            Statistics dictionary
        """
        if len(blocks) < 2:
            return {}
            
        difficulties = [block.difficulty for block in blocks]
        block_times = []
        
        for i in range(1, len(blocks)):
            block_times.append(blocks[i].timestamp - blocks[i-1].timestamp)
            
        return {
            'average_difficulty': sum(difficulties) / len(difficulties),
            'min_difficulty': min(difficulties),
            'max_difficulty': max(difficulties),
            'average_block_time': sum(block_times) / len(block_times),
            'min_block_time': min(block_times),
            'max_block_time': max(block_times),
            'difficulty_changes': sum(1 for i in range(1, len(blocks)) 
                                     if blocks[i].difficulty != blocks[i-1].difficulty)
        }
    
    def __repr__(self):
        """String representation of the DifficultyAdjuster."""
        return (f"DifficultyAdjuster(target={self.target_block_time}s, "
                f"interval={self.adjustment_interval} blocks, "
                f"range={self.min_difficulty}-{self.max_difficulty})")
    
    def __str__(self):
        """String representation for printing."""
        return (
            f"Difficulty Adjuster\n"
            f"===================\n"
            f"Target Block Time: {self.target_block_time} seconds\n"
            f"Adjustment Interval: {self.adjustment_interval} blocks\n"
            f"Difficulty Range: {self.min_difficulty} - {self.max_difficulty}\n"
            f"Max Change Per Adjustment: {self.difficulty_change_limit * 100}%"
        )
