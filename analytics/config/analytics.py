from frappe import _


def get_data():
	return [
		{
			"label": _("CRM and Sales"),
			"icon": "icon-star",
			"items": [
				{
					"type": "page",
                    "Label": "Sales Pipeline Over Time",
                    "name": "advanced-sales-funnel",
					"icon": "icon-bar-chart",
				},
			]
		},
        {
            "label": _("Setup"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Document Versioning Settings"
                },
                {
                    "type": "doctype",
                    "name": "Sales Funnel Setup"
                }
            ]
        }
    ]
