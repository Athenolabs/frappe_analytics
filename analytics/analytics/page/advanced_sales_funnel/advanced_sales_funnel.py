# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
from collections import OrderedDict

import frappe
import random
import datetime
import json

from frappe import _


@frappe.whitelist()
def get_funnel_data(from_date, to_date, date_range):
    funnel_stages = get_funnel_setup_info()
    ret = []
    x_axis_interval = date_range_to_int(date_range)
    dates = setup_dates(from_date, to_date, x_axis_interval)
    # key is doctype, value is status - is this the best way?
    # could restructure and pop dates in...?
    # ALSO need to split into stages by doctype...can't do sequence with
    # mult doctypes
    lead_stages = {k:v for k, v in funnel_stages.iteritems() if v[0] == "Lead"}
    oppt_stages = {k:v for k, v in funnel_stages.iteritems()
                   if v[0] == "Opportunity"}
    quote_stages = {k:v for k, v in funnel_stages.iteritems()
                    if v[0] == "Quotation"}
    if lead_stages:
        lead_data = get_data(lead_stages, from_date, dates)
        for key, value in lead_data.iteritems():
            ret.append(format_data(key, value, "Lead"))
    if oppt_stages:
        oppt_data = get_data(oppt_stages, from_date, dates)
        for key, value in oppt_data.iteritems():
            ret.append(format_data(key, value, "Opportunity"))
    if quote_stages:
        quote_data = get_data(quote_stages, from_date, dates)
        for key, value in quote_data.iteritems():
            ret.append(format_data(key, value, "Quotation"))

    return {
        "dataset": ret,
        "columns": [str(date['start_date']) for date in dates]
        }


def format_data(key, value, document):
    return {
                "label": document + " - " + key,
                "data": value,
                "backgroundColor": "#%06x" % random.randint(0, 0xFFFFFF)
        }


def setup_dates(from_date, to_date, date_range):
    start_date = datetime.datetime.strptime(from_date, "%Y-%m-%d").date()
    end_date = datetime.datetime.strptime(to_date, "%Y-%m-%d").date()
    end_date += datetime.timedelta(days=1)
    time_period = (end_date - start_date).days
    columns = (int(time_period) / (int(date_range) + 1))
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


def get_data(stages, start_date, dates):
    # hack to get idx 0 of tuple (doctype name) from first item of stages dict
    doctype = stages[stages.keys()[0]][0]

    # set up a dict to hold a list of # in stage for each date range (history)
    # also, set up a template to be able to += / -= and then append to the
    # master history list
    # looks like {stage_name: [# in range 1, # in range 2, etc]}
    stage_history = {}
    for key, value in stages.iteritems():
        stage_history[value[1]] = []
    initial_entry = get_init_data(
        doctype, get_blank_stage_template(stages), start_date
        )

    for key, value in initial_entry.iteritems():
        stage_history[key].append(value)
    for date in dates:
        next_set = get_changes(doctype, get_blank_stage_template(stages), date)
        for key, value in next_set.iteritems():
            next_value = stage_history[key][-1] + next_set[key]
            if next_value >= 0:
                stage_history[key].append(next_value)
            else:
                stage_history[key].append(0)

    # need to pop initial data from set
    for key, value in stage_history.iteritems():
        value.pop(0)
    print(stage_history)
    return stage_history


def get_blank_stage_template(stages):
    template = {}
    for key, value in stages.iteritems():
        template[value[1]] = 0
    return template


def get_changes(doctype, stage_template, date):
    query = frappe.db.sql("""
        select a.changed_doc_name, a.old_value, a.new_value, b.status
        from `tab{0} Field History` a
        left outer join `tab{0}` b on a.changed_doc_name = b.name
        where a.fieldname = "status" and (date(a.date) between %s and %s)
        and (date(b.modified) between %s and %s)
        union
        select a.changed_doc_name, a.old_value, a.new_value, b.status
        from `tab{0} Field History` a
        right outer join `tab{0}` b on a.changed_doc_name = b.name
        where a.fieldname = "status" and (date(a.date) between %s and %s)
        and (date(b.modified) between %s and %s)
    """.format(doctype),
        (date['start_date'], date['end_date'], date['start_date'],
        date['end_date'], date['start_date'], date['end_date'],
        date['start_date'], date['end_date']), as_dict=True)
    for entry in query:
        if entry['old_value'] != None:
            print("coming from old value "),
            print(entry['old_value']),
            print(" to new value "),
            print(entry['new_value'])
            try:
                stage_template[entry['old_value']] -= 1
            except KeyError:
                pass
            try:
                stage_template[entry['new_value']] += 1
            except KeyError:
                pass
        elif entry['old_value'] == None and entry['new_value'] != None:
            print("no old value, new value is "),
            print(entry['new_value'])
            try:
                stage_template[entry['new_value']] += 1
            except KeyError:
                pass
        else:
            print("no history, doc is "),
            print(entry)
            try:
                stage_template[entry['status']] += 1
            except KeyError:
                pass
    return stage_template


def get_init_data(doctype, stage_template, start_date):
    query = frappe.db.sql("""
        select `name`, `status` from `tab{0}`
        where (date(`modified`) <= %s)
    """.format(doctype), start_date, as_dict=True)
    for entry in query:
        try:
            stage_template[entry['status']] += 1
        except KeyError:
            pass
    print(stage_template)
    return stage_template



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
        return 30
    elif date_range == "Quarterly":
        return 89
    elif date_range == "Yearly":
        return 364
