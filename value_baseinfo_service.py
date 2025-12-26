from flask import Flask, request, jsonify
import os
import sys
import threading
import json
import traceback

# 仅在GPU 3上加载模型 (参考其他服务)
os.environ["CUDA_VISIBLE_DEVICES"] = "2"

# 设置工作目录为 human_value_predict，以确保模块内部的相对路径正确
WORK_DIR = "/home/yxr/Yuqing-Project/Service/human_value_predict"
if os.path.exists(WORK_DIR):
    os.chdir(WORK_DIR)
    print(f"[Service] Changed working directory to: {os.getcwd()}")

# 添加路径到 sys.path
if WORK_DIR not in sys.path:
    sys.path.append(WORK_DIR)

# 导入API模块
_import_error_message = None
try:
    import predict_human_value_api
    import static_analyize_api
    print("[Service] Modules imported successfully.")
except ImportError as e:
    _import_error_message = str(e)
    print(f"[Service] Error importing modules: {e}")
    predict_human_value_api = None
    static_analyize_api = None

app = Flask(__name__)

# 配置
SERVICE_HOST = "0.0.0.0"
SERVICE_PORT = 8003

# 初始化状态
_value_initialized = False
_baseinfo_initialized = False
_init_lock = threading.Lock()

def ensure_initialized():
    """确保模型/服务已初始化"""
    global _value_initialized, _baseinfo_initialized
    with _init_lock:
        if not _value_initialized:
            if predict_human_value_api:
                print("[Service] Initializing predict_human_value_api...")
                try:
                    predict_human_value_api.init()
                    _value_initialized = True
                    print("[Service] predict_human_value_api initialized.")
                except Exception as e:
                    print(f"[Service] Failed to initialize predict_human_value_api: {e}")
                    traceback.print_exc()
        
        if not _baseinfo_initialized:
            if static_analyize_api:
                print("[Service] Initializing static_analyize_api...")
                try:
                    static_analyize_api.init()
                    _baseinfo_initialized = True
                    print("[Service] static_analyize_api initialized.")
                except Exception as e:
                    print(f"[Service] Failed to initialize static_analyize_api: {e}")
                    traceback.print_exc()

@app.route("/value", methods=["POST"])
def run_value_prediction():
    ensure_initialized()
    if not predict_human_value_api:
        return jsonify({
            "ok": False, 
            "error": f"predict_human_value_api module not loaded. Import error: {_import_error_message}"
        }), 500

    if not request.is_json:
        return jsonify({"ok": False, "error": "request body must be JSON"}), 400

    payload = request.get_json(silent=True) or {}
    
    # 参数获取
    event_name = payload.get("event_name", "")
    csv_file_path = payload.get("csv_file_path", "")
    image_dir_path = payload.get("image_dir_path", "")
    
    # 参数校验
    missing = [k for k, v in {
        "event_name": event_name,
        "csv_file_path": csv_file_path,
    }.items() if not v]
    
    if missing:
        return jsonify({
            "ok": False,
            "error": f"missing required fields: {', '.join(missing)}"
        }), 400

    if not os.path.exists(csv_file_path):
        return jsonify({"ok": False, "error": f"csv_file_path not found: {csv_file_path}"}), 400

    try:
        # 调用 predict_human_value_api.forward
        print(f"[Service] Calling predict_human_value_api.forward for {event_name}...")
        # import pdb; pdb.set_trace()
        result, dir_path = predict_human_value_api.forward(
            event_name=event_name,
            event_data_csv_path=csv_file_path,
            event_image_dir=image_dir_path,
            skip_used=True
        )
        
        response = {
            "ok": True,
            "event_name": event_name,
            "outputs": result,
            "output_dir": dir_path
        }
        return jsonify(response), 200
    except Exception as exc:
        print(f"[Service] Error in /value: {exc}")
        traceback.print_exc()
        return jsonify({
            "ok": False,
            "error": str(exc)
        }), 500

@app.route("/baseinfo", methods=["POST"])
def run_baseinfo_analysis():
    ensure_initialized()
    if not static_analyize_api:
        return jsonify({
            "ok": False, 
            "error": f"static_analyize_api module not loaded. Error: {_baseinfo_import_error}"
        }), 500

    if not request.is_json:
        return jsonify({"ok": False, "error": "request body must be JSON"}), 400

    payload = request.get_json(silent=True) or {}

    # 参数获取
    csv_file_path = payload.get("csv_file_path", "")
    
    if not csv_file_path:
         return jsonify({"ok": False, "error": "missing required field: csv_file_path"}), 400

    if not os.path.exists(csv_file_path):
        return jsonify({"ok": False, "error": f"path not found: {csv_file_path}"}), 400

    try:
        # 调用 static_analyize_api.forward
        # 注意：该函数可能期望目录路径，如果传入文件路径可能需要API内部支持或传入父目录
        # 这里直接透传 csv_file_path
        print(f"[Service] Calling static_analyize_api.forward for {csv_file_path}...")
        result = static_analyize_api.forward_file(csv_file_path)
        
        
        response = {
            "ok": True,
            "outputs": result,
        }
        return jsonify(response), 200
    except Exception as exc:
        print(f"[Service] Error in /baseinfo: {exc}")
        traceback.print_exc()
        return jsonify({
            "ok": False,
            "error": str(exc)
        }), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "value_baseinfo_service",
        "initialized": {
            "value": _value_initialized,
            "baseinfo": _baseinfo_initialized
        },
        "work_dir": os.getcwd()
    })

if __name__ == "__main__":
    print(f"[Service] Starting service on {SERVICE_HOST}:{SERVICE_PORT}...")
    # 在主线程中可以预先初始化（可选）
    # ensure_initialized()
    app.run(host=SERVICE_HOST, port=SERVICE_PORT, debug=False)
