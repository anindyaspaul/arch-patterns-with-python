from datetime import date, timedelta
import pytest

from model import OrderLine, Batch, OutOfStock
from service import allocate

today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)


def make_batch_and_line(sku, batch_qty, line_qty):
    return (
        Batch('batch-001', sku, batch_qty, today),
        OrderLine('order-001', sku, line_qty)
    )


def test_allocating_to_a_batch_reduces_the_available_quantity():
    batch, line = make_batch_and_line('SMALL-TABLE', 20, 2)
    batch.allocate(line)
    assert batch.available_quantity == 18


def test_can_allocate_if_available_greater_than_required():
    batch, line = make_batch_and_line('SMALL-TABLE', 20, 2)
    assert batch.can_allocate(line)


def test_cannot_allocate_if_available_smaller_than_required():
    batch, line = make_batch_and_line('SMALL-TABLE', 20, 21)
    assert batch.can_allocate(line) is False


def test_can_allocate_if_available_equal_to_required():
    batch, line = make_batch_and_line('SMALL-TABLE', 20, 20)
    assert batch.can_allocate(line)


def test_cannot_allocate_if_skus_do_not_match():
    batch = Batch('batch-001', 'SMALL-TABLE', 20, today)
    line = OrderLine('order-001', 'LARGE-TABLE', 2)
    assert batch.can_allocate(line) is False


def test_can_only_deallocate_allocated_lines():
    batch, line = make_batch_and_line('SMALL-TABLE', 20, 2)
    batch.deallocate(line)
    assert batch.available_quantity == 20


def test_allocation_is_idempotent():
    batch, line = make_batch_and_line('SMALL-TABLE', 20, 2)
    batch.allocate(line)
    batch.allocate(line)
    assert batch.available_quantity == 18
    

def test_prefers_warehouse_batches_to_shipments():
    in_stock = Batch('in-stock', 'SPOON', 100, eta=None)
    in_shipping = Batch('in-shipping', 'SPOON', 100, eta=tomorrow)
    line = OrderLine('order', 'SPOON', 10)
    allocate(line, [in_stock, in_shipping])
    assert in_stock.available_quantity == 90
    assert in_shipping.available_quantity == 100


def test_prefers_earlier_batches():
    earliest = Batch('earliest', 'SPOON', 100, eta=today)
    medium = Batch('medium', 'SPOON', 100, eta=tomorrow)
    latest = Batch('latest', 'SPOON', 100, eta=later)
    line = OrderLine('order', 'SPOON', 10)
    allocate(line, [medium, earliest, latest])
    assert earliest.available_quantity == 90
    assert medium.available_quantity == 100
    assert latest.available_quantity == 100


def test_allocation_returns_batch_ref():
    in_stock = Batch('in-stock', 'SPOON', 100, eta=None)
    in_shipping = Batch('in-shipping', 'SPOON', 100, eta=tomorrow)
    line = OrderLine('order', 'SPOON', 10)
    allocation = allocate(line, [in_stock, in_shipping])
    assert allocation == in_stock.reference

def test_raises_out_of_stock_exception_if_cannot_allocate():
    batch, line = make_batch_and_line('SMALL-TABLE', 20, 20)
    allocate(line, [batch])
    with pytest.raises(OutOfStock, match='SMALL-TABLE'):
        allocate(OrderLine('order2', 'SMALL-TABLE', 1), [batch])

