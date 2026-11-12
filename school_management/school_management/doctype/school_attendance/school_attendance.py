import frappe
from frappe.model.document import Document


class SchoolAttendance(Document):

	def validate(self):
		if frappe.db.exists("School Attendance", {"student": self.student, "attendance_date": self.attendance_date,
				"docstatus": 1, "name": ["!=", self.name]}):
			frappe.throw("Attendance is already marked for this student on this date")
