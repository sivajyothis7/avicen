# import frappe
# import requests
# import json
# from datetime import datetime, time

# @frappe.whitelist()
# def fetch_and_create_checkins():
#     yesterday = datetime.today().strftime('%Y-%m-%d')
    
#     biometric_url = "https://so365.in/SmartApp_ess/api/SwipeDetails/GetDeviceLogs"
#     biometric_params = {
#         "APIKey": "375211082407",
#         "AccountName": "ALWANEES",
#         "FromDate": yesterday,
#         "ToDate": yesterday
#     }

#     try:
#         response = requests.get(biometric_url, params=biometric_params)
#         response.raise_for_status()
#         data = response.json()
#         frappe.msgprint("Biometric data fetched successfully")
#         print("Biometric data fetched successfully:", data)
#     except requests.exceptions.RequestException as e:
#         frappe.throw(f"Failed to fetch biometric data. Error: {e}")
#         print("Failed to fetch biometric data. Error:", e)
#         return

#     if isinstance(data, dict) and "Logs" in data:
#         logs = data["Logs"]
#     elif isinstance(data, list):
#         logs = data
#     else:
#         frappe.throw("Unexpected response format")
#         print("Unexpected response format:", data)
#         return

#     logs_dict = {}

#     for log in logs:
#         employee_id = log.get("UserId")
#         timestamp = log.get("LogDate")
#         if employee_id and timestamp:
#             try:
#                 log_datetime = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
#                 formatted_timestamp = log_datetime.strftime('%Y-%m-%d %H:%M:%S.000000')

#                 if employee_id in logs_dict:
#                     previous_log_type = logs_dict[employee_id]['log_type']
#                     log_type = "OUT" if previous_log_type == "IN" else "IN"
#                 else:
#                     if log_datetime.time() < time(3, 0):  
#                         log_type = "OUT"
#                     else:
#                         log_type = "IN"

#                 logs_dict[employee_id] = {
#                     'timestamp': formatted_timestamp,
#                     'log_type': log_type
#                 }
#             except ValueError as e:
#                 frappe.msgprint(f"Timestamp format error: {e}")
#                 print(f"Timestamp format error: {e}")
#                 continue

#     for employee_id, log_info in logs_dict.items():
#         formatted_timestamp = log_info['timestamp']
#         log_type = log_info['log_type']

#         existing_log = frappe.db.exists("Employee Checkin", {
#             "employee_field_value": employee_id,
#             "time": formatted_timestamp
#         })

#         if existing_log:
#             print(f"Duplicate log found for EmployeeID: {employee_id} at {formatted_timestamp}. Skipping entry.")
#             frappe.msgprint(f"Duplicate log found for EmployeeID: {employee_id} at {formatted_timestamp}. Skipping entry.")
#             continue

#         payload = {
#             "employee_field_value": employee_id,
#             "timestamp": formatted_timestamp,
#             "employee_fieldname": "attendance_device_id",
#             "log_type": log_type
#         }

#         try:
#             frappe_response = requests.post(
#                 "https://avicen.enfono.com/api/method/hrms.hr.doctype.employee_checkin.employee_checkin.add_log_based_on_employee_field",
#                 headers={
#                     "Authorization": "token 563e54570e4420e:0cefeae0e1dc516",
#                     "Content-Type": "application/json"
#                 },
#                 data=json.dumps(payload),
#             )
#             frappe_response.raise_for_status()
#             print(f"Employee Checkin created successfully for EmployeeID: {employee_id}")
#             frappe.msgprint(f"Employee Checkin created successfully for EmployeeID: {employee_id}")
#         except requests.exceptions.RequestException as e:
#             print(f"Failed to create Employee Checkin for EmployeeID: {employee_id}. Error:", e)
#             frappe.msgprint(f"Failed to create Employee Checkin for EmployeeID: {employee_id}. Error: {e}")

#     print("Process completed.")
#     frappe.msgprint("Process completed.")



import frappe
import requests
import json
from datetime import datetime, time

