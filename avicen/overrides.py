import frappe
from frappe import _
from frappe.utils import add_days
from frappe.utils import add_days, get_link_to_form

from hrms.hr.doctype.employee_checkin.employee_checkin import EmployeeCheckin 
from hrms.hr.doctype.shift_request.shift_request import ShiftRequest 
from hrms.hr.doctype.shift_assignment.shift_assignment import has_overlapping_timings


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
                _("You must be within {0} meters of your shift location to check in.").format(checkin_radius)
            )


class CustomShiftRequest(ShiftRequest):
    def throw_overlap_error(self, shift_details):
        pass

    def on_submit(self):
        if self.status not in ["Approved", "Rejected"]:
            frappe.throw(_("Only Shift Request with status 'Approved' and 'Rejected' can be submitted"))

        if self.status == "Approved":
            overlapping_assignments = frappe.get_all(
                "Shift Assignment",
                filters={
                    "employee": self.employee,
                    "docstatus": 1,
                    "start_date": ["<=", self.from_date],
                    "end_date": ["in", [None, ""]]
                },
                fields=["name", "start_date"]
            )

            for assignment in overlapping_assignments:
                assignment_doc = frappe.get_doc("Shift Assignment", assignment.name)
                new_end_date = add_days(self.from_date, -1)
                assignment_doc.end_date = new_end_date
                assignment_doc.flags.ignore_validate = True
                assignment_doc.flags.ignore_mandatory = True
                assignment_doc.save()
                assignment_doc.submit()
                
                frappe.msgprint(
                    _("✅ Previous Shift Assignment {0} updated with end date {1}").format(
                        get_link_to_form("Shift Assignment", assignment.name),
                        frappe.bold(new_end_date)
                    )
                )

            assignment_doc = frappe.new_doc("Shift Assignment")
            assignment_doc.company = self.company
            assignment_doc.shift_type = self.shift_type
            assignment_doc.employee = self.employee
            assignment_doc.start_date = self.from_date
            if self.to_date:
                assignment_doc.end_date = self.to_date
            assignment_doc.shift_request = self.name
            assignment_doc.flags.ignore_permissions = True
            assignment_doc.insert()
            assignment_doc.submit()

            frappe.msgprint(
                _("✅ New Shift Assignment {0} created for Employee {1}").format(
                    get_link_to_form("Shift Assignment", assignment_doc.name),
                    frappe.bold(self.employee)
                )
            )
