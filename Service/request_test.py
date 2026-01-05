import requests



url = "http://localhost:8080/whole_service"
payload = {
    "data_source_path": "/data1/yxr/结果文件",
}
resp = requests.post(url, json=payload, timeout=500)
print(resp.status_code, resp.json())
# import pdb;pdb.set_trace()
print(resp.json().keys())