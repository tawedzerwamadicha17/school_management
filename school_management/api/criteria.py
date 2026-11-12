"""Pure promotion-criteria logic. No frappe imports, so it is unit-testable anywhere."""


def subject_percentages(rows):
    """rows: dicts with subject, total_score, maximum_score. Several rows per subject are summed."""
    totals = {}
    for r in rows:
        t = totals.setdefault(r["subject"], [0.0, 0.0])
        t[0] += float(r.get("total_score") or 0)
        t[1] += float(r.get("maximum_score") or 0)
    return {c: (s / m * 100 if m else 0.0) for c, (s, m) in totals.items()}


def summarize(rows, pass_mark):
    pcts = subject_percentages(rows)
    n = len(pcts)
    avg = sum(pcts.values()) / n if n else 0.0
    failed = sum(1 for v in pcts.values() if v < pass_mark)
    return {"subjects": n, "average": round(avg, 2), "failed": failed}


def check_criteria(m, p):
    """m: metrics (average, subjects, failed, attendance, fees_outstanding). p: policy mapping.
    Returns the list of failed criteria (empty list = eligible)."""
    failures = []
    if m["average"] < p.get("min_average", 50):
        failures.append("average")
    if m["subjects"] < p.get("min_subjects_passed", 0):
        failures.append("min_subjects")
    if m["failed"] > p.get("max_failed_subjects_allowed", 0):
        failures.append("failed_subjects")
    if p.get("requires_attendance_min") and m.get("attendance", 0) < p["requires_attendance_min"]:
        failures.append("attendance")
    if p.get("requires_fee_clearance") and m.get("fees_outstanding", 0) > 0:
        failures.append("fees")
    if p.get("requires_lms_completion") and m.get("lms_incomplete", 0) > 0:
        failures.append("lms_completion")
    return failures
