frappe.ui.form.on("School Student", {
	refresh(frm) {
		if (frm.is_new()) return;
		const colors = { Active: "green", Graduated: "blue", Suspended: "orange", Inactive: "gray" };
		frm.page.set_indicator(__(frm.doc.school_status), colors[frm.doc.school_status] || "gray");

		frm.add_custom_button(__("Promotion History"), () =>
			frappe.set_route("List", "Level Progression", { student: frm.doc.name })
		, __("View"));
		frm.add_custom_button(__("Assessment Results"), () =>
			frappe.set_route("List", "School Assessment Result", { student: frm.doc.name })
		, __("View"));
		frm.add_custom_button(__("Fees"), () =>
			frappe.set_route("List", "School Fee", { student: frm.doc.name })
		, __("View"));
	},
});
