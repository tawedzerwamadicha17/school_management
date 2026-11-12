# School Management (Frappe)

Phase 1: School Level, Promotion Policy, Level Progression (immutable audit), Promotion Run, promotion engine.
Standalone: requires only Frappe and LMS (v15). It ships its own School Student, Academic Year/Term, Subject, Assessment Result, Attendance, Fee and Class doctypes, so ERPNext and Education are not needed.

LMS bridge: every Student is given a User (from the student email, role LMS Student) so they can sign in to LMS;
toggle this under School Management Settings. Map LMS Courses to each School Level. Students are auto-enrolled in their level's courses when
`current_level` is set or they are promoted. A Promotion Policy can require 100% LMS completion.

## Install
    cd apps && unzip school_management.zip   # or copy the folder into apps/
    bench --site <site> install-app school_management
    bench --site <site> migrate

## Use
1. Create School Levels (1..N) and one Promotion Policy per level.
2. Create School Students (and Academic Years/Terms, Subjects), then set School Student > Current Level.
3. Create a Promotion Run (level + term), tick Dry Run first, press Run Promotion.
# school_management
# school_management
