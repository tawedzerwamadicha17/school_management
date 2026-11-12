app_name = "school_management"
app_title = "School Management"
app_publisher = "Your Name"
app_description = "Levels, promotion policy and automatic level progression"
app_email = "you@example.com"
app_logo_url = "/assets/school_management/images/logo.svg"
app_license = "mit"

required_apps = ["frappe/lms"]
after_install = "school_management.setup.ensure_roles"
after_migrate = "school_management.setup.ensure_roles"

doc_events = {
    "School Student": {"on_update": "school_management.api.lms.on_student_update"},
}


# Shows the app on the desk home / apps screen
add_to_apps_screen = [
    {
        "name": "school_management",
        "logo": "/assets/school_management/images/logo.svg",
        "title": "School Management",
        "route": "/desk/school-management",
        "has_permission": "school_management.setup.has_app_permission",
    }
]
