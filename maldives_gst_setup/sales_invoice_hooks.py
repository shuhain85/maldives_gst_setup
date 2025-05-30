# -------------------------------------
# Server Hook: Calculate Totals on Sales Invoice Submit
# -------------------------------------

import frappe

def calculate_tax_totals(doc, method):
    taxable = 0
    non_taxable = 0
    tax_amount = 0

    for item in doc.items:
        if not item.item_code:
            continue
        item_doc = frappe.get_doc("Item", item.item_code)
        if item_doc.get("custom_taxabel") == "Yes":
            taxable += item.amount or 0
        elif item_doc.get("custom_taxabel") == "No":
            non_taxable += item.amount or 0

    for tax in doc.get("taxes", []):
        tax_amount += tax.tax_amount or 0

    doc.custom_taxable_total = taxable
    doc.custom_non_taxable_total = non_taxable
    doc.custom_tax_total = tax_amount
