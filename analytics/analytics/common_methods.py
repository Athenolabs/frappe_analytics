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


def delete_history(doc, method):
    if doc.doctype is not "Doc History Temp":
        frappe.msgprint("not doc history temp")
        history_doctype = get_analytics_doctype_name(doc.doctype)
        history_list = frappe.client.get_list(
            history_doctype, filters={"changed_doc_name": doc.name}
            )
    if history_list:
        for item in history_list:
            frappe.delete_doc(history_doctype, item['name'])


def dump_pre_save_doc(doc, method):
    if is_versionable(doc):
        doc_dict = date_hook(doc.as_dict())
        print("DICT HERE")
        print(doc_dict)
        storage_doc = {
            "doctype": "Doc History Temp",
            "json_blob": doc_dict
        }
        history_doc = frappe.client.insert(storage_doc)


def sort_pre_save_doc(doc, method):
    if is_versionable(doc):
        sort_temp_entries()


def is_versionable(doc):
	# slightly odd here, may want to refactor.
	# since custom field is for DISABLING versioning,
	# check if the doc is not disabled (dbl negative)
    if check_if_module_is_versionable(doc):# and not check_if_doc_is_disabled(doc):
        return True
    else:
        return False


# relic from when was integrated with framework and property_setter
#def check_if_doc_is_disabled(doc):
#	filters = json.dumps({
#		"doc_type": doc.doctype,
#		"property": 'disable_versioning'
#	})
#	try:
#		properties = frappe.client.get("Property Setter", filters=filters)
#		value = properties['value']
#	except:
#		# no property setter for given document, so defaults to False
#		value = False
#	return value


def check_if_module_is_versionable(doc):
    module = doc.meta.module
    try:
        settings = json.loads(
            frappe.model.document.get_doc(
                "Document Versioning Settings", "Document Versioning Settings"
            ).as_dict()['stored_modules'])
    except KeyError:
        settings = {}
        settings[module] = False
    return settings[module]


def log_field_changes(new_dict, old_dict):
    ignored_fields = ["modified", "creation", "__onload"]
    for k, v in old_dict.iteritems():

# these are commented out b/c they're causing issues with datetimes
# string comparison is wrong, says they're changed b/c Y-m-d != m-d-Y
#        if type(new_dict[k]) != type(old_dict[k]):
#            new_dict[k] = str(new_dict[k])
#            old_dict[k] = str(old_dict[k])

        if new_dict[k] != old_dict[k] and k not in ignored_fields:
                doc = {
                    "doctype": get_analytics_doctype_name(old_dict['doctype']),
                    "changed_doctype": new_dict['doctype'],
                    "changed_doc_name": new_dict['name'],
                    "fieldname": k,
                    "old_value": old_dict[k],
                    "new_value": new_dict[k],
                    "modified_by_user": new_dict["modified_by"],
                    "date": new_dict["modified"]
                    }
                # can't save old/new value as list -> means child table.
                if type(doc['old_value']) is not list:
                    make_doctype_maybe(doc['doctype'])
                    history = Document(doc)
                    history.insert()
                else:
                    for idx, entry in enumerate(doc['old_value']):
                        log_field_changes(doc['new_value'][idx], entry)


def insert_new_doc(dictionary):
    ignored_fields = ["modified", "creation", "__onload"]
    for k, v in dictionary.iteritems():
        if k not in ignored_fields:
            doc = {
                "doctype": get_analytics_doctype_name(dictionary['doctype']),
                "changed_doctype": dictionary['doctype'],
                "changed_doc_name": dictionary['name'],
                "fieldname": k,
                "old_value": None,
                "new_value": dictionary[k],
                "modified_by_user": dictionary["modified_by"],
                "date": dictionary["modified"]
                }
            if type(doc['new_value']) is not list:
                make_doctype_maybe(doc['doctype'])
                history = Document(doc)
                history.insert()
            else:
                for idx, entry in enumerate(doc['new_value']):
                    insert_new_doc(doc['new_value'][idx])

def sort_changed_field(doc):
    """ Gets changed field from doc hook, sorts into correct table, and
    removes doc from Frappe's Changed Fields table"""
    to_doctype_name = get_analytics_doctype_name(doc.changed_doctype)
    make_doctype_maybe(to_doctype_name)
    new_doc = Document(sanitize_document(doc, to_doctype_name))
    new_doc.save()
    doc.delete()


def get_analytics_doctype_name(doctype):
    return (doctype + " Field History")


#def sanitize_document(from_doc, to_doctype):
#    """ Sanitizes document to only contain fields in destination doctype, plus
#    the destination doctype"""
#    meta = get_meta(to_doctype)
#    fields = [field.fieldname for field in meta.fields]
#    doc_dict = frappe.client.get(from_doc)
#    sanitized_doc =  {k:v for k, v in doc_dict.iteritems() if k in fields}
#    sanitized_doc['doctype'] = to_doctype
#    return sanitized_doc


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


def sort_temp_entries(doc, method):
    changed_fields = get_list(
        "Doc History Temp", limit_page_length=None
        )

    for name in changed_fields:
        doc = frappe.get_doc("Doc History Temp", name['name'])
        old_dict = ast.literal_eval(doc.json_blob)
	try:
	    new_dict = frappe.client.get(old_dict['doctype'], old_dict['name'])
#       WHY DOES THIS HAVE TO BE BACKWARDS
            log_field_changes(old_dict, new_dict)
            doc.delete()
	except: # new doc, does not exist yet
	    pass

def del_items(dictionary):
    if "items" in dictionary.keys():
        del dictionary['items']


def date_hook(dictionary):
    for key, value in dictionary.iteritems():
        if str(type(value)) == "<type 'datetime.datetime'>":
            print(key, value)
            dictionary[key] = datetime.datetime.strftime(value, "%m-%d-%Y %H:%M:%S")
    return dictionary
