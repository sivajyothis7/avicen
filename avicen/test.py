import frappe
import requests
import json
from datetime import datetime

def fetch_biometric_token():
    token_url = "http://fidu.dyndns.org:8081/jwt-api-token-auth/"
    payload = {
        "username": "admin",  
        "password": "Dufi@404"  
    }

    try:
        response = requests.post(token_url, data=payload)
        response.raise_for_status()
        token_data = response.json()
        return token_data.get("token")  
    except requests.exceptions.RequestException as e:
        frappe.throw(f"Failed to fetch biometric token. Error: {e}")
        print(f"Failed to fetch biometric token. Error: {e}")
        return None

@frappe.whitelist()
def fetch_and_create_checkins():
    today = datetime.today()
    start_time = today.replace(hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
    end_time = today.replace(hour=23, minute=59, second=59, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')

    biometric_url = f"http://fidu.dyndns.org:8081/iclock/api/transactions/?end_time={end_time}&start_time={start_time}"

    biometric_token = fetch_biometric_token()  
    if not biometric_token:
        return

    biometric_params = {}
    logs_dict = {}

    try:
        while biometric_url:
            response = requests.get(
                biometric_url,
                headers={"Authorization": f"Bearer {biometric_token}"},  
                params=biometric_params
            )
            response.raise_for_status()
            data = response.json()

            if isinstance(data, dict) and "data" in data:
                logs = data["data"]
            else:
                frappe.throw("Unexpected response format")
                print("Unexpected response format:", data)
                return

            for log in logs:
                employee_id = log.get("emp_code")
                timestamp = log.get("punch_time")
                punch_state_display = log.get("punch_state_display")
                
                if employee_id and timestamp:
                    try:
                        log_datetime = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                        formatted_timestamp = log_datetime.strftime('%Y-%m-%d %H:%M:%S.000000')

                        if punch_state_display == "Check In":
                            log_type = "IN"
                        elif punch_state_display == "Check Out":
                            log_type = "OUT"
                        else:
                            log_type = ""  

                        if employee_id not in logs_dict:
                            logs_dict[employee_id] = []

                        logs_dict[employee_id].append({
                            'timestamp': formatted_timestamp,
                            'log_type': log_type
                        })
                    except ValueError as e:
                        frappe.msgprint(f"Timestamp format error: {e}")
                        print(f"Timestamp format error: {e}")
                        continue

            biometric_url = data.get("next")
            if biometric_url:
                print(f"Fetching next page: {biometric_url}")
            else:
                print("No more pages to fetch.")

    except requests.exceptions.RequestException as e:
        frappe.throw(f"Failed to fetch biometric data. Error: {e}")
        print("Failed to fetch biometric data. Error:", e)
        return

    for employee_id, logs in logs_dict.items():
        for log_info in logs:
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
                    "http://127.0.0.1:8006/api/method/hrms.hr.doctype.employee_checkin.employee_checkin.add_log_based_on_employee_field",
                    headers={
                        "Authorization": "token 7659804d9abbc47:e500a38f79d0d4f",  
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
