import frappe
from frappe.model.document import Document


class SchoolAcademicTerm(Document):

	def validate(self):
		if self.term_end_date <= self.term_start_date:
			frappe.throw("Term End Date must be after Term Start Date")
