import frappe
from analytics.analytics.common_methods import get_pallete


@frappe.whitelist()
def get_data(from_date, to_date, user):
    data = frappe.db.sql("""
        select `reference_doctype`, `user`, count(`name`) as total from `tabCommunication`
        where `user` = "{0}" and (date(`creation`) between %s and %s)
        group by `user`, `reference_doctype`
        """.format(user), (from_date, to_date), as_dict=True)
    data = scrub(data)
    print(data)
    datasets = [{
        'data': [item['total'] for item in data],
        'backgroundColor': get_pallete(len(data)),
    }]
    labels = [item['reference_doctype'] for item in data]

    return {
        'labels': labels,
        'datasets': datasets
    }

def scrub(data):
    accepted_list = [
        'Lead', 'Opportunity', 'Quotation', 'Sales Order', 'Delivery Note',
        'Sales Invoice', 'Supplier Quotation', 'Purchase Order',
        'Purchase Invoice'
        ]
    return [item for item in data if item['reference_doctype'] in accepted_list]
