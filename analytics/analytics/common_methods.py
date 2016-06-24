from random import *
import frappe
from frappe.core.doctype.doctype.doctype import DocType
from frappe.desk.form.meta import get_meta
from frappe.model.document import Document
import datetime
import json

from .doctype_template import get_change_doctype_json


def dump_doc(doc, method):
    if module_is_versionable(doc):
        doc_dict = frappe.get_doc(doc.doctype, doc.name).as_json()
        storage_doc = {
            "doctype": "Doc History Temp",
            "changed_name": doc.name,
            "is_open": True,
            "old_json_blob": doc_dict
        }
        frappe.client.insert(storage_doc)


def add_updated_doc(doc, method):
    if module_is_versionable(doc):
        doc_dict = doc.as_json()
        filters = json.dumps({"changed_name": doc.name, "is_open": "1"})
        docname = frappe.client.get_value(
            "Doc History Temp",
            "name",
            as_dict = False,
            filters = filters)
        doc = frappe.get_doc("Doc History Temp", docname)
        doc.is_open = False
        doc.new_json_blob = doc_dict
        doc.save()


def sort_temp_entries():
    doc_history_list = frappe.get_list(
        "Doc History Temp",
        filters = json.dumps({
            "is_open": "0",
            }),
        limit_page_length = None
        )
    for name in doc_history_list:
        doc = frappe.get_doc("Doc History Temp", name['name'])
        old_dict = json.loads(doc.old_json_blob)
        new_dict = json.loads(doc.new_json_blob)
        log_field_changes(old_dict, new_dict)
        doc.delete()


def clean_history():
    doctype_list = frappe.get_list("DocType", limit_page_length=None)
    for doctype in doctype_list:
        if "Field History" in doctype['name']:
            changed_doctype = doctype['name'].replace(" Field History", "")
            changed_doc_names = frappe.db.sql("""
                SELECT `changed_doc_name` FROM `tab{0}`
                GROUP BY `changed_doc_name`
                """.format(doctype['name']))
            for name in changed_doc_names:
                try:
                    frappe.get_doc(changed_doctype, name[0])
                except:
                    delete_history(changed_doctype, name[0])


def delete_history_event(doc, method):
    delete_history(doc.doctype, doc.name)


def delete_history(doctype, docname):
    frappe.db.sql("""
        DELETE FROM `tab{0} Field History`
        WHERE `changed_doc_name` = "{1}"
        """.format(doctype, docname))


def module_is_versionable(doc):
    module = doc.meta.module
    try:
        settings = json.loads(
            frappe.model.document.get_doc(
                "Document Versioning Settings", "Document Versioning Settings"
            ).as_dict()['stored_modules'])
        versionable = settings[module]
    except:
        versionable = False
    return versionable


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
