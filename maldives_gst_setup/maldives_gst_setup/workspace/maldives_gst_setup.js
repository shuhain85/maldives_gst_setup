frappe.provide("frappe.workspaces");

frappe.workspaces["maldives_gst_setup"] = {
  label: "Maldives GST",
  icon: "octicon octicon-globe",
  items: [
    {
      label: "GST Tools",
      items: [
        {
          type: "page",
          name: "gst-setup-wizard",
          label: "GST Setup Wizard"
        }
      ]
    }
  ]
};
