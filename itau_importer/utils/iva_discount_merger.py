from beancount.core.convert import get_weight

from beancount.core import flags
from beancount.core.data import Posting

IVA_DISCOUNT_TOKEN = 'REDUC. IVA LEY 17934'
TOLERANCE = 0.005


def remove_percentage(value, percentage):
    return value / (1 + percentage / 100)


def get_reduced_iva(value, iva=22, points=9, **kwargs):
    return (remove_percentage(value, iva)  # Removes current IVA
            * (points / 100)  # Applies given IVA Points
            )


def similar(a, b, tolerance):
    return abs(a - b) < tolerance


def get_txn_main_value(txn):
    value = next(get_weight(p).number for p in txn.postings if p.units)
    return abs(float(value))


def get_possible_parents(rediva_transaction, sibbling_transactions):
    iva_discount = get_txn_main_value(rediva_transaction)
    close_transactions = sorted(
        sibbling_transactions,
        key=circle_sort(sibbling_transactions, rediva_transaction))

    for transaction in close_transactions:
        transaction_value = get_txn_main_value(transaction)
        expected_iva_discount = get_reduced_iva(transaction_value, points=9)

        if any(
                similar(
                    remove_percentage(expected_iva_discount, extra_discount),
                    iva_discount, TOLERANCE) for extra_discount in range(11)):
            yield transaction


def circle_sort(lst, center):
    def sorter(i):
        return abs(lst.index(i) - lst.index(center))

    return sorter


def merge_iva_discounts(transactions):
    iva_discount_txns = [
        t for t in transactions if t.narration == IVA_DISCOUNT_TOKEN
    ]

    non_merged_txns = transactions.copy()

    for iva_discount_txn in iva_discount_txns:
        possible_parents = get_possible_parents(iva_discount_txn,
                                                non_merged_txns)
        try:
            parent = next(possible_parents)
        except StopIteration:
            continue

        non_merged_txns.remove(parent)
        transactions.remove(iva_discount_txn)

        iva_discount_meta = {}

        if parent.date != iva_discount_txn.date:
            iva_discount_meta['date'] = iva_discount_txn.date

        discount_amount = iva_discount_txn.postings[0].units
        parent.postings.insert(
            -1,
            Posting('Income:Rediva', -discount_amount, None, None,
                    flags.FLAG_WARNING, iva_discount_meta),
        )
