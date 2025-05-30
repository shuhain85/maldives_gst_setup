frappe.pages['gst-setup-wizard'].on_page_load = function(wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: 'GST Setup Wizard (Maldives)',
    single_column: true
  });

  $(wrapper).html(frappe.render_template("gst_setup_wizard", {}));

  $('#run-gst-setup').on('click', function () {
    frappe.call({
      method: 'maldives_gst_setup.setup.setup_wizard.run_gst_setup',
      callback: function (r) {
        if (!r.exc) {
          $('#setup-log').html(`<pre>${r.message}</pre>`);
        }
      }
    });
  });
};
