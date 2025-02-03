import json
from policy import Policy, Block, BlockType, ComparisonOperator  # Assuming your code is in `policy.py`
import os

POLICY_DIR = "./policies"
os.makedirs(POLICY_DIR, exist_ok=True)

# Create a policy
policy = Policy("ExamplePolicy")

# Create blocks
start_block = Block(BlockType.START)
cond_block = Block(BlockType.CONDITIONAL, ComparisonOperator.GREATER_EQUAL, "age", 18)
cond_block2 = Block(BlockType.CONDITIONAL, ComparisonOperator.GREATER, "salary", 10000)
end_block2 = Block(BlockType.END, output_value=1000)
end_block3 = Block(BlockType.END, output_value=0)
end_block = Block(BlockType.END, output_value=0)

# Link blocks
start_block.next_block = cond_block
cond_block.next_true = cond_block2
cond_block2.next_true = end_block2
cond_block2.next_false = end_block3
cond_block.next_false = end_block

# Add blocks to policy
policy.add_block(start_block)
policy.add_block(cond_block)
policy.add_block(cond_block2)
policy.add_block(end_block2)
policy.add_block(end_block3)
policy.add_block(end_block)



# Save policy
policy.save()

# Load policy from file
with open(f"{POLICY_DIR}/ExamplePolicy.json") as f:
    policy_data = json.load(f)

loaded_policy = Policy.from_dict(policy_data)

# Check if everything is correctly linked
assert loaded_policy.start_block.next_block == loaded_policy.blocks[1]  # Should be `cond_block`
