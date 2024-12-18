import frappe
from hrms.hr.doctype.employee_checkin.employee_checkin import EmployeeCheckin

class CustomEmployeeCheckin(EmployeeCheckin):
    def validate_distance_from_shift_location(self):
        if not frappe.db.get_single_value("HR Settings", "allow_geolocation_tracking"):
            return

        if not (self.latitude or self.longitude):
            frappe.msgprint(
                _("Latitude and longitude values are missing, but check-in will proceed.")
            )
            return

        assignment_locations = frappe.get_all(
            "Shift Assignment",
            filters={
                "employee": self.employee,
                "shift_type": self.shift,
                "start_date": ["<=", self.time],
                "shift_location": ["is", "set"],
                "docstatus": 1,
            },
            or_filters=[["end_date", ">=", self.time], ["end_date", "is", "not set"]],
            pluck="shift_location",
        )
        if not assignment_locations:
            return

        checkin_radius, latitude, longitude = frappe.db.get_value(
            "Shift Location", assignment_locations[0], ["checkin_radius", "latitude", "longitude"]
        )
        if checkin_radius <= 0:
            return

        distance = get_distance_between_coordinates(latitude, longitude, self.latitude, self.longitude)
        if distance > checkin_radius:
            frappe.throw(
                _("You must be within {0} meters of your shift location to check in.").format(checkin_radius),
                exc=CheckinRadiusExceededError,
            )
