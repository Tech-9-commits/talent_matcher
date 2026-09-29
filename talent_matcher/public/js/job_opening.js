frappe.ui.form.on("Job Opening", {
    refresh: function(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__("🎯 Match Candidates with AI"), function() {
                show_candidate_matcher_dialog(frm);
            }, __("Talent AI"));
        }
    }
});

function show_candidate_matcher_dialog(frm) {
    let d = new frappe.ui.Dialog({
        title: __("AI Candidate Matcher for: {0}", [frm.doc.job_title]),
        fields: [
            {
                label: __("Number of Candidates (Top K)"),
                fieldname: "top_k",
                fieldtype: "Select",
                options: ["3", "5", "10", "20"],
                default: "5"
            },
            {
                fieldname: "results_html",
                fieldtype: "HTML"
            }
        ],
        primary_action_label: __("Run AI Matching"),
        primary_action: function(values) {
            d.fields_dict.results_html.$wrapper.html(`
                <div class="text-center text-muted my-4">
                    <div class="spinner-border spinner-border-sm text-primary" role="status"></div>
                    <span class="ml-2">${__("Calculating embeddings and evaluating skill fit...")}</span>
                </div>
            `);

            frappe.call({
                method: "talent_matcher.api.match_candidates_for_job",
                args: {
                    job_opening_id: frm.doc.name,
                    top_k: values.top_k
                },
                callback: function(r) {
                    if (r.message && r.message.matches) {
                        render_matching_results(d, r.message.matches);
                    } else {
                        d.fields_dict.results_html.$wrapper.html(`
                            <div class="alert alert-warning mt-3">${__("No matching candidates found.")}</div>
                        `);
                    }
                }
            });
        }
    });

    d.show();
}

function render_matching_results(dialog, matches) {
    if (!matches || matches.length === 0) {
        dialog.fields_dict.results_html.$wrapper.html(`
            <div class="alert alert-info mt-3">${__("No candidates found in the database yet. Try uploading resumes to Job Applicants.")}</div>
        `);
        return;
    }

    let html = `
    <div class="mt-3" style="max-height: 480px; overflow-y: auto;">
        <table class="table table-bordered table-hover">
            <thead class="thead-light">
                <tr>
                    <th style="width: 25%;">${__("Candidate")}</th>
                    <th style="width: 15%; text-align: center;">${__("Fit Score")}</th>
                    <th style="width: 45%;">${__("AI Evaluation & Skills")}</th>
                    <th style="width: 15%; text-align: center;">${__("Action")}</th>
                </tr>
            </thead>
            <tbody>
    `;

    matches.forEach(function(m) {
        let badge_class = m.ai_fit_score >= 75 ? "badge-success" : (m.ai_fit_score >= 50 ? "badge-warning" : "badge-secondary");
        let matched_tags = (m.matched_skills || []).map(s => `<span class="badge badge-success mr-1">${s}</span>`).join(" ");
        let missing_tags = (m.missing_skills || []).map(s => `<span class="badge badge-danger mr-1">${s}</span>`).join(" ");

        html += `
            <tr>
                <td>
                    <strong>${frappe.utils.escape_html(m.candidate_name || "Applicant")}</strong><br>
                    <small class="text-muted">${frappe.utils.escape_html(m.email || "")}</small><br>
                    <small class="text-muted">${frappe.utils.escape_html(m.phone || "")}</small>
                </td>
                <td style="text-align: center; vertical-align: middle;">
                    <h4><span class="badge ${badge_class}">${m.ai_fit_score}%</span></h4>
                    <small class="text-muted">Sim: ${(m.vector_score * 100).toFixed(1)}%</small>
                </td>
                <td>
                    <p class="mb-1" style="font-size: 12px;"><em>${frappe.utils.escape_html(m.executive_summary || "")}</em></p>
                    ${matched_tags ? `<div class="mb-1"><small><strong>Matched:</strong></small> ${matched_tags}</div>` : ""}
                    ${missing_tags ? `<div><small><strong>Missing:</strong></small> ${missing_tags}</div>` : ""}
                </td>
                <td style="text-align: center; vertical-align: middle;">
                    <a href="/app/job-applicant/${encodeURIComponent(m.applicant_id)}" target="_blank" class="btn btn-xs btn-primary">
                        ${__("View Profile")}
                    </a>
                </td>
            </tr>
        `;
    });

    html += `
            </tbody>
        </table>
    </div>
    `;

    dialog.fields_dict.results_html.$wrapper.html(html);
}
