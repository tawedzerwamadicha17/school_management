frappe.ui.form.on("School Management Settings", {
	refresh(frm) {
		frm.add_custom_button(__("Create LMS Users for All Students"), () => {
			frappe.call({
				method: "school_management.api.lms.create_missing_users",
				freeze: true,
			}).then((r) => {
				const m = r.message || { created: [], skipped: {} };
				frappe.msgprint(
					__("{0} students linked to a User, {1} skipped (no email or error)", [
						m.created.length,
						Object.keys(m.skipped).length,
					])
				);
			});
		});
	},
});
