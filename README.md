## [BETA] Powerful Analytics for the Frappe Framework

**1.) Enable tracking of field-level events**

Let's say you have an Item Price, and change that price. Want to see what it used to be? Now you can.

**2.) Empower business intelligence through strong reporting and analytics.**

Field history tracking is enabled on a module-by-module basis in the
"Document Versioning Settings" doctype. Upon changing a document in an enabled
module, the changed field(s) are sorted into a custom doctype named
[doctype] Field History. Great use-cases include CRM, Selling, Projects, Manufacturing, Buying, and Accounts. I would not enable it for modules like Core, Email, etc.

Some potential reports:
  - See your sales funnel and how quickly leads progress by 'status' field
  - With an 'estimated close date' field, see how many opportunities close
    or push in a given time period
  - Create burndown charts for project tasks
  - Track conversion rates through lead and opportunity stages - i.e.
    10% of Prospects become MQL's, 23% of MQL's become SQL's, etc.


### Contributing

If you have a report you'd like to have, or a better method for the backend,
send a pull request!

Reports should be created as a "page" in the analytics app - and should be kept
plug-and-play with the data provided by Frappe and ERPNext.

If your reports will require a custom field that isn't provided, set it up with
fixtures.


#### License

MIT
