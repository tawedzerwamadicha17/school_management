import frappe
from frappe.model.document import Document


class SchoolStudent(Document):

	def validate(self):
		self.student_name = " ".join(x for x in (self.first_name, self.middle_name, self.last_name) if x)
		if self.student_email_id:
			self.student_email_id = self.student_email_id.strip().lower()
