import frappe
from frappe.model.document import Document


class PromotionRun(Document):

	@frappe.whitelist()
	def run(self):
		frappe.only_for("System Manager")
		if self.status in ("Queued", "Running"):
			frappe.throw("This run is already in progress")
		self.db_set("status", "Queued")
		frappe.enqueue("school_management.api.promotion.execute_run",
			queue="long", timeout=3600, run_name=self.name)
