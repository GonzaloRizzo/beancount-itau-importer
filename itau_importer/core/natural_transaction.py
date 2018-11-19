from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from beancount.core.amount import div as amount_div
from beancount.core.data import Amount, Posting, Transaction
from beancount.core.flags import FLAG_OKAY

from beancount.parser.printer import format_entry


@dataclass
class NaturalTransaction:
    date: datetime
    amount: Amount
    debited_account: str
    account: Optional[str] = 'Expenses:Unknown'
    description: Optional[str] = None
    payee: Optional[str] = None
    debited_amount: Optional[Amount] = None

    def __post_init__(self):
        if not self.debited_amount:
            self.debited_amount = self.amount

    def parse(self, meta: Optional[dict] = None) -> Transaction:
        credit_posting = Posting(
            account=self.account,
            units=self.amount,
            cost=None,
            price=amount_div(self.debited_amount, self.amount.number)
            if self.debited_amount
            and self.debited_amount.currency != self.amount.currency else None,
            flag=None,
            meta=None,
        )

        debit_posting = Posting(
            account=self.debited_account,
            units=-self.debited_amount
            if self.debited_amount != self.amount else None,
            cost=None,
            price=None,
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
                credit_posting,
                debit_posting,
            ])

    def render(self):
        return format_entry(self.parse())
