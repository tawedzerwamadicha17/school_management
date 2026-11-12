frappe.ui.form.on("Promotion Run", {
	refresh(frm) {
		if (!frm.is_new() && ["Draft", "Completed", "Failed"].includes(frm.doc.status)) {
			frm.add_custom_button(__("Run Promotion"), () => {
				frappe.confirm(
					frm.doc.dry_run ? __("Run as dry run?") : __("This will promote eligible students. Continue?"),
					() => frm.call("run").then(() => frm.reload_doc())
				);
			}).addClass("btn-primary");
		}
		if (["Queued", "Running"].includes(frm.doc.status)) {
			frm.dashboard.set_headline(__("In progress, refresh to see results"));
		}
	},
});
