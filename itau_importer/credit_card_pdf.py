from datetime import datetime

from beancount.core.data import Amount
from beancount.core.number import D

from .core.mixins import InferPayeeMixin, MergeIvaDiscountMixin
from .core.natural_importer import NaturalImporter
from .core.natural_transaction import NaturalTransaction
from .utils import pdf_parser


class CreditCardPDFImporter(InferPayeeMixin, MergeIvaDiscountMixin,
                            NaturalImporter):
    def __init__(self, account_uyu, account_usd):
        self.account = {
            'USD': account_usd,
            'UYU': account_uyu,
        }

    def identify(self, file):
        if file.mimetype() != 'application/pdf':
            return False

        entries = file.convert(pdf_parser.credit_card_parser)
        if len(entries) == 0:
            return False

        return True

    def get_debited_amount(self, parsed_transaction):
        [amount_origin, amount_uyu, amount_usd] = [
            parsed_transaction[x]
            for x in ['amount_origin', 'amount_uyu', 'amount_usd']
        ]
        return infer_amount(amount_origin, amount_uyu, amount_usd)[0]

    def get_amount(self, parsed_transaction):
        [amount_origin, amount_uyu, amount_usd] = [
            parsed_transaction[x]
            for x in ['amount_origin', 'amount_uyu', 'amount_usd']
        ]

        [amount, origin] = infer_amount(amount_origin, amount_uyu, amount_usd)

        return origin or amount

    def converter(self, file):
        parsed_entries = file.convert(pdf_parser.credit_card_parser)
        return [
            NaturalTransaction(
                date=datetime.strptime(t['date'], '%Y-%m-%d').date(),
                description=t['description'],
                payee=None,
                amount=self.get_amount(t),
                debited_amount=self.get_debited_amount(t),
                account=None,
                debited_account=self.account[self.get_debited_amount(t).
                                             currency]) for t in parsed_entries
            if not t['is_card_payment']
        ]


def parse_number(number):
    return D(str(number)).quantize(D('0.00'))


def infer_amount(amount_origin, amount_uyu, amount_usd):
    if not ((amount_usd is None) ^ (amount_uyu is None)):
        raise ValueError("Only one of UYU or USD can be provided")

    if amount_uyu:
        amount = Amount(parse_number(amount_uyu), 'UYU')

    if amount_usd:
        amount = Amount(parse_number(amount_usd), 'USD')

    origin = None

    if amount_origin and amount_origin != amount.number:
        origin = Amount(D(str(amount_origin)), 'UNKNOWN')

    return amount, origin
