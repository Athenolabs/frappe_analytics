from random import *
import frappe
from frappe.client import get_list
from frappe.core.doctype.doctype.doctype import DocType
from frappe.desk.form.meta import get_meta
from frappe.model.document import Document
import ast
import datetime
import json

from .doctype_template import get_change_doctype_json


# IMPORTANT: THIS METHOD IS HOOOKED INTO
def sort_temp_entries(doc, method):
    changed_fields = get_list("Doc History Temp", limit_page_length=None)
    for name in changed_fields:
        doc = frappe.get_doc("Doc History Temp", name['name'])
        old_dict = json.loads(doc.json_blob)
        if (len(frappe.client.get_list(
            old_dict['doctype'], filters={'name': old_dict['name']}
            )) > 0):
            new_dict = frappe.client.get(old_dict['doctype'], old_dict['name'])
        else:
            new_dict = None
        log_field_changes(old_dict, new_dict)
        doc.delete()


def clean_history():
    doctypes = frappe.client.get_list("DocType", limit_page_length=None)
    for doctype in doctypes:
        if "Field History" not in doctype['name']:
            docnames = get_doc_names(doctype['name'])
            for entry in docnames:
                try:
                    frappe.client.get(doctype['name'], entry['changed_doc_name'])
                except:
                    try:
                        frappe.client.delete(
                            (doctype['name'] + " Field History"),
                            entry['name']
                            )
                    except:
                        pass


def get_doc_names(docname):
    try:
        return frappe.db.sql("""
            select `name`, `changed_doc_name` from `tab{0} Field History`
            group by `changed_doc_name`
        """.format(docname), as_dict=True)
    except:
        return []


def dump_pre_save_doc(doc, method):
# deciding to dump json strung here after a date hook to avoid having to use
# ast later down the line
    if module_is_versionable(doc):
        doc_dict = date_hook(doc.as_dict())
        try:
            doc_dict = json.dumps(doc_dict)
        except:
            frappe.throw(doc_dict)
        storage_doc = {
            "doctype": "Doc History Temp",
            "json_blob": doc_dict
        }
        history_doc = frappe.client.insert(storage_doc)


def module_is_versionable(doc):
    module = doc.meta.module
    try:
        settings = json.loads(
            frappe.model.document.get_doc(
                "Document Versioning Settings", "Document Versioning Settings"
            ).as_dict()['stored_modules'])
    except:
        settings = {}
        settings[module] = False
    return settings[module]


def log_field_changes(new_dict, old_dict):
    ignored_fields = ["modified", "creation", "__onload"]
    for k, v in new_dict.iteritems():
        if k not in ignored_fields:
            if old_dict == None:
                make_doc(new_dict, old_dict, k)
            else:
                try:
                    old_value = old_dict[k]
                except KeyError:
                    old_value = None
                if new_dict[k] != old_value:
                    make_doc(new_dict, old_dict, k)


def make_doc(new_dict, old_dict, k):
    doc = prep_doc(new_dict, old_dict, k)
    if type(doc['new_value']) is not list:
        make_doctype_maybe(doc['doctype'])
        history = Document(doc)
        history.insert()
    elif doc['old_value'] != None:
        for idx, entry in enumerate(doc['old_value']):
            log_field_changes(doc['new_value'][idx], entry)


def prep_doc(new_dict, old_dict, k):
    ret =  {
        "doctype": get_analytics_doctype_name(new_dict['doctype']),
        "changed_doctype": new_dict['doctype'],
        "changed_doc_name": new_dict['name'],
        "fieldname": k,
        "new_value": new_dict[k],
        "modified_by_user": new_dict["modified_by"],
        "date": new_dict["modified"]
        }
    if old_dict != None:
        ret["old_value"] = old_dict[k]
    else:
        ret["old_value"] = None
    return ret



def get_analytics_doctype_name(doctype):
    return (doctype + " Field History")


def make_doctype_maybe(doctype_name):
    """ Makes doctype for Analytics app, if necessary"""
    try:
        dt = frappe.get_list(
            "DocType",
            filters={"name": doctype_name},
            ignore_permissions=True
            )[0]
    except:
        dt = DocType(get_change_doctype_json(doctype_name))
        dt.insert(ignore_permissions=True)


def date_hook(dictionary):
    for key, value in dictionary.iteritems():
        if str(type(value)) == "<type 'datetime.datetime'>":
            dictionary[key] = datetime.datetime.strftime(value, "%m-%d-%Y %H:%M:%S")
        elif str(type(value)) == "<type 'datetime.date'>":
            dictionary[key] = datetime.datetime.strftime(value, "%m-%d-%Y")
        elif str(type(value)) == "<type 'list'>":
            dictionary[key] = [date_hook(entry) for entry in value]
        elif type(value) == "<type 'dict'>":
            dictionary[key] = date_hook(value)
    return dictionary


def get_pallete(num):
    pallete = []
    h, s, v = random()*6, .5, 243.2
    for i in range(num):
        h += 3.708
        pallete.append('#'+'%02x'*3%((v,v-v*s*abs(1-h%2),v-v*s)*3)[5**int(h)/3%3::int(h)%2+1][:3])
        if i % 5/4:
            s += .1
            v -= 51.2
    return pallete
