import re
from typing import List

from beancount.core.data import Entries, D
from ..natural_transaction import NaturalTransaction, Detail

IVA_DISCOUNT_EXP = r'REDUC\. IVA LEY 17934'
TOLERANCE = 0.005


def remove_percentage(value, percentage):
    return D(value) / (1 + D(percentage) / 100)


def reapply_iva_points(value, iva=22, points=9, **kwargs):
    return (remove_percentage(value, iva)  # Removes current IVA
            * (D(points) / 100)  # Applies given IVA Points
            )


def circle_sort(lst, center):
    def sorter(i):
        return abs(lst.index(i) - lst.index(center))

    return sorter


def similar(a, b, tolerance=0):
    return abs(a - b) < tolerance


def get_possible_parents(discount_transaction: NaturalTransaction,
                         sibblings: List[NaturalTransaction]):
    close_transactions: List[NaturalTransaction] = sorted(
        sibblings, key=circle_sort(sibblings, discount_transaction))

    for transaction in close_transactions:
        expected_discount = reapply_iva_points(
            transaction.amount.number, points=9)
        if any(
                similar(
                    abs(discount_transaction.amount.number),
                    remove_percentage(expected_discount, discount),
                    tolerance=0.005) for discount in range(11)):
            yield transaction


class MergeIvaDiscountMixin:
    iva_discount_account = 'Income:RedIva'

    def pre_parse(
            self,
            natural_transactions: List[NaturalTransaction],
            existing_entries: Entries,
    ):
        natural_transactions = super().pre_parse(natural_transactions,
                                                 existing_entries)

        discount_txns = [
            t for t in natural_transactions
            if re.match(IVA_DISCOUNT_EXP, t.description or '')
        ]

        available_txns = natural_transactions.copy()

        for discount_txn in discount_txns:
            possible_parents = get_possible_parents(discount_txn,
                                                    available_txns)
            try:
                parent = next(possible_parents)
            except StopIteration:
                continue

            available_txns.remove(parent)
            natural_transactions.remove(discount_txn)

            detail = Detail(
                discount_txn.amount,
                account=self.iva_discount_account,
                extra=True,
            )

            if parent.date != discount_txn.date:
                detail.meta['date'] = discount_txn.date

            parent.details.append(detail)

        return natural_transactions
