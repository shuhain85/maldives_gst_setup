import frappe
from frappe.model.document import Document

def create_gst_accounts_and_templates(company):
    created = []

    # -------------------------------------
    # Output GST Account
    # -------------------------------------
    if not frappe.db.exists("Account", {"account_name": "Output GST", "company": company}):
        frappe.get_doc({
            "doctype": "Account",
            "account_name": "Output GST",
            "parent_account": get_parent_account(company, "Liability"),
            "company": company,
            "root_type": "Liability",
            "account_type": "Tax"
        }).insert()
        created.append("Output GST account created")

    # -------------------------------------
    # Input GST Account
    # -------------------------------------
    if not frappe.db.exists("Account", {"account_name": "Input GST", "company": company}):
        frappe.get_doc({
            "doctype": "Account",
            "account_name": "Input GST",
            "parent_account": get_parent_account(company, "Asset"),
            "company": company,
            "root_type": "Asset",
            "account_type": "Tax"
        }).insert()
        created.append("Input GST account created")

    # -------------------------------------
    # Purchase Tax Template (Inclusive)
    # -------------------------------------
    if not frappe.db.exists("Purchase Taxes and Charges Template", {"title": "Maldives GST 8%", "company": company}):
        frappe.get_doc({
            "doctype": "Purchase Taxes and Charges Template",
            "title": "Maldives GST 8%",
            "company": company,
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": f"Input GST - {company_abbr(company)}",
                "rate": 8,
                "included_in_print_rate": 1
            }]
        }).insert()
        created.append("Purchase Tax Template created")

    # -------------------------------------
    # Sales Tax Template (Inclusive)
    # -------------------------------------
    if not frappe.db.exists("Sales Taxes and Charges Template", {"title": "Maldives GST 8%", "company": company}):
        frappe.get_doc({
            "doctype": "Sales Taxes and Charges Template",
            "title": "Maldives GST 8%",
            "company": company,
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": f"Output GST - {company_abbr(company)}",
                "rate": 8,
                "included_in_print_rate": 1
            }]
        }).insert()
        created.append("Sales Tax Template created")

    # -------------------------------------
    # Item Tax Templates
    # -------------------------------------
    tax_templates = [
        ("Taxable sales", [{"tax_type": "Maldives GST 8%", "tax_rate": 8}]),
        ("Taxable Purchase", [{"tax_type": "Maldives GST 8%", "tax_rate": 8}]),
        ("Non-Taxable sales", []),
        ("Non taxable purchase", [])
    ]

    for title, taxes in tax_templates:
        if not frappe.db.exists("Item Tax Template", {"title": title, "company": company}):
            frappe.get_doc({
                "doctype": "Item Tax Template",
                "title": title,
                "company": company,
                "taxes": taxes
            }).insert()
            created.append(f"Item Tax Template created: {title}")

    # -------------------------------------
    # Tax Category
    # -------------------------------------
    if not frappe.db.exists("Tax Category", {"title": "Purchase"}):
        frappe.get_doc({
            "doctype": "Tax Category",
            "title": "Purchase",
            "default": 1,
            "company": company
        }).insert()
        created.append("Tax Category 'Purchase' created")

    # -------------------------------------
    # Tax Rule
    # -------------------------------------
    if not frappe.db.exists("Tax Rule", {"apply_on": "Item Tax Template", "tax_template": "Maldives GST 8%"}):
        frappe.get_doc({
            "doctype": "Tax Rule",
            "apply_on": "Item Tax Template",
            "tax_template": "Maldives GST 8%",
            "company": company,
            "tax_category": "Purchase",
            "item_tax_template": "Taxable Purchase",
            "priority": 1
        }).insert()
        created.append("Tax Rule for GST Item created")

    # -------------------------------------
    # Assign Item Tax Templates Based on custom_taxabel
    # -------------------------------------
    items = frappe.get_all("Item", fields=["name", "custom_taxabel"])
    for item in items:
        doc = frappe.get_doc("Item", item.name)
        doc.taxes = []

        if item.custom_taxabel == "Yes":
            doc.append("taxes", {
                "item_tax_template": "Taxable sales"
            })
            doc.append("taxes", {
                "item_tax_template": "Taxable Purchase",
                "tax_category": "Purchase"
            })
        elif item.custom_taxabel == "No":
            doc.append("taxes", {
                "item_tax_template": "Non-Taxable sales"
            })
            doc.append("taxes", {
                "item_tax_template": "Non taxable purchase",
                "tax_category": "Purchase"
            })

        doc.save()
        created.append(f"Updated Item tax templates for: {item.name}")

    # -------------------------------------
    # Add Custom Fields to Sales Invoice
    # -------------------------------------
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

    sales_invoice_fields = {
        "Sales Invoice": [
            {
                "fieldname": "custom_taxable_total",
                "label": "taxable_total",
                "fieldtype": "Currency",
                "insert_after": "in_words",
                "read_only": 1,
                "in_list_view": 1,
                "in_preview": 1
            },
            {
                "fieldname": "custom_non_taxable_total",
                "label": "non_taxable_total",
                "fieldtype": "Currency",
                "insert_after": "custom_taxable_total",
                "read_only": 1,
                "in_list_view": 1,
                "in_preview": 1
            },
            {
                "fieldname": "custom_tax_total",
                "label": "Tax_Total",
                "fieldtype": "Currency",
                "insert_after": "custom_non_taxable_total",
                "read_only": 1,
                "in_list_view": 1,
                "in_preview": 1
            }
        ]
    }

    create_custom_fields(sales_invoice_fields)
    created.append("Custom fields added to Sales Invoice (tax totals)")

    # -------------------------------------
    # Client Script: Refresh Fields After Submit
    # -------------------------------------
    if not frappe.db.exists("Client Script", {"name": "Refresh Tax Totals on Load"}):
        frappe.get_doc({
            "doctype": "Client Script",
            "dt": "Sales Invoice",
            "script_type": "Form",
            "enabled": 1,
            "module": "Custom",
            "script": """
frappe.ui.form.on('Sales Invoice', {
    refresh(frm) {
        if (frm.doc.docstatus === 1) {
            frm.refresh_field('custom_taxable_total');
            frm.refresh_field('custom_non_taxable_total');
            frm.refresh_field('custom_tax_total');
        }
    }
});
"""
        }).insert()
        created.append("Client Script: Refresh Tax Totals on Load created")
