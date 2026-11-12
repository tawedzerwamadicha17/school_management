frappe.listview_settings["School Student"] = {
	add_fields: ["school_status"],
	get_indicator(doc) {
		const colors = {
		Active: "green",
		Graduated: "blue",
		Suspended: "orange",
		Inactive: "gray",
		};
		const color = colors[doc.school_status];
		return color ? [__(doc.school_status), color, "school_status,=," + doc.school_status] : null;
	},
};
