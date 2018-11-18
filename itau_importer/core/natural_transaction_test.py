import unittest
import textwrap

from datetime import date
from beancount.core.amount import A

from .natural_transaction import NaturalTransaction


def normalize_entry(entry):
    return '\n'.join([l.rstrip() for l in entry.splitlines() if len(l) != 0])


class NaturalTransactionTest(unittest.TestCase):
    def setUp(self):
        self.transaction = NaturalTransaction(
            date(2012, 12, 12),
            A('10 UYU'),
            'Assets:Cash',
        )

    def test_renders_mandatory_fields(self):

        target = textwrap.dedent("""
            2012-12-12 *
              ! Expenses:Unknown  10 UYU
              Assets:Cash
        """)
        self.assertEqual(
            normalize_entry(target),
            normalize_entry(self.transaction.render()),
        )

    def test_renders_with_descriptions(self):
        target = textwrap.dedent("""
            2012-12-12 * "Description"
              ! Expenses:Unknown  10 UYU
              Assets:Cash
        """)
        self.transaction.description = "Description"
        self.assertEqual(
            normalize_entry(target),
            normalize_entry(self.transaction.render()),
        )

    def test_renders_with_payee(self):
        target = textwrap.dedent("""
            2012-12-12 * "Payee" ""
              ! Expenses:Unknown  10 UYU
              Assets:Cash
        """)
        self.transaction.payee = "Payee"
        self.assertEqual(
            normalize_entry(target),
            normalize_entry(self.transaction.render()),
        )

    def test_renders_with_descriptions_and_payee(self):
        target = textwrap.dedent("""
            2012-12-12 * "Payee" "Description"
              ! Expenses:Unknown  10 UYU
              Assets:Cash
        """)
        self.transaction.payee = "Payee"
        self.transaction.description = "Description"
        self.assertEqual(
            normalize_entry(target),
            normalize_entry(self.transaction.render()),
        )

    def test_renders_conversions(self):
        target = textwrap.dedent("""
            2012-12-12 * "Payee" "Description"
              ! Expenses:Unknown  10 UYU @ 0.5 ARS
              Assets:Cash         -5 ARS
        """)
        self.transaction.payee = "Payee"
        self.transaction.description = "Description"
        self.transaction.debited_amount = A('5 ARS')
        self.assertEqual(
            normalize_entry(target),
            normalize_entry(self.transaction.render()),
        )
