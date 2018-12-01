from typing import List

from beancount.core.data import Entries
from beancount.core.getters import get_all_payees

from ..natural_transaction import NaturalTransaction

MIN_INFERABLE_LENGTH = 4


def normalize(s):
    return s.replace(' ', '').lower()


def infer_payee(payees, natural_transaction: NaturalTransaction):
    posible_payees = sorted(
        [
            p for p in payees if len(p) >= MIN_INFERABLE_LENGTH
            and normalize(p) in normalize(natural_transaction.description)
        ],
        key=len,
        reverse=True,
    )
    return next(iter(posible_payees), None)


class InferPayeeMixin:
    def pre_parse(
            self,
            natural_transactions: List[NaturalTransaction],
            existing_entries: Entries,
    ):
        natural_transactions = super().pre_parse(natural_transactions,
                                                 existing_entries)
        if not existing_entries:
            return

        payees = get_all_payees(existing_entries or [])

        for natural_transaction in natural_transactions:
            if natural_transaction.payee:
                continue

            infered_payee = infer_payee(payees, natural_transaction)
            if infered_payee:
                natural_transaction.payee = infered_payee
                natural_transaction.description = ''
        return natural_transactions
