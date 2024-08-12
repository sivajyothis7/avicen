import frappe
import requests
import json
from datetime import datetime, timedelta

@frappe.whitelist()
def fetch_and_create_checkins():
    yesterday = datetime.today().strftime('%Y-%m-%d')
    
    biometric_url = "https://so365.in/SmartApp_ess/api/SwipeDetails/GetDeviceLogs"
    biometric_params = {
        "APIKey": "375211082407",
        "AccountName": "ALWANEES",
        "FromDate": yesterday,
        "ToDate": yesterday
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

    log_type_toggle = "OUT" 

    for log in logs:
        employee_field_value = log.get("UserId")  
        timestamp = log.get("LogDate")

        try:
            formatted_timestamp = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S").strftime('%Y-%m-%d %H:%M:%S.000000')
        except ValueError as e:
            frappe.msgprint(f"Timestamp format error: {e}")
            print(f"Timestamp format error: {e}")
            continue

        payload = {
            "employee_field_value": employee_field_value,
            "timestamp": formatted_timestamp,
            "employee_fieldname": "attendance_device_id",
            "log_type": log_type_toggle
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
            print(f"Employee Checkin created successfully for EmployeeID: {employee_field_value}")
            frappe.msgprint(f"Employee Checkin created successfully for EmployeeID: {employee_field_value}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to create Employee Checkin for EmployeeID: {employee_field_value}. Error:", e)
            frappe.msgprint(f"Failed to create Employee Checkin for EmployeeID: {employee_field_value}. Error: {e}")

        log_type_toggle = "IN" if log_type_toggle == "OUT" else "OUT"

    print("Process completed.")
    frappe.msgprint("Process completed.")
