import zipfile
from datetime import datetime

from beancount.core.data import Amount
from beancount.core.number import D

from .core.mixins import InferPayeeMixin, MergeIvaDiscountMixin
from .core.natural_importer import NaturalImporter
from .core.natural_transaction import NaturalTransaction

TOKEN = 'UMSATZ'


def get_target_file(file):
    myzip = zipfile.ZipFile(file)
    return next(
        myzip.read(zip_info) for zip_info in myzip.filelist
        if zip_info.filename.startswith(TOKEN)).decode()


class MultiCashImporter(MergeIvaDiscountMixin, NaturalImporter):
    def identify(self, file):
        if file.mimetype() != 'application/zip':
            return False
        try:
            file.convert(get_target_file)
        except StopIteration:
            return False
        return True

    def parse_line(self, line):
        cells = line.split(';')
        return NaturalTransaction(
            date=datetime.strptime(cells[3], '%d.%m.%y').date(),
            amount=Amount(D(cells[10]) * -1, 'UYU'),
            debited_account='Expenses:Itau',
            description=' '.join([cells[6], cells[9]]),
        )

    def converter(self, file):
        raw_file = file.convert(get_target_file)
        return [self.parse_line(line) for line in raw_file.splitlines()]
