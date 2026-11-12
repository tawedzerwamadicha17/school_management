import frappe
from frappe.model.document import Document


class SchoolAcademicYear(Document):

	def validate(self):
		if self.year_end_date <= self.year_start_date:
			frappe.throw("Year End Date must be after Year Start Date")
