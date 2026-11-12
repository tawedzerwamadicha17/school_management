import json
from collections import Counter

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate

from school_management.api.criteria import check_criteria, summarize
from school_management.api.lms import enroll_student, incomplete_courses

SAVEPOINT = "school_promotion"
NOT_ELIGIBLE_STATUS = ["Graduated", "Inactive", "Suspended"]


def get_policy(level, academic_term):
    """Latest Promotion Policy for the level that is effective for the term's academic year."""
    year = frappe.db.get_value("School Academic Term", academic_term, "academic_year")
    term_start = getdate(frappe.db.get_value("School Academic Year", year, "year_start_date"))
    best = None
    for p in frappe.get_all("Promotion Policy", filters={"school_level": level}, fields=["*"]):
        s = frappe.db.get_value("School Academic Year", p.effective_from_year, "year_start_date") if p.effective_from_year else None
        s = getdate(s) if s else getdate("1900-01-01")
        if s <= term_start and (best is None or s > best[0]):
            best = (s, p)
    if not best:
        frappe.throw(_("No Promotion Policy found for level {0}").format(level))
    return best[1]


def collect_metrics(student, academic_term, policy):
    rows = frappe.get_all(
        "School Assessment Result",
        filters={"student": student, "academic_term": academic_term, "docstatus": 1},
        fields=["subject", "total_score", "maximum_score"],
    )
    m = summarize(rows, flt(policy.pass_mark))

    start, end = frappe.db.get_value("School Academic Term", academic_term, ["term_start_date", "term_end_date"])
    att = frappe.get_all(
        "School Attendance",
        filters={"student": student, "docstatus": 1, "attendance_date": ["between", [start, end]]},
        fields=["status"],
    )
    # No attendance records counts as 0%: only matters when a minimum is required
    m["attendance"] = (sum(1 for a in att if a.status == "Present") / len(att) * 100) if att else 0.0

    m["fees_outstanding"] = flt(frappe.db.sql(
        "select coalesce(sum(outstanding_amount), 0) from `tabSchool Fee` "
        "where student=%s and academic_term=%s and docstatus=1",
        (student, academic_term),
    )[0][0])
    m["lms_incomplete"] = incomplete_courses(student, policy.school_level)
    return m


def close_enrollments(student, level):
    """Deactivate the student in School Classes of the old level (rows are kept, not deleted)."""
    groups = frappe.get_all("School Class", filters={"school_level": level}, pluck="name")
    if groups:
        frappe.db.set_value("School Class Student", {"parent": ["in", groups], "student": student}, "active", 0)


def promote_student(student, academic_term, dry_run=False, override=False, reason=None):
    """Evaluate and (unless dry_run) apply the outcome for one student. Atomic per student."""
    current = frappe.db.get_value("School Student", student, "current_level")
    if not current:
        frappe.throw(_("Student {0} has no Current Level").format(student))

    if frappe.db.exists("Level Progression", {
        "student": student, "academic_term": academic_term, "outcome": ["in", ["Promoted", "Graduated"]],
    }):
        frappe.throw(_("Student {0} was already processed for {1}").format(student, academic_term))

    number = frappe.db.get_value("School Level", current, "level_number")
    next_level = frappe.db.get_value("School Level", {"level_number": number + 1}, "name")

    policy = get_policy(current, academic_term)
    metrics = collect_metrics(student, academic_term, policy)
    failures = check_criteria(metrics, policy)

    if failures and not override:
        outcome, decision = "Retained", "Auto"
    else:
        outcome = "Promoted" if next_level else "Graduated"
        decision = "Conditional" if failures else "Auto"
        if failures and not (reason or "").strip():
            frappe.throw(_("A reason is required to override failed criteria"))

    result = {
        "student": student, "outcome": outcome, "from_level": current,
        "to_level": next_level if outcome == "Promoted" else current,
        "average": metrics["average"], "failures": failures, "message": ", ".join(failures),
    }
    if dry_run:
        return result

    frappe.db.savepoint(SAVEPOINT)
    try:
        frappe.get_doc({
            "doctype": "Level Progression", "student": student,
            "from_level": current, "to_level": result["to_level"], "academic_term": academic_term,
            "average_score": metrics["average"], "outcome": outcome, "decision_type": decision,
            "reason": reason if failures else None,
            "overridden_by": frappe.session.user if failures and override else None,
            "conditional_flags": json.dumps({"failed": failures, "metrics": metrics}) if failures else None,
        }).insert(ignore_permissions=True)

        if outcome == "Promoted":
            frappe.db.set_value("School Student", student, "current_level", next_level)
            close_enrollments(student, current)
        elif outcome == "Graduated":
            frappe.db.set_value("School Student", student, "school_status", "Graduated")
            close_enrollments(student, current)
    except Exception:
        frappe.db.rollback(save_point=SAVEPOINT)
        raise

    if outcome == "Promoted":
        # Best effort: a missing user or unpublished course must not undo the promotion
        try:
            result["lms"] = enroll_student(student, next_level)
        except Exception:
            frappe.log_error(title=f"LMS enrollment failed for {student}")
    return result


@frappe.whitelist()
def promote_one(student, academic_term, dry_run=0, override=0, reason=None):
    frappe.only_for("System Manager")
    return promote_student(student, academic_term, cint(dry_run), cint(override), reason)


@frappe.whitelist()
def batch_promote(school_level, academic_term, dry_run=0):
    """Process every eligible student in a level. Each student succeeds or fails independently.
    For large levels use a Promotion Run document, which runs this in a background job."""
    frappe.only_for("System Manager")
    dry_run = cint(dry_run)
    students = frappe.get_all(
        "School Student",
        filters={"current_level": school_level, "enabled": 1, "school_status": ["not in", NOT_ELIGIBLE_STATUS]},
        fields=["name", "student_name"],
        order_by="name",
    )
    results = []
    for s in students:
        try:
            r = promote_student(s.name, academic_term, dry_run=dry_run)
            if not dry_run:
                frappe.db.commit()
        except Exception as e:
            frappe.db.rollback()
            r = {"student": s.name, "outcome": "Error", "average": 0, "failures": [], "message": str(e)[:140]}
        r["student_name"] = s.student_name
        results.append(r)
    return results


def execute_run(run_name):
    """Background job behind Promotion Run."""
    run = frappe.get_doc("Promotion Run", run_name)
    run.db_set("status", "Running")
    frappe.db.commit()
    try:
        results = batch_promote(run.school_level, run.academic_term, run.dry_run)
        run.reload()
        run.set("items", [])
        for r in results:
            run.append("items", {
                "student": r["student"], "student_name": r.get("student_name"),
                "outcome": r["outcome"], "average": r.get("average"), "message": r.get("message"),
            })
        counts = Counter(r["outcome"] for r in results)
        prefix = "DRY RUN: " if run.dry_run else ""
        run.summary = prefix + ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())) or prefix + "No eligible students"
        run.status = "Completed"
        run.save(ignore_permissions=True)
    except Exception:
        frappe.db.rollback()
        frappe.log_error(title=f"Promotion Run {run_name} failed")
        frappe.db.set_value("Promotion Run", run_name, "status", "Failed")
    frappe.db.commit()
