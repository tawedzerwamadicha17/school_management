import frappe
from frappe.model.document import Document


class SchoolFee(Document):

	def validate(self):
		if (self.paid_amount or 0) > (self.amount or 0):
			frappe.throw("Paid Amount cannot exceed Amount")
		self.outstanding_amount = (self.amount or 0) - (self.paid_amount or 0)
