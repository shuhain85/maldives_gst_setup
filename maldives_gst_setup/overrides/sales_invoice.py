from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice as BaseSalesInvoice
import frappe

class CustomSalesInvoice(BaseSalesInvoice):
    def validate(self):
        super().validate()
        self.set_tax_totals()

    def set_tax_totals(self):
        taxable = 0
        non_taxable = 0
        tax_total = 0

        for item in self.items:
            if item.item_tax_template:
                try:
                    template = frappe.get_doc("Item Tax Template", item.item_tax_template)
                    rate = template.taxes[0].tax_rate if template.taxes else 0
                except:
                    rate = 0
            else:
                rate = 0

            base_net = item.base_net_amount or 0

            if rate >= 8:
                taxable += base_net
                tax_total += (base_net * rate / 100)
            else:
                non_taxable += base_net

        self.custom_taxable_total = taxable
        self.custom_non_taxable_total = non_taxable
        self.custom_tax_total = tax_total