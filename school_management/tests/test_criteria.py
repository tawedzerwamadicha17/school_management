import unittest

from school_management.api.criteria import check_criteria, subject_percentages, summarize

POLICY = {"min_average": 50, "min_subjects_passed": 3, "max_failed_subjects_allowed": 0,
          "requires_attendance_min": 0, "requires_fee_clearance": 0}


def rows(*scores):
    return [{"subject": f"C{i}", "total_score": s, "maximum_score": 100} for i, s in enumerate(scores)]


class TestCriteria(unittest.TestCase):
    def metrics(self, *scores, **extra):
        m = summarize(rows(*scores), 50)
        m.update({"attendance": 100, "fees_outstanding": 0})
        m.update(extra)
        return m

    def test_eligible(self):
        self.assertEqual(check_criteria(self.metrics(60, 70, 80), POLICY), [])

    def test_high_average_but_one_failed_subject_blocks(self):
        self.assertEqual(check_criteria(self.metrics(95, 95, 40), POLICY), ["failed_subjects"])

    def test_low_average_flagged(self):
        self.assertIn("average", check_criteria(self.metrics(30, 55, 55), POLICY))

    def test_too_few_subjects(self):
        self.assertIn("min_subjects", check_criteria(self.metrics(80, 80), POLICY))

    def test_failed_subjects_allowed_by_policy(self):
        p = dict(POLICY, max_failed_subjects_allowed=1)
        self.assertEqual(check_criteria(self.metrics(95, 95, 40), p), [])

    def test_attendance_and_fees_only_when_required(self):
        m = self.metrics(70, 70, 70, attendance=60, fees_outstanding=100)
        self.assertEqual(check_criteria(m, POLICY), [])
        p = dict(POLICY, requires_attendance_min=80, requires_fee_clearance=1)
        self.assertEqual(check_criteria(m, p), ["attendance", "fees"])

    def test_lms_completion_only_when_required(self):
        m = self.metrics(70, 70, 70, lms_incomplete=2)
        self.assertEqual(check_criteria(m, POLICY), [])
        self.assertEqual(check_criteria(m, dict(POLICY, requires_lms_completion=1)), ["lms_completion"])

    def test_multiple_rows_per_course_are_summed(self):
        r = [{"subject": "M", "total_score": 20, "maximum_score": 40},
             {"subject": "M", "total_score": 30, "maximum_score": 60}]
        self.assertEqual(subject_percentages(r), {"M": 50.0})

    def test_no_results(self):
        m = summarize([], 50)
        self.assertEqual(m, {"subjects": 0, "average": 0.0, "failed": 0})


if __name__ == "__main__":
    unittest.main()
