import frappe
from frappe.model.document import Document


class LevelProgression(Document):

	"""Immutable audit record: cannot be edited or deleted once created."""

	def validate(self):
		if not self.is_new():
			frappe.throw("Level Progression records are immutable")

	def on_trash(self):
		frappe.throw("Level Progression records cannot be deleted")
