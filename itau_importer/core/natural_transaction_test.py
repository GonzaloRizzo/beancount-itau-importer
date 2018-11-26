import unittest
import textwrap

from datetime import date
from beancount.core.amount import A

from .natural_transaction import NaturalTransaction, Detail


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
              Expenses:Unknown  10 UYU
              Assets:Cash
        """)
        self.assertEqual(
            normalize_entry(target),
            normalize_entry(self.transaction.render()),
        )

    def test_renders_with_descriptions(self):
        target = textwrap.dedent("""
            2012-12-12 * "Description"
              Expenses:Unknown  10 UYU
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
              Expenses:Unknown  10 UYU
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
              Expenses:Unknown  10 UYU
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
              Expenses:Unknown  10 UYU
              Assets:Cash       -5 ARS @ 2 UYU
        """)
        self.transaction.payee = "Payee"
        self.transaction.description = "Description"
        self.transaction.debited_amount = A('5 ARS')
        self.assertEqual(
            normalize_entry(target),
            normalize_entry(self.transaction.render()),
        )

    def test_renders_details_with_whole_amount_detailed(self):
        target = textwrap.dedent("""
            2012-12-12 * "Payee" "Description"
              Expenses:Unknown    2 UYU
              Expenses:Unknown    3 UYU
              Expenses:Unknown    5 UYU
              Assets:Cash       -10 UYU
        """)
        self.transaction.payee = "Payee"
        self.transaction.description = "Description"
        self.transaction.details = [
            Detail(A('2 UYU')),
            Detail(A('3 UYU')),
            Detail(A('5 UYU')),
        ]
        self.assertEqual(
            normalize_entry(target),
            normalize_entry(self.transaction.render()),
        )

    def test_renders_details_with_partial_detailing(self):
        target = textwrap.dedent("""
            2012-12-12 * "Payee" "Description"
              Expenses:Unknown    2 UYU
              Expenses:Unknown    8 UYU
              Assets:Cash       -10 UYU
        """)
        self.transaction.payee = "Payee"
        self.transaction.description = "Description"
        self.transaction.details = [
            Detail(A('2 UYU')),
        ]
        self.assertEqual(
            normalize_entry(target),
            normalize_entry(self.transaction.render()),
        )

    def test_renders_details_with_descriptions(self):
        target = textwrap.dedent("""
                2012-12-12 * "Payee" "Description"
                  Expenses:Unknown    1 UYU
                    desc: "Item 1"
                  Expenses:Unknown    3 UYU
                    desc: "Item 2"
                  Expenses:Unknown    4 UYU
                  Expenses:Unknown    2 UYU
                  Assets:Cash       -10 UYU
            """)
        self.transaction.payee = "Payee"
        self.transaction.description = "Description"
        self.transaction.details = [
            Detail(A('1 UYU'), "Item 1"),
            Detail(A('3 UYU'), "Item 2"),
            Detail(A('4 UYU')),
        ]
        self.assertEqual(
            normalize_entry(target),
            normalize_entry(self.transaction.render()),
        )

    def test_renders_details_with_custom_account(self):
        target = textwrap.dedent("""
            2012-12-12 * "Payee" "Description"
              Liabilities:Debtor    2 UYU
              Liabilities:Debtor    3 UYU
                desc: "Eter"
              Expenses:Unknown      5 UYU
              Assets:Cash         -10 UYU
        """)
        self.transaction.payee = "Payee"
        self.transaction.description = "Description"
        self.transaction.details = [
            Detail(A('2 UYU'), account="Liabilities:Debtor"),
            Detail(A('3 UYU'), "Eter", "Liabilities:Debtor"),
        ]
        self.assertEqual(
            normalize_entry(target),
            normalize_entry(self.transaction.render()),
        )

    def test_renders_details_with_extra_flag(self):
        target = textwrap.dedent("""
            2012-12-12 * "Payee" "Description"
              Expenses:Unknown   10 UYU
              Assets:Cash       -10 UYU
              Income:Discount    -2 UYU
              Assets:Cash         2 UYU
        """)
        self.transaction.payee = "Payee"
        self.transaction.description = "Description"
        self.transaction.details = [
            Detail(A('-2 UYU'), extra=True, account="Income:Discount"),
        ]
        self.assertEqual(
            normalize_entry(target),
            normalize_entry(self.transaction.render()),
        )
