from itau_importer.utils.iva_discount_merger import merge_iva_discounts


class MergeIvaDiscountMixin:
    def extract(self, file, existing_entries):
        transactions = super().extract(file, existing_entries)
        merge_iva_discounts(transactions)
        return transactions
