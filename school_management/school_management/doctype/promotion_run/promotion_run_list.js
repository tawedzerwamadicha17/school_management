frappe.listview_settings["Promotion Run"] = {
	add_fields: ["status"],
	get_indicator(doc) {
		const colors = {
		Draft: "gray",
		Queued: "orange",
		Running: "yellow",
		Completed: "green",
		Failed: "red",
		};
		const color = colors[doc.status];
		return color ? [__(doc.status), color, "status,=," + doc.status] : null;
	},
};
