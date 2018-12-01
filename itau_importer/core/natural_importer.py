from typing import List

from beancount.core.data import Entries, new_metadata
from beancount.ingest.importer import ImporterProtocol

from .natural_transaction import NaturalTransaction


class NaturalImporter(ImporterProtocol):
    def converter(self, file) -> List[NaturalTransaction]:
        raise NotImplementedError

    def pre_parse(
            self,
            natural_transactions: List[NaturalTransaction],
            existing_entries: Entries,
    ):
        return natural_transactions

    def extract(self, file, existing_entries):
        natural_transactions = self.converter(file)
        natural_transactions = self.pre_parse(natural_transactions,
                                              existing_entries)

        return [
            natural_transaction.parse(new_metadata(file, 0))
            for natural_transaction in natural_transactions
        ]
