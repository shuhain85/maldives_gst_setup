from frappe import _

def get_data():
    return [
        {
            "module_name": "maldives_gst_setup",  # Must match modules.txt
            "label": _("Maldives GST"),
            "color": "blue",
            "icon": "octicon octicon-globe",
            "type": "module",
            "description": _("Maldives GST Setup Wizard and automation")
        }
    ]
