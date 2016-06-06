## Powerful Analytics for the Frappe Framework

NOTE: THIS APP IS NOT PRODUCTION-READY. IT IS EXPECTED TO INSTALL BUT IS IS STILL IN
THOUROUGH TESTING AND BUG FIXING STATE

This app is supposed to do two things:

**1.) Enable field history tracking**

Let's say you have a price of an item and change that price. The App will enable 
you to see the entire history of this particular items price.

**2.) Provide advanced reports based on the data it creates.**

It's important to note that the reporting based on field history will not
be helpful for events pre-installation. The data doesn't exist yet. So, despite
not having many reports right now, you'll want to start building up your data
for later use!!

Field history tracking is enabled on a module-by-module basis in the
"Document Versioning Settings" doctype. Upon changing a document in an enabled
module, the changed field(s) are sorted into a custom doctype named
[doctype] Field History. Again, if in doubt, enable a module. Great use-cases
are CRM, Selling, Projects, Manufacturing, Buying, and Accounts. I would not
enable it for modules like Core, Email, etc.

Reporting is coming soon....here are some potential reports!
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
