import frappe
from frappe.model.document import Document


class SchoolLevel(Document):

	def validate(self):
		if self.level_number < 1:
			frappe.throw("Level Number must be 1 or greater")
