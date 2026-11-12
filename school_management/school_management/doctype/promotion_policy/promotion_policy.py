import frappe
from frappe.model.document import Document


class PromotionPolicy(Document):

	def validate(self):
		for f in ("min_average", "pass_mark", "requires_attendance_min"):
			if not 0 <= (self.get(f) or 0) <= 100:
				frappe.throw(f"{self.meta.get_label(f)} must be between 0 and 100")
