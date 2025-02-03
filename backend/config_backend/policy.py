import uuid
import json
import os
from typing import List, Optional, Dict
from enum import Enum;

POLICY_DIR = "./policies"
os.makedirs(POLICY_DIR, exist_ok=True)

class BlockType(Enum):
    START = "start"
    CONDITIONAL = "conditional"
    END = "end" 

class ComparisonOperator(Enum):
    GREATER = '>'
    GREATER_EQUAL = '>='
    LESS = '<'
    LESS_EQUAL = '<='
    EQUAL = '='

class Block:
    def __init__(self,
               type: BlockType,
               operator=None,
               target_variable=None,
               value=None,
               output_value=None,
               ):
        self.id = uuid.uuid4();
        self.type = type
        self.next_block = None  # Used for start block
        # Conditional block uses
        self.next_true = None
        self.next_false = None

        if self.type == BlockType.CONDITIONAL:
            if operator is None or target_variable is None or value is None:
                raise ValueError("Conditional block must contain operator, target_variable and value fields")
            self.operator = operator
            self.target_variable = target_variable
            self.value = value
        elif self.type == BlockType.END:
            if output_value is None:
                raise ValueError("End block must return a value")
            self.output_value = output_value

    def to_dict(self):
        """Parse into dictionary format"""
        return {
            "id": str(self.id),  # Convert UUID to string
            "type": self.type.value,  # Convert Enum to string
            "operator": self.operator.value if self.type == BlockType.CONDITIONAL else None,
            "target_variable": self.target_variable if self.type == BlockType.CONDITIONAL else None,
            "value": self.value if self.type == BlockType.CONDITIONAL else None,
            "output_value": self.output_value if self.type == BlockType.END else None,
            "next_block": str(self.next_block.id) if self.next_block else None,
            "next_true": str(self.next_true.id) if self.next_true else None,
            "next_false": str(self.next_false.id) if self.next_false else None,
        }


    @staticmethod
    def from_dict(data):
        """Create a `Block` from a dictionary"""
        block = Block(
            type=BlockType(data["type"]),
            operator=ComparisonOperator(data["operator"]) if data["operator"] else None,
            target_variable=data.get("target_variable"),
            value=data.get("value"),
            output_value=data.get("output_value"),
        )
        block.id = uuid.UUID(data["id"])  # Convert back to UUID
        block.next_block = data["next_block"]  # Store as ID for later linking
        block.next_true = data["next_true"]
        block.next_false = data["next_false"]
        return block



class Policy:
    def __init__(self, name: str):
        self.name = name
        self.blocks: List[Block] = []
        self.start_block: Optional[Block] = None

    def add_block(self, block: Block):
        """Adds a block to the policy, ensuring only one start block exists."""
        if block.type == BlockType.START:
            if self.start_block:
                raise ValueError("There can only be one start block.")
            self.start_block = block
        self.blocks.append(block)
    
    def to_dict(self):
        """Converts a `Policy` into dictionary format."""
        return {
            "name": self.name,
            "blocks": [block.to_dict() for block in self.blocks]
        }

    @staticmethod
    def from_dict(data):
        """Load a `Policy` from a dictionary"""
        policy = Policy(data["name"])
        blocks = [Block.from_dict(block) for block in data["blocks"]]
        
        # Create a lookup table for ID resolution
        block_lookup = {str(block.id): block for block in blocks}

        # Resolve references
        for block in blocks:
            if block.next_block:
                block.next_block = block_lookup.get(block.next_block)
            if block.next_true:
                block.next_true = block_lookup.get(block.next_true)
            if block.next_false:
                block.next_false = block_lookup.get(block.next_false)

        policy.blocks = blocks
        policy.start_block = next((b for b in blocks if b.type == BlockType.START), None)
        return policy

    
    def save(self):
        """Save a `Policy` as a JSON file"""
        with open(f"{POLICY_DIR}/{self.name}.json", "w") as f:
            json.dump(self.to_dict(), f, indent=4)

    def validate_policy(self):
        if not self.start_block:
            raise ValueError("Policy must contain a start block")
        
        for block in self.blocks:
            if block.type == BlockType.END:
                if block.next_block or block.next_true or block.next_false:
                    raise ValueError("End blocks cannot have any outgoing block links")
            elif block.type == BlockType.CONDITIONAL:
                if not block.next_true or not block.next_false:
                    raise ValueError("Conditional blocks must have both true and false paths")
