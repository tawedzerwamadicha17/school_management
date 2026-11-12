frappe.listview_settings["Level Progression"] = {
	add_fields: ["outcome"],
	get_indicator(doc) {
		const colors = {
		Promoted: "green",
		Retained: "orange",
		Graduated: "blue",
		};
		const color = colors[doc.outcome];
		return color ? [__(doc.outcome), color, "outcome,=," + doc.outcome] : null;
	},
};
