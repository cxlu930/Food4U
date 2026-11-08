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
        self.user_patch = patch.object(db, "current_user", return_value="preferences-test")
        self.user_patch.start()
        self.addCleanup(self.user_patch.stop)
        self.schema_patch = patch.object(db, "_schema_ready", False)
        self.schema_patch.start()
        self.addCleanup(self.schema_patch.stop)
        db.init_db()

    def weekly_summary(self):
        summary = db.get_spending_summary()
        return {key: summary[key] for key in ("budget", "spent", "remaining")}

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
        self.assertEqual(at.number_input[0].value, 100.0)
        at.number_input[0].set_value(80.0)
        at.select_slider[0].set_value(0)
        at.multiselect[0].set_value(["chinese", "japanese"])
        at.multiselect[1].set_value(["savory", "sour"])
        at.multiselect[2].set_value(["peanut"])
        at.button[0].click().run()
        self.assertFalse(at.exception)
        self.assertFalse(at.metric)
        self.assertEqual(self.weekly_summary(), {"budget": 80.0, "spent": 0, "remaining": 80.0})
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
        self.assertEqual(self.weekly_summary(), {"budget": 20.0, "spent": 0, "remaining": 20.0})
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
        self.assertEqual(self.weekly_summary(), {"budget": 20.0, "spent": 25.5, "remaining": -5.5})
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

    def test_monthly_save_reload_and_independent_budget_amounts(self):
        at = self.page()
        self.assertEqual(at.number_input(key="weekly_budget_inline").value, 100.0)
        self.assertEqual(at.number_input(key="monthly_budget_inline").value, 400.0)
        at.number_input(key="weekly_budget_inline").set_value(150.0)
        at.number_input(key="monthly_budget_inline").set_value(650.0)
        at.button[0].click().run()
        period_radio = at.radio[0]
        period_radio.set_value("monthly").run()
        self.assertEqual(db.get_preferences()["budget_period"], "weekly")
        at.button[0].click().run()
        prefs = db.get_preferences()
        self.assertEqual((prefs["budget_period"], prefs["weekly_budget"], prefs["monthly_budget"]), ("monthly", 150.0, 650.0))
        fresh = self.page()
        self.assertEqual(fresh.radio[0].value, "monthly")
        self.assertEqual(fresh.number_input(key="monthly_budget_inline").value, 650.0)
        home = self.page("app.py")
        markup = "".join(element.proto.body for element in home.get("html"))
        self.assertIn("Monthly budget: $650.00", markup)
        self.assertEqual(home.radio[0].value, "monthly")
        home.radio[0].set_value("weekly").run()
        markup = "".join(element.proto.body for element in home.get("html"))
        self.assertIn("Weekly budget: $150.00", markup)
        self.assertEqual(db.get_preferences()["budget_period"], "monthly")
        fresh.number_input(key="monthly_budget_inline").set_value(0.0)
        fresh.button[0].click().run()
        self.assertEqual(db.get_preferences()["monthly_budget"], 0.0)
        self.assertEqual(db.get_preferences()["weekly_budget"], 150.0)
        home = self.page("app.py")
        self.assertFalse(home.exception)
        self.assertIn("No positive budget allocated", "".join(x.proto.body for x in home.get("html")))

    def test_saved_period_survives_navigation_and_repeated_saves(self):
        at = self.page()
        for period in ("monthly", "weekly", "monthly"):
            at.radio(key="preferences_budget_period").set_value(period).run()
            at.button[0].click().run()
            self.assertEqual(db.get_preferences()["budget_period"], period)
            # Another form submission must keep the selection after the saved default changes.
            at.run()
            self.assertEqual(at.radio(key="preferences_budget_period").value, period)
            at.button[0].click().run()
            at.switch_page("app.py").run()
            self.assertFalse(at.exception)
            self.assertEqual(at.button(key="toggle_budget_period").label, period.title())
            self.assertEqual(db.get_preferences()["budget_period"], period)
            at.switch_page("pages/1_Preferences.py").run()
            self.assertEqual(at.radio(key="preferences_budget_period").value, period)

    def test_home_uses_actual_calendar_month_receipts(self):
        db.save_preferences({
            "weekly_budget": 100.0, "monthly_budget": 400.0, "budget_period": "monthly",
            "cuisines": [], "spice_level": 0, "flavor": [], "avoid_tags": [],
        })
        with patch.object(db, "today_vancouver", return_value=date(2026, 11, 7)):
            for day, amount in [("2026-10-31", 999.0), ("2026-11-01", 40.0), ("2026-11-07", 25.0), ("2026-11-30", 35.0), ("2026-12-01", 999.0)]:
                db.save_confirmed_receipt({"store": "Period fixture", "purchase_date": day, "total_price": amount}, [])
            home = self.page("app.py")
            markup = "".join(x.proto.body for x in home.get("html"))
            self.assertIn("$100.00", markup)
            self.assertIn("$300.00", markup)
            self.assertIn("25.0% used", markup)
            self.assertIn("2026-11-01 – 2026-11-30", markup)
            home.radio[0].set_value("weekly").run()
            markup = "".join(x.proto.body for x in home.get("html"))
            self.assertIn("$25.00", markup)
            self.assertIn("$75.00", markup)
            self.assertIn("2026-11-02 – 2026-11-08", markup)

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
