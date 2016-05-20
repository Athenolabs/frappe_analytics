# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
from collections import OrderedDict

import frappe
import random
import datetime
import json

from frappe import _

from analytics.analytics.common_methods import get_pallete


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
                stage_values = []
                for a in value:
                    stage_values.insert(0, len(a['docs']))
                ret.append(format_data(key, stage_values, "Lead"))
    if opportunities == '1':
        oppt_stages = {k:v for k, v in funnel_stages.iteritems()
                       if v[0] == "Opportunity"}
        if oppt_stages:
            oppt_data = get_data(oppt_stages, dates, to_date)
            for key, value in oppt_data.iteritems():
                stage_values = []
                for a in value:
                    stage_values.insert(0, len(a['docs']))
                ret.append(format_data(key, stage_values, "Opportunity"))
    if quotations == '1':
        quote_stages = {k:v for k, v in funnel_stages.iteritems()
                        if v[0] == "Quotation"}
        if quote_stages:
            quote_data = get_data(quote_stages, dates, to_date)
            for key, value in quote_data.iteritems():
                stage_values = []
                for a in value:
                    stage_values.insert(0, len(a['docs']))
                ret.append(format_data(key, stage_values, "Quotation"))

    ret = get_colors(ret)

    return {
        "dataset": ret,
        "columns": [str(date['start_date']) for date in dates][::-1]
        }


def get_colors(ret):
    colors = get_pallete(len(ret))
    for idx, entry in enumerate(ret):
        entry['backgroundColor'] = colors[idx]
    return ret


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


def setup_dict_for_data(doctype, stages, dates, end_date):
    data = {}
    for key, value in stages.iteritems():
        data[value[1]] = [
            {'start_date' : date['start_date'],
             'end_date': date['end_date'],
             'docs': [], 'idx': idx} for idx, date in enumerate(dates)
             ]
    data['current'] = [{key: []} for key, value in data.iteritems()]
    current_data = get_init_data(doctype, end_date)
    for row in data['current']:
        row[row.keys()[0]] = [doc for doc in current_data if
                              doc['status'] == row.keys()[0]]
    return data


def get_data(stages, dates, end_date):
    # get idx 0 of tuple (doctype name) from first item of stages dict
    doctype = stages[stages.keys()[0]][0]
    data = setup_dict_for_data(doctype, stages, dates, end_date)
    current_info = data.pop('current', None)
    changes = get_changes(doctype, dates, end_date, stages)
    #print(current_info)
    for key, value in data.iteritems():
        value[0]['docs'] = [entry[entry.keys()[0]] for entry in current_info
                            if entry.keys()[0] == key]
        value[0]['docs'] = value[0]['docs'][0]

#   Move docs with creation before this period into the prev. period,
#   effectively 'deleting' docs created in the current period
#   Then, move docs with a status change in the current period into the
#   'old' status, still in the current period.
#   KEY = STATUS NAME
#   VALUE = LIST OF DATE RANGES
#   ENTRY = DICT OF IDX, START DATE, END DATE, DOCUMENT LIST
#   ROW = DICT OF DOCUMENT - NAME, STATUS, CREATION, OWNER
    for key, value in data.iteritems():
        #print(value)
        for idx, entry in enumerate(value):
            changed_in_period = changes[key][idx][idx]
            if len(changed_in_period) > 0:
                for change in changed_in_period:
                    ch_doc = change.keys()[0]
                    ch_vals = change[ch_doc]
                    for row in entry['docs']:
                        if row['name'] == ch_doc:
                            print len(entry['docs'])
                            try:
                                print(ch_doc, ch_vals)
                                print(idx)
                                data[ch_vals['old_value']][idx]['docs'].append(row)
                            except KeyError:
                                pass
                            entry['docs'] = [doc for doc in entry['docs'] if
                                             doc['name'] != ch_doc]
                            print(len(entry['docs']))
            for row in entry['docs']:
                if row['creation'].date() < entry['start_date']:
                    try:
                        value[idx + 1]['docs'].append(row)
                    except IndexError:
                        pass
    return data


def get_blank_stage_template(stages):
    template = {}
    for key, value in stages.iteritems():
        template[value[1]] = 0
    return template


def get_changes(doctype, dates, end_date, stages):
    ret = {}
    for key, value in stages.iteritems():
        ret[value[1]] = [{idx: None } for idx, date in enumerate(dates)]
    query = frappe.db.sql("""
        select distinct `changed_doc_name`, `old_value`, `new_value`, `date`
        from `tab{0} Field History`
        where `fieldname` = "status" and (date(`date`) <= %s)
    """.format(doctype), end_date, as_dict=True)
    for key, value in ret.iteritems():
        for idx, date in enumerate(dates):
            ret[key][idx][idx] = [
                {entry['changed_doc_name']: {
                    'old_value': entry['old_value'],
                    'new_value': entry['new_value']
                    }
                } for entry in query if
                date['start_date'] <= entry['date'].date() <= date['end_date']
                and entry['new_value'] == key
                ]
    return ret


def get_init_data(doctype, end_date):
    return frappe.db.sql("""
        select distinct `name`, `creation`, `status`, `owner` from `tab{0}`
        where (date(`tab{0}`.creation) <= %s)
    """.format(doctype), end_date, as_dict=True)


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
