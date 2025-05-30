import frappe
from erpnext.accounts.doctype.pos_invoice.pos_invoice import POSInvoice

class CustomPOSInvoice(POSInvoice):
    def validate(self):
        super().validate()

        for item in self.items:
            allowed_uoms = frappe.get_all(
                "UOM Conversion Detail",
                filters={"parent": item.item_code},
                pluck="uom"
            )

            # Always allow the default stock_uom
            try:
                item_doc = frappe.get_doc("Item", item.item_code)
                if item_doc.stock_uom not in allowed_uoms:
                    allowed_uoms.append(item_doc.stock_uom)
            except Exception:
                pass

            if item.uom not in allowed_uoms:
                frappe.throw(
                    f"UOM '{item.uom}' is not allowed for item '{item.item_code}'. Allowed UOMs: {', '.join(allowed_uoms)}"
                )