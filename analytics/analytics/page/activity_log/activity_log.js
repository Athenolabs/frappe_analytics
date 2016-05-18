frappe.pages['activity-log'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Activity Log',
		single_column: true
	});
	wrapper.activity_log = new ActivityChart(page, wrapper);

}

this.ActivityChart = Class.extend({
	init: function(page, wrapper){
		var me = this;
		me.setup(wrapper);
		me.get_data();
	},

	setup: function(wrapper){
		var me = this;
		users = ['moe.barry@energychoice.com','manda.schulman@energychoice.com',
						 'minella.gjoka@energychoice.com', 'alejandro.ruiz_ramon@energychoice.com']
		this.elements = {
			layout: $(wrapper).find(".layout-main"),
			from_date: wrapper.page.add_date(__("From Date")),
			to_date: wrapper.page.add_date(__("To Date")),
			user: wrapper.page.add_select(__("User"), users),
			refresh_btn: wrapper.page.set_primary_action(__("Reload"),
				function() { me.get_data(); }, "icon-refresh"),
		};
		this.options = {
			from_date: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			to_date: frappe.datetime.get_today()
		}
		$.each(this.options, function(k, v) {
			try{
				me.elements[k].val(frappe.datetime.str_to_user(v));
				me.elements[k].on("change", function() {
					me.options[k] = frappe.datetime.user_to_str($(this).val());
				});
			}catch(err){
			}
		});
	},
	get_data: function(){
		var me = this;
		frappe.call({
			method: "analytics.analytics.page.activity_log.activity_log.get_data",
			args: {
				"from_date": me.options.from_date,
				"to_date": me.options.to_date,
				"user": $(me.elements.user).val()
			},
			callback: function(r){
				if($("#myChart").length == 0){
					$(".layout-main-section").append("<canvas id='myChart'></canvas>");
				}else{
					$("#myChart").remove();
					$(".layout-main-section").append("<canvas id='myChart'></canvas>");
				}
				var ctx = $("#myChart");
				var myChart = new Chart(ctx, {
					type: 'polarArea',
					data: {
						labels: r.message.labels,
						datasets: r.message.datasets
					},
				})
			}
		});
	}
});