# -------------------------------------
# Client Scripts: UOM Enforcement for Sales, Delivery, Quotation, Orders
# -------------------------------------

client_scripts = [
    {
        "doctype": "Client Script",
        "dt": "Sales Invoice",
        "script_type": "Form",
        "name": "sales_uom",
        "script": """
frappe.ui.form.on('Sales Invoice', {
    onload: function(frm) {
        frm.fields_dict.items.grid.get_field('uom').get_query = function(doc, cdt, cdn) {
            let row = locals[cdt][cdn];
            if (uom_lists[cdn]) {
                return { filters: { 'name': ['in', uom_lists[cdn]] } };
            } else {
                return { filters: { 'name': ['!=', ''] } };
            }
        };
    }
});
let uom_lists = {};
frappe.ui.form.on('Sales Invoice Item', {
    item_code: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        frappe.db.get_doc('Item', row.item_code).then(docs => {
            let uom_list = [];
            docs.uoms.forEach(uom => uom_list.push(uom.uom));
            uom_lists[cdn] = uom_list;
            frm.fields_dict.items.grid.get_field('uom').refresh();
        });
    },
    uom: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (uom_lists[cdn] && !uom_lists[cdn].includes(row.uom)) {
            frappe.msgprint(`UOM "${row.uom}" is not valid for Item "${row.item_code}".`);
            frappe.model.set_value(cdt, cdn, 'uom', '');
        }
    }
});
"""
    },
    {
        "doctype": "Client Script",
        "dt": "Delivery Note",
        "script_type": "Form",
        "name": "delivery_uom",
        "script": """
frappe.ui.form.on('Delivery Note', {
    onload: function(frm) {
        frm.fields_dict.items.grid.get_field('uom').get_query = function(doc, cdt, cdn) {
            let row = locals[cdt][cdn];
            if (uom_lists[cdn]) {
                return { filters: { 'name': ['in', uom_lists[cdn]] } };
            } else {
                return { filters: { 'name': ['!=', ''] } };
            }
        };
    }
});
let uom_lists = {};
frappe.ui.form.on('Delivery Note Item', {
    item_code: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        frappe.db.get_doc('Item', row.item_code).then(docs => {
            let uom_list = [];
            docs.uoms.forEach(uom => uom_list.push(uom.uom));
            uom_lists[cdn] = uom_list;
            frm.fields_dict.items.grid.get_field('uom').refresh();
        });
    },
    uom: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (uom_lists[cdn] && !uom_lists[cdn].includes(row.uom)) {
            frappe.msgprint(`UOM "${row.uom}" is not valid for Item "${row.item_code}".`);
            frappe.model.set_value(cdt, cdn, 'uom', '');
        }
    }
});
"""
    },
    {
        "doctype": "Client Script",
        "dt": "Sales Order",
        "script_type": "Form",
        "name": "order_uom",
        "script": """
frappe.ui.form.on('Sales Order', {
    onload: function(frm) {
        frm.fields_dict.items.grid.get_field('uom').get_query = function(doc, cdt, cdn) {
            let row = locals[cdt][cdn];
            if (uom_lists[cdn]) {
                return { filters: { 'name': ['in', uom_lists[cdn]] } };
            } else {
                return { filters: { 'name': ['!=', ''] } };
            }
        };
    }
});
let uom_lists = {};
frappe.ui.form.on('Sales Order Item', {
    item_code: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        frappe.db.get_doc('Item', row.item_code).then(docs => {
            let uom_list = [];
            docs.uoms.forEach(uom => uom_list.push(uom.uom));
            uom_lists[cdn] = uom_list;
            frm.fields_dict.items.grid.get_field('uom').refresh();
        });
    },
    uom: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (uom_lists[cdn] && !uom_lists[cdn].includes(row.uom)) {
            frappe.msgprint(`UOM "${row.uom}" is not valid for Item "${row.item_code}".`);
            frappe.model.set_value(cdt, cdn, 'uom', '');
        }
    }
});
"""
    },
    {
        "doctype": "Client Script",
        "dt": "Purchase Invoice",
        "script_type": "Form",
        "name": "purchase_invoice_uom",
        "script": """
frappe.ui.form.on('Purchase Invoice', {
    onload: function(frm) {
        frm.fields_dict.items.grid.get_field('uom').get_query = function(doc, cdt, cdn) {
            let row = locals[cdt][cdn];
            if (uom_lists[cdn]) {
                return { filters: { 'name': ['in', uom_lists[cdn]] } };
            } else {
                return { filters: { 'name': ['!=', ''] } };
            }
        };
    }
});
let uom_lists = {};
frappe.ui.form.on('Purchase Invoice Item', {
    item_code: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        frappe.db.get_doc('Item', row.item_code).then(docs => {
            let uom_list = [];
            docs.uoms.forEach(uom => uom_list.push(uom.uom));
            uom_lists[cdn] = uom_list;
            frm.fields_dict.items.grid.get_field('uom').refresh();
        });
    },
    uom: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (uom_lists[cdn] && !uom_lists[cdn].includes(row.uom)) {
            frappe.msgprint(`UOM "${row.uom}" is not valid for Item "${row.item_code}".`);
            frappe.model.set_value(cdt, cdn, 'uom', '');
        }
    }
});
"""
    },
    {
        "doctype": "Client Script",
        "dt": "Quotation",
        "script_type": "Form",
        "name": "quotation_uom",
        "script": """
frappe.ui.form.on('Quotation', {
    onload: function(frm) {
        frm.fields_dict.items.grid.get_field('uom').get_query = function(doc, cdt, cdn) {
            let row = locals[cdt][cdn];
            if (uom_lists[cdn]) {
                return { filters: { 'name': ['in', uom_lists[cdn]] } };
            } else {
                return { filters: { 'name': ['!=', ''] } };
            }
        };
    }
});
let uom_lists = {};
frappe.ui.form.on('Quotation Item', {
    item_code: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        frappe.db.get_doc('Item', row.item_code).then(docs => {
            let uom_list = [];
            docs.uoms.forEach(uom => uom_list.push(uom.uom));
            uom_lists[cdn] = uom_list;
            frm.fields_dict.items.grid.get_field('uom').refresh();
        });
    },
    uom: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (uom_lists[cdn] && !uom_lists[cdn].includes(row.uom)) {
            frappe.msgprint(`UOM "${row.uom}" is not valid for Item "${row.item_code}".`);
            frappe.model.set_value(cdt, cdn, 'uom', '');
        }
    }
});
"""
    }
]

for script in client_scripts:
    if not frappe.db.exists("Client Script", {"dt": script["dt"], "script_type": "Form", "name": script["name"]}):
        frappe.get_doc(script).insert()
        created.append(f"Client Script for {script['dt']} created: {script['name']}")

#  Move this outside the loop
return "\n".join(created) or "Nothing new created. Already configured."



def get_parent_account(company, root_type):
    acc = frappe.db.get_value("Account", {"company": company, "root_type": root_type, "is_group": 1}, "name")
    if not acc:
        frappe.throw(f"No parent account found for root type: {root_type}")
    return acc

def company_abbr(company):
    return frappe.db.get_value("Company", company, "abbr")
