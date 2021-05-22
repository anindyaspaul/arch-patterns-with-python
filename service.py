from typing import List
from model import Batch, OrderLine, OutOfStock


def allocate(line: OrderLine, batches: List[Batch]):
    try:
        batch = next(
            batch for batch in sorted(batches) if batch.can_allocate(line)
        )
    except StopIteration:
        raise OutOfStock(f"Out of stock for sku {line.sku}")
    batch.allocate(line)
    return batch.reference

