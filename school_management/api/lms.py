import frappe

SAVEPOINT = "school_lms_enroll"


def level_courses(level):
    return frappe.get_all(
        "Level LMS Course", filters={"parent": level, "parenttype": "School Level"}, pluck="course"
    )


def enroll_student(student, level):
    """Enroll the student's linked User in every LMS course mapped to the level.
    Returns {"enrolled": [...], "skipped": [{"course", "reason"}]}. Never raises for a single course."""
    out = {"enrolled": [], "skipped": []}
    user, reason = ensure_student_user(student)
    if not user:
        out["skipped"].append({"course": None, "reason": reason})
        return out

    for course in level_courses(level):
        if frappe.db.exists("LMS Enrollment", {"member": user, "course": course}):
            continue
        frappe.db.savepoint(SAVEPOINT)
        try:
            frappe.get_doc({
                "doctype": "LMS Enrollment", "member": user, "course": course, "member_type": "School Student",
            }).insert(ignore_permissions=True)
            out["enrolled"].append(course)
        except Exception as e:
            # e.g. unpublished or paid course, which LMS only lets admins enroll into
            frappe.db.rollback(save_point=SAVEPOINT)
            frappe.clear_messages()
            out["skipped"].append({"course": course, "reason": str(e)[:140]})
    return out


def incomplete_courses(student, level):
    """Number of the level's LMS courses the student has not completed (progress < 100)."""
    courses = level_courses(level)
    if not courses:
        return 0
    user = frappe.db.get_value("School Student", student, "user")
    if not user:
        return len(courses)
    done = 0
    for course in courses:
        progress = frappe.db.get_value("LMS Enrollment", {"member": user, "course": course}, "progress")
        if progress is not None and progress >= 100:
            done += 1
    return len(courses) - done


def on_student_update(doc, method=None):
    """Student on_update hook: make sure the student has an LMS-ready User, and enroll them
    in the level's courses when current_level is set or changed."""
    try:
        if doc.get("current_level") and doc.has_value_changed("current_level"):
            enroll_student(doc.name, doc.current_level)  # also ensures the User
        elif not doc.get("user"):
            ensure_student_user(doc.name)
        doc.user = frappe.db.get_value("School Student", doc.name, "user")  # keep in-memory doc in sync
    except Exception:
        frappe.log_error(title=f"LMS user/enrollment failed for {doc.name}")


@frappe.whitelist()
def sync_level_enrollments(school_level):
    """Backfill: enroll every active student of the level in the level's LMS courses."""
    frappe.only_for("System Manager")
    students = frappe.get_all("School Student", filters={"current_level": school_level, "enabled": 1}, pluck="name")
    return {s: enroll_student(s, school_level) for s in students}


def _setting(fieldname, default=1):
    value = frappe.db.get_single_value("School Management Settings", fieldname)
    return default if value is None else int(value)


def ensure_student_user(student):
    """Make sure the Student has a User that can log in to LMS (role: LMS Student).
    Creates the User from the Student's email if needed. Returns (user, reason_if_none)."""
    s = frappe.db.get_value(
        "School Student", student, ["user", "student_email_id", "first_name", "middle_name", "last_name"], as_dict=True
    )
    user = s.user
    if not user:
        if not _setting("auto_create_lms_users"):
            return None, "Student has no linked User (auto-creation is off)"
        email = (s.student_email_id or "").strip().lower()
        if not email:
            return None, "Student has no email, so no User can be created"
        if frappe.db.exists("User", email):
            user = email
        else:
            frappe.db.savepoint(SAVEPOINT)
            try:
                frappe.get_doc({
                    "doctype": "User", "email": email, "enabled": 1, "user_type": "Website User",
                    "first_name": s.first_name or email.split("@")[0],
                    "middle_name": s.middle_name, "last_name": s.last_name,
                    "send_welcome_email": _setting("send_welcome_email"),
                    "roles": [{"role": "LMS Student"}],
                }).insert(ignore_permissions=True)
            except Exception as e:
                frappe.db.rollback(save_point=SAVEPOINT)
                frappe.clear_messages()
                return None, f"Could not create User: {str(e)[:120]}"
            user = email
        frappe.db.set_value("School Student", student, "user", user, update_modified=False)

    if not frappe.db.exists("Has Role", {"parent": user, "parenttype": "User", "role": "LMS Student"}):
        frappe.get_doc("User", user).add_roles("LMS Student")
    return user, None


@frappe.whitelist()
def create_missing_users(school_level=None):
    """Backfill: give every Student without a User one, so they can sign in to LMS."""
    frappe.only_for("System Manager")
    filters = {"enabled": 1, "user": ["is", "not set"]}
    if school_level:
        filters["current_level"] = school_level
    created, skipped = [], {}
    for s in frappe.get_all("School Student", filters=filters, pluck="name"):
        user, reason = ensure_student_user(s)
        if user:
            created.append(s)
        else:
            skipped[s] = reason
    return {"created": created, "skipped": skipped}
