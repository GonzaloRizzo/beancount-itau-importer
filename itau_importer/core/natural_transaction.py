from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from functools import reduce

from beancount.core.amount import (
    div as amount_div,
    add as amount_add,
    sub as amount_sub,
)

from beancount.core.data import Amount, Posting, Transaction
from beancount.core.flags import FLAG_OKAY
from beancount.core.number import D

from beancount.parser.printer import format_entry


def sum_postings(amounts, currency):
    return reduce(
        amount_add,
        [p.units for p in amounts],
        Amount(D(0), currency),
    )


@dataclass
class Detail:
    amount: Amount
    description: Optional[str] = None
    account: Optional[str] = None
    extra: bool = False

    def as_posting(self, default_account=None):
        return Posting(
            account=self.account or default_account,
            units=self.amount,
            cost=None,
            price=None,
            flag=None,
            meta={'desc': self.description} if self.description else None,
        )


@dataclass
class NaturalTransaction:
    date: datetime
    amount: Amount
    debited_account: str
    account: Optional[str] = 'Expenses:Unknown'
    description: Optional[str] = None
    payee: Optional[str] = None
    debited_amount: Optional[Amount] = None
    details: List[Detail] = field(default_factory=list)

    def __post_init__(self):
        if not self.debited_amount:
            self.debited_amount = self.amount

    def parse(self, meta: Optional[dict] = None) -> Transaction:

        detailed_postings = [
            d.as_posting(default_account=self.account) for d in self.details
            if not d.extra
        ]

        main = Posting(
            account=self.account,
            units=amount_sub(
                self.amount,
                sum_postings(detailed_postings, self.amount.currency)),
            cost=None,
            price=None,
            flag=None,
            meta=None,
        )

        debit = Posting(
            account=self.debited_account,
            units=(-self.debited_amount if
                   (self.debited_amount != self.amount
                    or len(self.details) > 0) else None),
            cost=None,
            price=(amount_div(self.amount, self.debited_amount.number)
                   if self.debited_amount.currency != self.amount.currency else
                   None),
            flag=None,
            meta=None,
        )

        extra_postings = [
            d.as_posting(default_account=self.account) for d in self.details
            if d.extra
        ]

        if len(extra_postings) > 0:
            extra_postings.append(
                Posting(
                    account=self.debited_account,
                    units=-sum_postings(extra_postings, self.amount.currency),
                    cost=None,
                    price=None,
                    flag=None,
                    meta=None,
                ))

        return Transaction(
            meta=meta or dict(),
            date=self.date,
            flag=FLAG_OKAY,
            tags=set(),
            links=set(),
            payee=self.payee,
            narration=self.description,
            postings=[
                p for p in [
                    *detailed_postings,
                    main if main.units.number != 0 else None,
                    debit,
                    *extra_postings,
                ] if p is not None
            ])

    def render(self):
        return format_entry(self.parse())
