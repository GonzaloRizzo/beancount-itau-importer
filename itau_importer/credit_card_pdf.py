from datetime import datetime

from beancount.core.data import Amount
from beancount.core.number import D

from .core.mixins import InferPayeeMixin, MergeIvaDiscountMixin, AttachInternationalTaxMixin
from .core.natural_importer import NaturalImporter
from .core.natural_transaction import NaturalTransaction
from .utils import pdf_parser


def parse_number(number):
    return D(str(number)).quantize(D('0.00'))


def infer_amounts(amount_origin, amount_uyu, amount_usd):
    if not ((amount_usd is None) ^ (amount_uyu is None)):
        raise ValueError("Only one of UYU or USD can be provided")

    if amount_uyu:
        amount = Amount(parse_number(amount_uyu), 'UYU')

    if amount_usd:
        amount = Amount(parse_number(amount_usd), 'USD')

    origin = None

    if amount_origin and amount_origin != float(amount.number):
        origin = Amount(parse_number(amount_origin), 'UNKNOWN')

    return amount, origin


class CreditCardPDFImporter(
        InferPayeeMixin,
        MergeIvaDiscountMixin,
        AttachInternationalTaxMixin,
        NaturalImporter,
):
    def __init__(self, account_uyu, account_usd):
        self.account = {
            'USD': account_usd,
            'UYU': account_uyu,
        }

    def identify(self, file):
        if file.mimetype() != 'application/pdf':
            return False

        entries = file.convert(pdf_parser.credit_card_parser)

        return len(entries) > 0

    def converter(self, file):
        entries = file.convert(pdf_parser.credit_card_parser)
        return [
            self.parse_entry(e) for e in entries if not e['is_card_payment']
        ]

    def parse_entry(self, entry):
        [debited_amount, origin_amount] = infer_amounts(
            entry['amount_origin'],
            entry['amount_uyu'],
            entry['amount_usd'],
        )

        return NaturalTransaction(
            date=datetime.strptime(entry['date'], '%Y-%m-%d').date(),
            amount=origin_amount or debited_amount,
            debited_account=self.account[debited_amount.currency],
            description=entry['description'],
            debited_amount=debited_amount,
            meta={'_is_international': entry['amount_origin'] is not None})
