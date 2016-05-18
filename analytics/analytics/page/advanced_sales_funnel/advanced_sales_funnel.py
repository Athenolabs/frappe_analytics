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
def get_funnel_data(from_date, to_date, date_range, leads, opportunities,
                    quotations):
    funnel_stages = get_funnel_setup_info()
    ret = []
    x_axis_interval = date_range_to_int(date_range)
    dates = setup_dates(from_date, to_date, x_axis_interval)
    # key is doctype, value is status - is this the best way?
    # could restructure and pop dates in...?
    # ALSO need to split into stages by doctype...can't do sequence with
    # mult doctypes
    if leads == '1':
        lead_stages = {k:v for k, v in funnel_stages.iteritems()
                       if v[0] == "Lead"}
        if lead_stages:
            lead_data = get_data(lead_stages, dates, to_date)
            for key, value in lead_data.iteritems():
                ret.append(format_data(key, value, "Lead"))
    if opportunities == '1':
        oppt_stages = {k:v for k, v in funnel_stages.iteritems()
                       if v[0] == "Opportunity"}
        if oppt_stages:
            oppt_data = get_data(oppt_stages, dates, to_date)
            for key, value in oppt_data.iteritems():
                ret.append(format_data(key, value, "Opportunity"))
    if quotations == '1':
        quote_stages = {k:v for k, v in funnel_stages.iteritems()
                        if v[0] == "Quotation"}
        if quote_stages:
            quote_data = get_data(quote_stages, dates, to_date)
            for key, value in quote_data.iteritems():
                ret.append(format_data(key, value, "Quotation"))

    return {
        "dataset": ret,
        "columns": [str(date['start_date']) for date in dates][::-1]
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
    #end_date += datetime.timedelta(days=1)
    time_period = (end_date - start_date).days
    columns = (int(time_period) / (int(date_range) + 1))
    ret = []
    for column in range(columns):
        next_date = start_date + datetime.timedelta(days=int(date_range))
        ret.append(format_date(start_date, next_date, column))
        start_date = next_date + datetime.timedelta(days=1)
    return sorted(ret, key=lambda k: int(k['idx']), reverse=True)


def format_date(start_date, next_date, idx):
    return {"idx": idx, "start_date": start_date, "end_date": next_date}


def get_data(stages, dates, end_date):
    # hack to get idx 0 of tuple (doctype name) from first item of stages dict
    doctype = stages[stages.keys()[0]][0]
    # set up a dict to hold a list of # in stage for each date range (history)
    # also, set up a template to be able to += / -= and then append to the
    # master history list
    # looks like {stage_name: [# in range 1, # in range 2, etc]}
    stage_history = {}
    for key, value in stages.iteritems():
        stage_history[value[1]] = []
    end_date_entry = get_init_data(doctype, get_blank_stage_template(stages), end_date)
    for key, value in end_date_entry.iteritems():
        stage_history[key].insert(0, value)
    for date in dates:
        next_set = get_changes(doctype, get_blank_stage_template(stages), date)
        for key, value in next_set.iteritems():
            next_value = stage_history[key][0] + next_set[key]
            if next_value >= 0:
                stage_history[key].insert(0, next_value)
            else:
                stage_history[key].insert(0, 0)
    # pop first date still? or pop last date?
    for key, value in stage_history.iteritems():
        value.pop(0)
        value = reversed(value)
    return stage_history


def get_blank_stage_template(stages):
    template = {}
    for key, value in stages.iteritems():
        template[value[1]] = 0
    return template


# need this to rewind from end date rather than fast-forward from start date
def get_changes(doctype, stage_template, date):
    query = frappe.db.sql("""
        select a.changed_doc_name, a.old_value, a.new_value, b.status, b.creation
        from `tab{0}` b
        left outer join `tab{0} Field History` a on a.changed_doc_name = b.name
        where a.fieldname = "status" and (date(a.date) between %s and %s)
        union
        select a.changed_doc_name, a.old_value, a.new_value, b.status, b.creation
        from `tab{0}` b
        right outer join `tab{0} Field History` a on a.changed_doc_name = b.name
        where a.fieldname = "status" and (date(a.date) between %s and %s)
    """.format(doctype),
        (date['start_date'], date['end_date'], date['start_date'],
        date['end_date']), as_dict=True)
    for entry in query:
        if entry['creation'] != None:
            creation = entry['creation'].date()
            if creation >= date['start_date']:
                try:
                    stage_template[entry['status']] -= 1
    #                stage_template[entry['new_value']] -= 1
    #                stage_template[entry['old_value']] -= 1
                except KeyError:
                    try:
                        stage_template[entry['new_value']] -= 1
                    except:
                        stage_template[entry['old_value']] -= 1
                del entry
            else:
                try:
                    stage_template[entry['new_value']] -= 1
                except:
                    pass
                try:
                    stage_template[entry['old_value']] -= 1
                except:
                    pass
        elif entry['old_value'] != None:
            try:
                stage_template[entry['old_value']] += 1
            except KeyError:
                pass
            try:
                stage_template[entry['new_value']] -= 1
            except KeyError:
                pass
        elif entry['old_value'] == None and entry['new_value'] != None:
            try:
                stage_template[entry['new_value']] -= 1
            except KeyError:
                pass
        else:
            try:
                stage_template[entry['status']] -= 1
            except KeyError:
                pass
    return stage_template


def get_init_data(doctype, stage_template, end_date):
    query = frappe.db.sql("""
        select distinct `name`, `status` from `tab{0}`
        where (date(`tab{0}`.creation) < %s)
    """.format(doctype), end_date, as_dict=True)
    for entry in query:
        try:
            stage_template[entry['status']] += 1
        except KeyError:
            pass
    return stage_template



def get_funnel_setup_info():
    funnel_dict = {}
    funnel_info = frappe.get_doc("Sales Funnel Setup").sales_funnel_setup
    for row in funnel_info:
        funnel_dict[str(row.idx)] = (row.document, row.status)
    return funnel_dict


# better way to get montly/quarterly/yearly interval is needed.
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
