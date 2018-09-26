#!/usr/bin/env python3
from datetime import datetime

from beancount.ingest.importer import ImporterProtocol

from beancount.core import flags
from beancount.core.data import Transaction, Posting, Amount, new_metadata
from beancount.core.number import D
from beancount.core.getters import get_all_payees

from .utils import pdf_parser


class CreditCardPDFImporter(ImporterProtocol):
    """Itau's Credit Card PDF Importer"""

    def __init__(self, base_account):
        self.base_account = base_account

    def name(self):
        return self.__class__.__name__

    __str__ = name

    def identify(self, file):
        if file.mimetype() != 'application/pdf':
            return False

        entries = file.convert(pdf_parser.credit_card_parser)
        if len(entries) == 0:
            return False

        return True

    def extract(self, file, existing_entries):
        payees = get_all_payees(existing_entries)
        parsed_entries = file.convert(pdf_parser.credit_card_parser)

        transactions = []
        for entry in parsed_entries:
            if entry.get('is_card_payment', False):
                continue

            infered_payee = infer_payee(payees, entry['description'])
            txn_expense_account = 'Expenses:Unknown'
            txn_units, txn_price = infer_amount(entry['amount_origin'],
                                                entry['amount_uyu'],
                                                entry['amount_usd'])
            txn = Transaction(
                meta=new_metadata(file.name, 0),
                date=datetime.strptime(entry['date'], '%Y-%m-%d').date(),
                flag=flags.FLAG_OKAY,
                tags=set(),
                payee=infered_payee,
                links=set(),
                postings=[
                    Posting(txn_expense_account, txn_units, None, txn_price,
                            flags.FLAG_WARNING, None),
                    Posting(f'{self.base_account}:{txn_units.currency}', None,
                            None, None, None, None),
                ],
                narration=entry['description'] if not infered_payee else '')

            transactions.append(txn)

        return transactions


def infer_payee(payees, description):
    payees = list(payee for payee in payees
                  if payee.lower().replace(' ', '') in description.replace(
                      ' ', '').lower())
    if len(payees) == 0:
        return None
    return sorted(payees, key=len, reverse=True)[0]


def infer_amount(origin_amount, amount_uyu, amount_usd):
    if not (bool(amount_usd) ^ bool(amount_uyu)):
        raise ValueError("Only one of UYU or USD can be provided")

    if amount_uyu:
        amount = amount_uyu
        currency = 'UYU'

    if amount_usd:
        amount = amount_usd
        currency = 'USD'

    price = None

    if origin_amount and abs(origin_amount) != abs(amount):
        origin_currency = 'UNKNOWN'
        origin_rate = origin_amount / amount

        price = Amount(D(origin_rate).quantize(D('0.00')), origin_currency)

    return Amount(D(amount).quantize(D('0.00')), currency), price
