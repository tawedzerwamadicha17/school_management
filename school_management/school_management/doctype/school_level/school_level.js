frappe.ui.form.on("School Level", {
	refresh(frm) {
		if (frm.is_new() || !(frm.doc.lms_courses || []).length) return;
		frm.add_custom_button(__("Enroll Students in LMS Courses"), () => {
			frappe.call({
				method: "school_management.api.lms.sync_level_enrollments",
				args: { school_level: frm.doc.name },
				freeze: true,
			}).then((r) => {
				const n = Object.values(r.message || {}).reduce((a, x) => a + x.enrolled.length, 0);
				frappe.msgprint(__("{0} new enrollments created", [n]));
			});
		});
	},
});
