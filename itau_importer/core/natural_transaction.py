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


@dataclass
class Detail:
    amount: Amount
    description: Optional[str] = None
    account: Optional[str] = None
    extra: bool = False


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

    def get_detailed_postings(self):
        return [
            Posting(
                account=d.account or self.account,
                units=d.amount,
                cost=None,
                price=None,
                flag=None,
                meta={'desc': d.description} if d.description else None,
            ) for d in self.details if not d.extra
        ]

    def parse(self, meta: Optional[dict] = None) -> Transaction:
        main_posting = Posting(
            account=self.account,
            units=self.amount,
            cost=None,
            price=None,
            flag=None,
            meta=None,
        )

        detailed_postings = self.get_detailed_postings()
        detailed_amount = reduce(amount_add,
                                 [p.units for p in detailed_postings],
                                 Amount(D(0), self.amount.currency))

        main_posting = main_posting._replace(
            units=amount_sub(main_posting.units, detailed_amount))

        debit_price = (amount_div(self.amount, self.debited_amount.number)
                       if self.debited_amount
                       and self.debited_amount.currency != self.amount.currency
                       else None)

        debit_posting = Posting(
            account=self.debited_account,
            units=(-self.debited_amount if
                   (self.debited_amount != self.amount
                    or len(detailed_postings) > 0) else None),
            cost=None,
            price=debit_price,
            flag=None,
            meta=None,
        )

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
                    main_posting if main_posting.units.number != 0 else None,
                    debit_posting,
                ] if p is not None
            ])

    def render(self):
        return format_entry(self.parse())
