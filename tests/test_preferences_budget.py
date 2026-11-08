"""A-module integration checks. All writes go to a disposable SQLite database."""
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from unittest.mock import patch

import db
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


class PreferencesBudgetTests(TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path_patch = patch.object(db, "DB_PATH", str(Path(self.temporary.name) / "test.db"))
        self.path_patch.start()
        self.addCleanup(self.path_patch.stop)
        self.seed_patch = patch.object(db, "SEED_SAMPLE_DATA", False)
        self.seed_patch.start()
        self.addCleanup(self.seed_patch.stop)
        db.init_db()

    def save_preferences(self, budget=80.0):
        preferences = {
            "weekly_budget": budget, "cuisines": ["chinese", "japanese"],
            "spice_level": 0, "flavor": ["savory", "sour"], "avoid_tags": ["peanut"],
        }
        db.save_preferences(preferences)
        return preferences

    def page(self, path="pages/1_Preferences.py"):
        at = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)
        self.assertFalse(at.exception, str(at.exception))
        if path != "app.py":
            at.switch_page(path).run(timeout=30)
        self.assertFalse(at.exception, str(at.exception))
        return at

    def test_preferences_save_reload_zero_and_immediate_dashboard(self):
        at = self.page()
        self.assertEqual(at.number_input[0].value, 0.0)
        at.number_input[0].set_value(80.0)
        at.select_slider[0].set_value(0)
        at.multiselect[0].set_value(["chinese", "japanese"])
        at.multiselect[1].set_value(["savory", "sour"])
        at.multiselect[2].set_value(["peanut"])
        at.button[0].click().run()
        self.assertFalse(at.exception)
        self.assertFalse(at.metric)
        self.assertEqual(db.get_spending_summary(), {"budget": 80.0, "spent": 0, "remaining": 80.0})
        prefs = db.get_preferences()
        self.assertEqual(prefs["spice_level"], 0)
        self.assertEqual(prefs["flavor"], ["savory", "sour"])
        refreshed = self.page()
        self.assertEqual(refreshed.number_input[0].value, 80.0)
        self.assertEqual(refreshed.select_slider[0].value, 0)
        self.assertEqual(refreshed.multiselect[0].value, ["chinese", "japanese"])
        self.assertEqual(refreshed.multiselect[1].value, ["savory", "sour"])
        self.assertEqual(refreshed.multiselect[2].value, ["peanut"])
        refreshed.number_input[0].set_value(0.0)
        refreshed.button[0].click().run()
        self.assertEqual(db.get_preferences()["weekly_budget"], 0.0)
        home = self.page("app.py")
        markup = "".join(element.proto.body for element in home.get("html"))
        self.assertIn("Weekly budget: $0.00", markup)
        self.assertNotIn("Using default weekly budget", markup)

    def test_receipt_save_updates_spent_week_filter_duplicate_and_overspend(self):
        self.save_preferences(20.0)
        self.assertEqual(db.get_spending_summary(), {"budget": 20.0, "spent": 0, "remaining": 20.0})
        receipt = {"store": "A integration fixture", "purchase_date": date.today().isoformat(), "total_price": 25.5}
        items = [
            {"ingredient_name": "rice", "raw_text": "Rice", "price": 10.0,
             "quantity": 1.0, "unit": "kg", "recognized": True},
            {"ingredient_name": None, "raw_text": "Unknown product", "price": 15.5,
             "quantity": 1.0, "unit": None, "recognized": False},
        ]
        self.assertTrue(db.save_confirmed_receipt(receipt, items))
        self.assertFalse(db.save_confirmed_receipt(receipt, items))
        monday = date.today() - timedelta(days=date.today().weekday())
        for offset in [-1, 7]:
            other = {"store": "Outside current week", "purchase_date": (monday + timedelta(days=offset)).isoformat(), "total_price": 100.0}
            db.save_confirmed_receipt(other, [])
        self.assertEqual(db.get_spending_summary(), {"budget": 20.0, "spent": 25.5, "remaining": -5.5})
        at = self.page()
        self.assertFalse(at.metric)
        self.assertFalse(at.warning)
        # A new connection and a new page session still see the saved receipt.
        refreshed = self.page()
        self.assertFalse(refreshed.metric)
        self.assertEqual(db.get_spending_summary()["spent"], 25.5)
        home = self.page("app.py")
        markup = "".join(element.proto.body for element in home.get("html"))
        self.assertIn("$25.50", markup)
        self.assertIn("$-5.50", markup)
        self.assertTrue(any("$5.50 over" in warning.value for warning in home.warning))
        self.assertIn("127.5% used", markup)
        self.assertIn('style="width:100.00%"', markup)
        self.assertEqual(len(db.get_pantry_items()), 1)

    def test_home_progress_and_empty_state_use_saved_data(self):
        self.save_preferences(100.0)
        def home_markup():
            at = self.page("app.py")
            return "".join(element.proto.body for element in at.get("html"))
        empty = home_markup()
        self.assertIn("No saved spending this week.", empty)
        self.assertIn("0.0% used", empty)
        self.assertNotIn("Chart illustrative only", empty)
        self.assertIn("Daily breakdown unavailable", empty)
        receipt = {"store": "Progress fixture", "purchase_date": date.today().isoformat(), "total_price": 25.0}
        db.save_confirmed_receipt(receipt, [])
        markup = home_markup()
        self.assertIn("25.0% used", markup)
        self.assertIn('style="width:25.00%"', markup)
        self.assertIn("$75.00", markup)
        self.save_preferences(0.0)
        zero = home_markup()
        self.assertIn("No positive budget allocated", zero)
        self.assertNotIn('role="progressbar"', zero)
        self.assertIn("$-25.00", zero)

    def test_unsaved_edits_and_failed_receipt_do_not_change_totals(self):
        self.save_preferences(73.33)
        at = self.page()
        at.number_input[0].set_value(200.0).run()
        self.assertEqual(db.get_preferences()["weekly_budget"], 73.33)
        self.assertFalse(at.metric)
        self.assertEqual(db.get_spending_summary()["budget"], 73.33)
        with self.assertRaises(ValueError):
            db.save_confirmed_receipt({"store": "Invalid date", "purchase_date": "invalid", "total_price": 40.0}, [])
        self.assertEqual(db.get_spending_summary()["spent"], 0)
        self.assertEqual(db.get_spending_summary()["remaining"], 73.33)


if __name__ == "__main__":
    main()
