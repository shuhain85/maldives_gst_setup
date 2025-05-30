import frappe

@frappe.whitelist()
def run_gst_setup():
    company = frappe.defaults.get_user_default("Company")
    if not company:
        return "No default company found. Please set a default Company in your user settings."

    try:
        from maldives_gst_setup.setup.utils import create_gst_accounts_and_templates
        result = create_gst_accounts_and_templates(company)
        return result
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "GST Setup Wizard Error")
        return f"Error: {str(e)}"
