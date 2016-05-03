frappe.pages['advanced-sales-funnel'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Advanced Sales Funnel',
		single_column: true
	});
	wrapper.sales_funnel = new AdvancedSalesFunnel(page, wrapper);

	frappe.breadcrumbs.add("Analytics");
}

this.AdvancedSalesFunnel = Class.extend({
	init: function(page, wrapper) {
		var me = this;
		// 0 setTimeout hack - this gives time for canvas to get width and height
		setTimeout(function() {
			me.setup(wrapper);
			me.get_data(page);
		}, 0);
	},

	setup: function(wrapper) {
		var me = this;

		this.elements = {
			layout: $(wrapper).find(".layout-main"),
			from_date: wrapper.page.add_date(__("From Date")),
			to_date: wrapper.page.add_date(__("To Date")),
			date_range: wrapper.page.add_field(
				{fieldtype:"Select", label: __("Range"), fieldname: "date_range",
				  id:"Weekly",
					options:[{label: __("Daily"), value: "Daily"},
					{label: __("Weekly"), value: "Weekly"},
					{label: __("Monthly"), value: "Monthly"},
					{label: __("Quarterly"), value: "Quarterly"},
					{label: __("Yearly"), value: "Yearly"}
					]
				}
			),
			refresh_btn: wrapper.page.set_primary_action(__("Reload"),
				function() { me.get_data(); }, "icon-refresh"),
		};

		this.options = {
			from_date: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			to_date: frappe.datetime.get_today(),
			date_range: "Weekly"
		};

		$.each(this.options, function(k, v) {
			try{
				me.elements[k].val(frappe.datetime.str_to_user(v));
				me.elements[k].on("change", function() {
					me.options[k] = frappe.datetime.user_to_str($(this).val());
					me.get_data();
				});
			}catch(err){
			}
		});

		// bind refresh
		this.elements.refresh_btn.on("click", function() {
			me.get_data();
		});
	},

	get_data: function(page, btn) {
		var me = this;
		var sel_range = $(".input-with-feedback option:selected").text();
		if (!sel_range) {
			sel_range = "Weekly"
		};
		frappe.call({
			method: "analytics.analytics.page.advanced_sales_funnel.advanced_sales_funnel.get_funnel_data",
			args: {
				from_date: me.options.from_date,
				to_date: me.options.to_date,
				date_range: sel_range
			},
			btn: btn,
			callback: function(r) {
				if(!r.exc) {
					var funnel_data = r.message.dataset;
					var columns = r.message.columns;
					$(".layout-main-section").append("<canvas id='myChart'></canvas>");
					var ctx = $("#myChart");
					var myChart = new Chart(ctx, {
					  type: "bar",
					  data: {
					    labels: columns,
					    datasets: funnel_data
					  },
					  options: {
					    scales: {
					      xAxes: [{
					        stacked: true
					      }],
					      yAxes: [{
					        stacked: true,
					        ticks: {
					          beginAtZero: true
					        }
					      }]
					    }
					  }
					});
				}
			}
		});
	}
});
