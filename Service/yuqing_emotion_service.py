from flask import Flask, request, jsonify
import os
import threading
from typing import Optional

# 仅在GPU 3上加载模型
os.environ["CUDA_VISIBLE_DEVICES"] = "2"

# 引入情感分析推理类
try:
	from emotion.inference import EmotionInference
except Exception as exc:
	EmotionInference = None  # 延迟在请求阶段给出更清晰的错误
	_import_error = exc
else:
	_import_error = None

# 引入yuqing话题分类推理类（通过追加路径方式加载）
import sys
_YUQING_DIR = "/home/yxr/Yuqing-Project/Service/yuqing-module"
if _YUQING_DIR not in sys.path:
	sys.path.append(_YUQING_DIR)
try:
	from inference import TopicClassifier  # yuqing-module/inference.py
except Exception as exc:
	TopicClassifier = None
	_yuqing_import_error = exc
else:
	_yuqing_import_error = None

app = Flask(__name__)

# 内部固定参数（不使用环境变量）
SERVICE_HOST = "0.0.0.0"
SERVICE_PORT = 8001
DEFAULT_MODEL_PATH = "/data1/yxr/Checkpoint/Service/Emotion/emotion_model"
DEFAULT_BATCH_SIZE = 1
DEFAULT_OPENAI_PORT = 30000

# yuqing默认参数
DEFAULT_YUQING_MODEL_PATH = "/home/yxr/Yuqing-Project/Service/yuqing-module/topic_model/transformer_best.pt"
DEFAULT_YUQING_BATCH_SIZE = 4

# 推理器单例与线程锁
_infer_lock = threading.Lock()
_infer_instance: Optional[EmotionInference] = None
_infer_initialized: bool = False

# yuqing推理器单例与线程锁
_yuqing_lock = threading.Lock()
_yuqing_instance: Optional[TopicClassifier] = None
_yuqing_initialized: bool = False


def get_infer_instance(model_path: Optional[str], batch_size: int, openai_port: int) -> EmotionInference:
	"""获取或创建全局推理实例，使用惰性初始化。"""
	global _infer_instance, _infer_initialized
	if EmotionInference is None:
		raise RuntimeError(f"无法导入EmotionInference: {_import_error}")
	if _infer_instance is None:
		with _infer_lock:
			if _infer_instance is None:
				_infer_instance = EmotionInference(
					model_path=model_path,
					batch_size=batch_size,
					port=openai_port,
				)
				# 仅在首次创建时调用可选的init()
				if hasattr(_infer_instance, "init") and callable(getattr(_infer_instance, "init")):
					_infer_instance.init(model_path, batch_size, openai_port)
				_infer_initialized = True
	return _infer_instance


def get_yuqing_instance(model_path: Optional[str], batch_size: int) -> TopicClassifier:
	"""获取或创建yuqing话题分类推理实例，使用惰性初始化。"""
	global _yuqing_instance, _yuqing_initialized
	if TopicClassifier is None:
		raise RuntimeError(f"无法导入TopicClassifier: {_yuqing_import_error}")
	if _yuqing_instance is None:
		with _yuqing_lock:
			if _yuqing_instance is None:
				_yuqing_instance = TopicClassifier(
					model_path=model_path,
					batch_size=batch_size,
				)
				# 若类实现了可选的init，则在首次创建时调用
				if hasattr(_yuqing_instance, "init") and callable(getattr(_yuqing_instance, "init")):
					_yuqing_instance.init(model_path, batch_size)
				_yuqing_initialized = True
	return _yuqing_instance


@app.route("/emotion", methods=["POST"])
def run_emotion_inference():
	if not request.is_json:
		return jsonify({"ok": False, "error": "request body must be JSON"}), 400

	payload = request.get_json(silent=True) or {}

	# 必填参数
	event_name = payload.get("event_name")
	csv_file_path = payload.get("csv_file_path")
	image_dir_path = payload.get("image_dir_path")

	# import pdb; pdb.set_trace()

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
		# 仅使用内部固定默认参数初始化（只在首次创建时进行init）
		inference = get_infer_instance(
			model_path=DEFAULT_MODEL_PATH,
			batch_size=DEFAULT_BATCH_SIZE,
			openai_port=DEFAULT_OPENAI_PORT,
		)
		# 运行算法
		event_summary = inference.forward(
			event_name=event_name,
			csv_file_path=csv_file_path,
			image_dir_path=image_dir_path,
		)
		response = {
			"ok": True,
			"event_name": event_name,
			"outputs": event_summary,
		}
		# 可选：尝试加载事件级结果简要返回
		
		return jsonify(response), 200
	except Exception as exc:
		return jsonify({
			"ok": False,
			"error": str(exc)
		}), 500


@app.route("/yuqing", methods=["POST"])
def run_yuqing_inference():
	if not request.is_json:
		return jsonify({"ok": False, "error": "request body must be JSON"}), 400

	payload = request.get_json(silent=True) or {}

	# 必填参数（与情感接口保持一致）
	event_name = payload.get("event_name")
	csv_file_path = payload.get("csv_file_path")
	image_dir_path = payload.get("image_dir_path")

	# print(csv_file_path)

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
	# if not os.path.isdir(image_dir_path):
	# 	print("no image folder")
	# 	return jsonify({"ok": False, "error": f"image_dir_path not found: {image_dir_path}"}), 400

	try:
		classifier = get_yuqing_instance(
			model_path=DEFAULT_YUQING_MODEL_PATH,
			batch_size=DEFAULT_YUQING_BATCH_SIZE,
		)
		# 运行yuqing话题分类forward
		event_results = classifier.forward(
			event_name=event_name,
			csv_file_path=csv_file_path,
			image_dir_path=image_dir_path,
		)
		response = {
			"ok": True,
			"event_name": event_name,
			"outputs": event_results,
		}
		return jsonify(response), 200
	except Exception as exc:
		return jsonify({
			"ok": False,
			"error": str(exc)
		}), 500


@app.route("/health", methods=["GET"])
def health():
	return jsonify({
		"status": "ok",
		"model_imported": EmotionInference is not None,
		"initialized": _infer_initialized,
		"defaults": {
			"model_path": DEFAULT_MODEL_PATH,
			"batch_size": DEFAULT_BATCH_SIZE,
			"openai_port": DEFAULT_OPENAI_PORT,
		},
	})


@app.route("/yuqing/health", methods=["GET"])
def yuqing_health():
	return jsonify({
		"status": "ok",
		"model_imported": TopicClassifier is not None,
		"initialized": _yuqing_initialized,
		"defaults": {
			"model_path": DEFAULT_YUQING_MODEL_PATH,
			"batch_size": DEFAULT_YUQING_BATCH_SIZE,
		},
	})


if __name__ == "__main__":
	app.run(host=SERVICE_HOST, port=SERVICE_PORT, debug=False)