@frappe.whitelist()
def fetch_and_create_checkins():
    dates_to_fetch = [
        "2024-06-12"
   ]

    biometric_url = "https://so365.in/SmartApp_ess/api/SwipeDetails/GetDeviceLogs"
    
    for target_date in dates_to_fetch:
        frappe.msgprint(f"Fetching data for {target_date}")

        biometric_params = {
            "APIKey": "375211082407",
            "AccountName": "ALWANEES",
            "FromDate": target_date,
            "ToDate": target_date
        }

        try:
            response = requests.get(biometric_url, params=biometric_params)
            response.raise_for_status()
            data = response.json()
            print(f"Biometric data fetched successfully for {target_date}:", data)
        except requests.exceptions.RequestException as e:
            frappe.throw(f"Failed to fetch biometric data for {target_date}. Error: {e}")
            return

        if isinstance(data, dict) and "Logs" in data:
            logs = data["Logs"]
        elif isinstance(data, list):
            logs = data
        else:
            frappe.throw(f"Unexpected response format on {target_date}")
            print("Unexpected response format:", data)
            return

        logs_dict = {}

        for log in logs:
            employee_id = log.get("UserId")
            timestamp = log.get("LogDate")
            if employee_id and timestamp:
                try:
                    log_datetime = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
                    formatted_timestamp = log_datetime.strftime('%Y-%m-%d %H:%M:%S.000000')

                    if employee_id in logs_dict:
                        previous_log_type = logs_dict[employee_id]['log_type']
                        log_type = "OUT" if previous_log_type == "IN" else "IN"
                    else:
                        log_type = "OUT" if log_datetime.time() < time(3, 0) else "IN"

                    logs_dict[employee_id] = {
                        'timestamp': formatted_timestamp,
                        'log_type': log_type
                    }
                except ValueError as e:
                    frappe.msgprint(f"Timestamp format error for {timestamp}: {e}")
                    continue

        for employee_id, log_info in logs_dict.items():
            formatted_timestamp = log_info['timestamp']
            log_type = log_info['log_type']

            existing_log = frappe.db.exists("Employee Checkin", {
                "employee_field_value": employee_id,
                "time": formatted_timestamp
            })

            if existing_log:
                print(f"Duplicate log found for {employee_id} at {formatted_timestamp}. Skipping.")
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
                print(f"Checkin created for {employee_id} at {formatted_timestamp}")
            except requests.exceptions.RequestException as e:
                print(f"Failed to create Checkin for {employee_id} at {formatted_timestamp}. Error: {e}")

    print("All dates processed.")
    frappe.msgprint("Biometric import completed for June 12, 13, 14, and 15.")



# import frappe
# import requests
# import json
# from datetime import datetime

# zkteco_url = "http://fidu.dyndns.org:8081/iclock/api/transactions/"

# erp_url = "http://127.0.0.1:8006"
# api_key = "7659804d9abbc47"
# api_secret = "3f226f85d2c0b42"
# erp_headers = {
#     "Authorization": f"token {api_key}:{api_secret}",
#     "Content-Type": "application/json"
# }

# @frappe.whitelist()
# def fetch_and_create_checkins():
#     page = 1 
    
#     today = datetime.today()
#     start_time = today.strftime("%Y-%m-%d 00:00:00")  
#     end_time = today.strftime("%Y-%m-%d 23:59:59")  

#     while True:
#         zkteco_api_url = f"{zkteco_url}?start_time={start_time}&end_time={end_time}&page={page}"

#         response = requests.get(zkteco_api_url, headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzM0NzYxNzI3LCJpYXQiOjE3MzQ2NzUzMjcsImp0aSI6ImMyNWMzYTM3MDdmNjQ2NmFiMWUzZjMyMTBkNzA3MGZiIiwidXNlcl9pZCI6MX0.IeizsFkMiWmySNEnHxYYNsGRRyPFMnmAVv-DmPCdxac"})
#         response.raise_for_status()
#         data = response.json()
        
#         if data['code'] != 0:  
#             frappe.throw(f"Failed to fetch data. Error code: {data['code']}")
#             return

#         for transaction in data['data']:
#             employee_id = transaction['emp_code']
#             punch_time = transaction['punch_time']
#             punch_state_display = transaction['punch_state_display']

#             try:
#                 log_datetime = datetime.strptime(punch_time, "%Y-%m-%d %H:%M:%S")
#                 formatted_time = log_datetime.strftime('%Y-%m-%d %H:%M:%S.000000')
#             except ValueError as e:
#                 frappe.msgprint(f"Timestamp format error: {e}")
#                 continue

#             log_type = "IN" if punch_state_display == "Check In" else "OUT"

#             payload = {
#                 "employee_field_value": employee_id,
#                 "timestamp": formatted_time,
#                 "employee_fieldname": "attendance_device_id",  
#                 "log_type": log_type
#             }

#             try:
#                 frappe_response = requests.post(
#                     f"{erp_url}/api/method/hrms.hr.doctype.employee_checkin.employee_checkin.add_log_based_on_employee_field",
#                     headers=erp_headers,
#                     data=json.dumps(payload)
#                 )
#                 frappe_response.raise_for_status()
#                 frappe.msgprint(f"Employee Checkin created successfully for EmployeeID: {employee_id}")
#             except requests.exceptions.RequestException as e:
#                 frappe.msgprint(f"Failed to create Employee Checkin for EmployeeID: {employee_id}. Error: {e}")
#                 continue

#         if data.get('next'):
#             page += 1
#         else:
#             break 

#     frappe.msgprint("Process completed.")
#     print("Process completed.")
