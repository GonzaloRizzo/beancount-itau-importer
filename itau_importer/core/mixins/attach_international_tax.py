from typing import List

from ..natural_transaction import NaturalTransaction, Detail
from beancount.core.data import D, Amount

INTERNATIONAL_TAX = D('0.03') * D('1.22')  # 3% plus VAT 22%


class AttachInternationalTaxMixin:
    international_tax_account = 'Expenses:Taxes:Itau'

    def pre_parse(
            self,
            natural_transactions: List[NaturalTransaction],
            existing_entries: List[any],
    ):
        natural_transactions = super().pre_parse(natural_transactions,
                                                 existing_entries)
        for natural_transaction in natural_transactions:
            is_international = natural_transaction.meta.get(
                '_is_international', False)

            if is_international:
                taxed_amount = (natural_transaction.debited_amount.number *
                                INTERNATIONAL_TAX).quantize(D('0.00'))
                natural_transaction.details.append(
                    Detail(
                        Amount(
                            taxed_amount,
                            natural_transaction.debited_amount.currency,
                        ),
                        account=self.international_tax_account,
                        extra=True,
                    ))
        return natural_transactions
