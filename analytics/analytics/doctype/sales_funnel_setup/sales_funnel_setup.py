# -*- coding: utf-8 -*-
# Copyright (c) 2015, Alec Ruiz-Ramon and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import json

class SalesFunnelSetup(Document):
	pass


@frappe.whitelist()
def get_field_options(doc, field_name):
	doc = json.loads(doc)
	meta = frappe.desk.form.meta.get_meta(doc['document'])
	fields = [field for field in meta.fields]
	options = [field.options for field in fields if field.fieldname == field_name][0]
	return options
