def auto_assign_item_tax_template(doc, method):
    doc.taxes = []

    if doc.custom_taxabel == "Yes":
        doc.append("taxes", {
            "item_tax_template": "Taxable sales"
        })
        doc.append("taxes", {
            "item_tax_template": "Taxable Purchase",
            "tax_category": "Purchase"
        })
    elif doc.custom_taxabel == "No":
        doc.append("taxes", {
            "item_tax_template": "Non-Taxable sales"
        })
        doc.append("taxes", {
            "item_tax_template": "Non taxable purchase",
            "tax_category": "Purchase"
        })
