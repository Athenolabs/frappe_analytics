// Copyright (c) 2016, Alec Ruiz-Ramon and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Funnel Setup', {
	refresh: function(frm) {

	}
});

frappe.ui.form.on("Document and Status Child Table", "document", function(doc, cdt, cdn){
	var doc = locals[cdt][cdn]
	frappe.call({
		method: "analytics.analytics.doctype.sales_funnel_setup.sales_funnel_setup.get_field_options",
		args: {
			"doc": doc,
			"field_name": "status"
		},
		callback: function(r){
			var chosen_field = frappe.prompt(
				{label: "Choose Status", fieldtype: "Select", options: r.message},
				function(data) {
				  console.log(data)
			    doc.status = data.choose_status;
					cur_frm.refresh();
					}
				)
			}
		})
});
