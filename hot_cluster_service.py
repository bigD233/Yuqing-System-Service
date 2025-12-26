from flask import Flask, request, jsonify
import os
import json
import sys
import threading
import importlib.util
from typing import Any

# 仅在GPU 3上加载模型
os.environ["CUDA_VISIBLE_DEVICES"] = "7"

# 引入hotPrediction热点预测模块
SERVICE_ROOT = "/home/yxr/Yuqing-Project/Service"
if SERVICE_ROOT not in sys.path:
    sys.path.append(SERVICE_ROOT)

# 修复 hotPrediction 内部模块导入路径问题 (data_processor等)
HOT_PREDICTION_DIR = os.path.join(SERVICE_ROOT, "hotPrediction")
if HOT_PREDICTION_DIR not in sys.path:
    sys.path.append(HOT_PREDICTION_DIR)

CLUSTER_MAIN_DIR = os.path.join(SERVICE_ROOT, "Cluster-main")
if CLUSTER_MAIN_DIR not in sys.path:
    sys.path.append(CLUSTER_MAIN_DIR)

from hotPrediction.hot_prediction import predict_single_event, init_predictor

# 模型单例与线程锁
_predictor_lock = threading.Lock()
_predictor_instance = None

_cluster_lock = threading.Lock()
_cluster_module = None


def get_predictor():
    """获取全局唯一的预测器实例（懒加载）"""
    global _predictor_instance
    if _predictor_instance is None:
        with _predictor_lock:
            if _predictor_instance is None:
                print("[Service] Initializing HotPredictor singleton...", flush=True)
                _predictor_instance = init_predictor()
                print("[Service] HotPredictor initialized.", flush=True)
    return _predictor_instance


def _load_cluster_module():
    module_name = "cluster_main"
    module_path = os.path.join(CLUSTER_MAIN_DIR, "main.py")
    if not os.path.exists(module_path):
        raise FileNotFoundError(f"Cluster main.py not found: {module_path}")
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module spec for: {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def get_cluster_module():
    global _cluster_module
    if _cluster_module is None:
        with _cluster_lock:
            if _cluster_module is None:
                print("[Service] Initializing Cluster singleton...", flush=True)
                _cluster_module = _load_cluster_module()
                if not hasattr(_cluster_module, "init_feature_extractor"):
                    raise AttributeError("Cluster module missing init_feature_extractor")
                if not hasattr(_cluster_module, "forward"):
                    raise AttributeError("Cluster module missing forward")
                _cluster_module.init_feature_extractor()
                print("[Service] Cluster initialized.", flush=True)
    return _cluster_module


def _jsonable(obj: Any):
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    to_list = getattr(obj, "tolist", None)
    if callable(to_list):
        return to_list()
    return str(obj)


app = Flask(__name__)

# 内部固定参数（不使用环境变量）
SERVICE_HOST = "0.0.0.0"
SERVICE_PORT = 8002


@app.route("/hot", methods=["POST"])
def run_hot_prediction():
    if not request.is_json:
        return jsonify({"ok": False, "error": "request body must be JSON"}), 400

    payload = request.get_json(silent=True) or {}

    # 必填参数
    event_name = payload.get("event_name")
    csv_file_path = payload.get("csv_file_path")
    image_dir_path = payload.get("image_dir_path")

    # 参数校验
    missing = [k for k, v in {
        "event_name": event_name,
        "csv_file_path": csv_file_path,
        "image_dir_path": image_dir_path,
    }.items() if not v]
    if missing:
        return jsonify({
            "ok": False,
            "error": f"missing required fields: {', '.join(missing)}"
        }), 400

    if not os.path.exists(csv_file_path):
        return jsonify({"ok": False, "error": f"csv_file_path not found: {csv_file_path}"}), 400
    if not os.path.isdir(os.path.dirname(csv_file_path)):
        return jsonify({"ok": False, "error": f"csv_file directory missing: {os.path.dirname(csv_file_path)}"}), 400
    if not os.path.isdir(image_dir_path):
        return jsonify({"ok": False, "error": f"image_dir_path not found: {image_dir_path}"}), 400

    try:
        # 获取单例模型
        predictor = get_predictor()

        # 调用逻辑，传入 predictor 实例
        output_json_path = predict_single_event(
            event_name=event_name,
            csv_file_path=csv_file_path,
            image_dir_path=image_dir_path,
            predictor=predictor,
        )
        with open(output_json_path, "r", encoding="utf-8") as f:
            result_data = json.load(f)
        response = {
            "ok": True,
            "event_name": event_name,
            "outputs": result_data,
        }
        return jsonify(response), 200
    except Exception as exc:
        return jsonify({
            "ok": False,
            "error": str(exc)
        }), 500


@app.route("/cluster", methods=["POST"])
def run_cluster():
    if not request.is_json:
        return jsonify({"ok": False, "error": "request body must be JSON"}), 400

    payload = request.get_json(silent=True) or {}

    data_source_path = payload.get("data_source_path")
    use_saved = bool(payload.get("use_saved", False))
    method = payload.get("method", "traditional")
    min_posts = int(payload.get("min_posts", 1))
    source_site = payload.get("source_site")
    use_prior = bool(payload.get("use_prior", True))
    max_samples_per_event = int(payload.get("max_samples_per_event", 1000))
    min_samples_per_event = int(payload.get("min_samples_per_event", 1))

    if data_source_path is not None and not os.path.exists(data_source_path):
        return jsonify({"ok": False, "error": f"data_source_path not found: {data_source_path}"}), 400

    try:
        cluster_module = get_cluster_module()
        result = cluster_module.forward(
            data_source_path=data_source_path,
            use_saved=use_saved,
            method=method,
            min_posts=min_posts,
            source_site=source_site,
            use_prior=use_prior,
            max_samples_per_event=max_samples_per_event,
            min_samples_per_event=min_samples_per_event,
        )
        if result is None:
            return jsonify({"ok": False, "error": "cluster forward returned None"}), 500
        outputs = {
            "clusters": _jsonable(result.get("clusters")),
            "metrics": _jsonable(result.get("metrics")),
            "labels": _jsonable(result.get("labels")),
        }
        return jsonify({"ok": True, "outputs": outputs}), 200
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "hot_and_cluster",
        "root": SERVICE_ROOT,
    })


if __name__ == "__main__":
    app.run(host=SERVICE_HOST, port=SERVICE_PORT, debug=False)
