import frappe
import requests
import json
from datetime import datetime, timedelta

@frappe.whitelist()
def fetch_and_create_checkins():
    today = datetime.today()
    from_date = (today - timedelta(days=1)).replace(hour=2, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
    to_date = today.replace(hour=1, minute=59, second=59, microsecond=999999).strftime('%Y-%m-%d %H:%M:%S')

    biometric_url = "https://so365.in/SmartApp_ess/api/SwipeDetails/GetDeviceLogs"
    biometric_params = {
        "APIKey": "375211082407",
        "AccountName": "ALWANEES",
        "FromDate": from_date,
        "ToDate": to_date
    }

    try:
        response = requests.get(biometric_url, params=biometric_params)
        response.raise_for_status()
        data = response.json()
        frappe.msgprint("Biometric data fetched successfully")
        print("Biometric data fetched successfully:", data)
    except requests.exceptions.RequestException as e:
        frappe.throw(f"Failed to fetch biometric data. Error: {e}")
        print("Failed to fetch biometric data. Error:", e)
        return

    if isinstance(data, dict) and "Logs" in data:
        logs = data["Logs"]
    elif isinstance(data, list):
        logs = data
    else:
        frappe.throw("Unexpected response format")
        print("Unexpected response format:", data)
        return

    logs_dict = {}

    for log in logs:
        employee_id = log.get("UserId")
        timestamp = log.get("LogDate")
        if employee_id and timestamp:
            try:
                formatted_timestamp = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S").strftime('%Y-%m-%d %H:%M:%S.000000')
                
                log_time = datetime.strptime(formatted_timestamp, '%Y-%m-%d %H:%M:%S.%f')
                day_start_time = log_time.replace(hour=2, minute=0, second=0, microsecond=0)

                if log_time >= day_start_time:
                    if employee_id not in logs_dict or formatted_timestamp > logs_dict[employee_id]['timestamp']:
                        previous_log_type = logs_dict[employee_id]['log_type'] if employee_id in logs_dict else None
                        log_type = "OUT" if previous_log_type == "IN" else "IN"

                        if not previous_log_type:
                            log_type = "IN"  # First check-in after 2 AM should be "IN"

                        logs_dict[employee_id] = {
                            'timestamp': formatted_timestamp,
                            'log_type': log_type
                        }
            except ValueError as e:
                frappe.msgprint(f"Timestamp format error: {e}")
                print(f"Timestamp format error: {e}")
                continue

    for employee_id, log_info in logs_dict.items():
        formatted_timestamp = log_info['timestamp']
        log_type = log_info['log_type']

        existing_log = frappe.db.exists("Employee Checkin", {
            "employee_field_value": employee_id,
            "time": formatted_timestamp
        })

        if existing_log:
            print(f"Duplicate log found for EmployeeID: {employee_id} at {formatted_timestamp}. Skipping entry.")
            frappe.msgprint(f"Duplicate log found for EmployeeID: {employee_id} at {formatted_timestamp}. Skipping entry.")
            continue

        payload = {
            "employee_field_value": employee_id,
            "timestamp": formatted_timestamp,
            "employee_fieldname": "attendance_device_id",
            "log_type": log_type
        }

        try:
            frappe_response = requests.post(
                "https://avicen.enfono.com/api/method/hrms.hr.doctype.employee_checkin.employee_checkin.add_log_based_on_employee_field",
                headers={
                    "Authorization": "token 563e54570e4420e:0cefeae0e1dc516",
                    "Content-Type": "application/json"
                },
                data=json.dumps(payload),
            )
            frappe_response.raise_for_status()
            print(f"Employee Checkin created successfully for EmployeeID: {employee_id}")
            frappe.msgprint(f"Employee Checkin created successfully for EmployeeID: {employee_id}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to create Employee Checkin for EmployeeID: {employee_id}. Error:", e)
            frappe.msgprint(f"Failed to create Employee Checkin for EmployeeID: {employee_id}. Error: {e}")

    print("Process completed.")
    frappe.msgprint("Process completed.")
