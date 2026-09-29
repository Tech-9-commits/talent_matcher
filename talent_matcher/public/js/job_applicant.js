frappe.ui.form.on("Job Applicant", {
    refresh: function(frm) {
        // Add "Parse Resume with AI" button if applicant is saved
        if (!frm.is_new()) {
            frm.add_custom_button(__("⚡ Parse Resume with AI"), function() {
                frappe.call({
                    method: "talent_matcher.api.parse_applicant_resume",
                    args: {
                        applicant_id: frm.doc.name
                    },
                    freeze: true,
                    freeze_message: __("Extracting text and analyzing skills with NLP..."),
                    callback: function(r) {
                        if (r.message && r.message.status === "success") {
                            frappe.show_alert({
                                message: __("Resume parsed successfully! Skills extracted: {0}", [r.message.skills.join(", ") || "None"]),
                                indicator: "green"
                            });
                            frm.reload_doc();
                        }
                    },
                    error: function(err) {
                        frappe.msgprint({
                            title: __("Parsing Failed"),
                            indicator: "red",
                            message: err.message || __("Could not parse resume attachment. Make sure a .pdf or .docx is attached.")
                        });
                    }
                });
            }, __("Talent AI"));
        }
    }
});
