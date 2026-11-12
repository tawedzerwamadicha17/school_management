import frappe
from frappe.model.document import Document


class SchoolAssessmentResult(Document):

	def validate(self):
		if (self.maximum_score or 0) <= 0:
			frappe.throw("Maximum Score must be greater than 0")
		if not 0 <= (self.total_score or 0) <= self.maximum_score:
			frappe.throw("Total Score must be between 0 and Maximum Score")
