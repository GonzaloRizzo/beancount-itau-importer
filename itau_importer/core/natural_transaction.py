from dataclasses import dataclass
from datetime import datetime

from beancount.core.amount import div as amount_div
from beancount.core.data import Amount, Posting, Transaction
from beancount.core.flags import FLAG_OKAY, FLAG_WARNING


@dataclass
class NaturalTransaction:
    date: datetime
    description: str
    payee: str
    amount: Amount
    account: str
    debited_amount: Amount
    debited_account: str

    def parse(self, meta: dict) -> Transaction:
        credit_posting = Posting(
            account=self.account or 'Expenses:Unknown',
            units=self.amount,
            cost=None,
            price=amount_div(self.debited_amount, self.amount.number)
            if self.debited_amount
            and self.debited_amount.currency != self.amount.currency else None,
            flag=FLAG_WARNING,
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
