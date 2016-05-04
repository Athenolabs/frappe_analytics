# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import random
import datetime
import json

from frappe import _


@frappe.whitelist()
def get_funnel_data(from_date, to_date, date_range):
    rows = get_funnel_setup_info()
    ret = []
    date_range = date_range_to_int(date_range)
    for key, value in rows.iteritems():
        row_name = str(value[0]) + " - " + str(value[1])
        dates = setup_dates(from_date, to_date, date_range)
        queries = get_queries(dates, value)
        ret.append(
            {
                "idx": key,
                "label": row_name,
                "data": queries,
                "backgroundColor": "#%06x" % random.randint(0, 0xFFFFFF)
            }
        )

    sorted_dict = sorted(ret, key=lambda k: int(k['idx']))
    return {
        "dataset": sorted_dict,
        "columns": [str(date['start_date']) for date in dates]
        }


def setup_dates(from_date, to_date, date_range):
    start_date = datetime.datetime.strptime(from_date, "%Y-%m-%d").date()
    end_date = datetime.datetime.strptime(to_date, "%Y-%m-%d").date()
    end_date += datetime.timedelta(days=1)
    time_period = (end_date - start_date).days
    columns = time_period / (date_range + 1)
    ret = []
    for column in range(columns):
        next_date = start_date + datetime.timedelta(days=int(date_range))
        ret.append({
            "idx": column,
            "start_date": start_date,
            "end_date": next_date
        })
        start_date = next_date + datetime.timedelta(days=1)
    return sorted(ret, key=lambda k: int(k['idx']))


def get_queries(dates, value):
    sql_query = []
    for d in dates:
        #sql_query.append(frappe.db.sql("""select count(*) from `tabLead Field History`
        #where (date(`date`) between %s and %s) and `new_value` = "{1}"
        #order by `date` desc
        #""".format(value[0], value[1]), (d['start_date'], d['end_date']))[0][0])
        # Test data
        sql_query.append(random.randint(0, 25))
    return sql_query


def get_funnel_setup_info():
    funnel_dict = {}
    funnel_info = frappe.get_doc("Sales Funnel Setup").sales_funnel_setup
    for row in funnel_info:
        funnel_dict[str(row.idx)] = (row.document, row.status)
    return funnel_dict


def date_range_to_int(date_range):
    if date_range == "Daily":
        return 0
    elif date_range == "Weekly":
        return 6
    elif date_range == "Monthly":
        return 29
    elif date_range == "Quarterly":
        return 89
    elif date_range == "Yearly":
        return 364
