# 应用服务层架构

本目录为项目后端的 **算法微服务层**：以 Flask 形式将多个算法（聚类、情感、舆情分类、热度、价值观、基础统计）封装为独立服务，并由编排服务串联调用，最终把聚合结果写入数据库（供前端展示）。

- **编排入口**：`service_api.py`（聚类 -> 逐事件调用各算法 -> 聚合 -> 入库）
- **算法微服务**：
  - `yuqing_emotion_service.py`：情感预测 + 舆情话题分类（端口 8001）
  - `hot_cluster_service.py`：热度预测 + 聚类（端口 8002）
  - `value_baseinfo_service.py`：价值观预测 + 基础信息统计（端口 8003）

---

## 总体架构

### 1) 数据流（从原始数据到入库）

1. 调用编排服务 `POST /whole_service` 并传入 `data_source_path`（原始数据根目录）。
2. 编排服务调用 **聚类服务**：`POST http://localhost:8002/cluster`。
3. 聚类结果会在 `data_source_path/cluster_events/` 下生成若干事件目录（每个目录对应一个聚类簇）。
4. 编排服务遍历每个事件目录，对每个事件依次调用：
   - 情感服务：`POST http://localhost:8001/emotion`
   - 舆情服务：`POST http://localhost:8001/yuqing`
   - 热度服务：`POST http://localhost:8002/hot`
   - 价值观服务：`POST http://localhost:8003/value`
   - 基础信息服务：`POST http://localhost:8003/baseinfo`
5. 编排服务将上述结果整理为统一格式（见下方 `formatted_result`），保存到本地 `formatted_results.json`。
6. 编排服务将最终聚合结果 POST 到数据库后端：
   - `POST http://localhost:5000/api/addHotThing`

### 2) 服务端口约定

- **编排服务**：`8080`（`service_api.py`）
- **情感 + 舆情服务**：`8001`（`yuqing_emotion_service.py`）
- **热度 + 聚类服务**：`8002`（`hot_cluster_service.py`）
- **价值观 + 基础信息服务**：`8003`（`value_baseinfo_service.py`）
- **数据库 API（入库/查询）**：`5000`（见 `finalfile/backend`）

---

## 目录结构（Service）

```
Service/
├── service_api.py                 # 编排入口：串联聚类+事件级算法并入库
├── yuqing_emotion_service.py      # 情感/舆情微服务 (8001)
├── hot_cluster_service.py         # 热度/聚类微服务 (8002)
├── value_baseinfo_service.py      # 价值观/基础信息微服务 (8003)
├── Cluster-main/                  # 多模态聚类算法
├── hotPrediction/                 # 热度预测算法
├── emotion/                       # 情感分析算法
├── yuqing-module/                 # 舆情等级算法
├── human_value_predict/           # 价值观预测算法&基础信息统计算法
└── request_test.py                # 简单请求脚本（调用 /whole_service）
```

---

## 数据准备

聚类模块对数据目录有固定格式要求（详见 `Cluster-main/README.md`）。常见格式如下：

```
<data_source_path>/
└── 事件A/
    ├── 事件A.csv
    └── images/
        ├── {id}.jpg
        └── {id}-0.jpg
```

- CSV 至少包含 `id`、文本字段（如 `微博正文` 等）。
- images 目录可选（多模态聚类/部分算法可能需要）。

---

## 快速开始

> 说明：各算法服务可能依赖 GPU、模型文件路径与较重的深度学习依赖。建议按“服务拆分”方式分别安装依赖与启动。

### 1) 启动数据库 API（入库服务，端口 5000）

数据库 API 不在本目录下，而在：`finalfile/backend`。

- 安装依赖（`finalfile/requirements.txt`）
- 启动：`python finalfile/backend/app.py`
- 默认 MySQL 连接：见 `finalfile/backend/config.py`（development 配置）
- 初始化数据库：`finalfile/init.sql`

### 2) 启动算法微服务

分别启动 3 个 Flask 服务（建议不同终端/进程）：

- 情感/舆情服务：
  - 入口：`Service/yuqing_emotion_service.py`
  - 端口：`8001`

- 热度/聚类服务：
  - 入口：`Service/hot_cluster_service.py`
  - 端口：`8002`

- 价值观/基础信息服务：
  - 入口：`Service/value_baseinfo_service.py`
  - 端口：`8003`

依赖参考：

- `Service/hotPrediction/requirements.txt`
- `Service/muitiCluster/requirements.txt`（聚类相关）
- `Service/human_value_predict/humanvalue_api/requirements.txt`（价值观相关）

> 注意：部分模块在代码中写死了模型路径（例如 `yuqing_emotion_service.py` 中的 `DEFAULT_MODEL_PATH`），需要在你的机器上保证路径存在或自行修改为可用路径。

### 3) 启动编排服务（端口 8080）

- 入口：`Service/service_api.py`
- 默认端口：`8080`

环境变量（可选）：

- `SERVICE_URL_EMOTION` 默认 `http://localhost:8001/emotion`
- `SERVICE_URL_YUQING` 默认 `http://localhost:8001/yuqing`
- `SERVICE_URL_HOT` 默认 `http://localhost:8002/hot`
- `SERVICE_URL_CLUSTER` 默认 `http://localhost:8002/cluster`
- `SERVICE_URL_VALUE` 默认 `http://localhost:8003/value`
- `SERVICE_URL_BASEINFO` 默认 `http://localhost:8003/baseinfo`
- `REQUEST_TIMEOUT_SECONDS` 默认 `600`

---

## API 使用

### 1) 一键跑完整流程：`POST /whole_service`

- URL：`http://localhost:8080/whole_service`
- Body：

```json
{
  "data_source_path": "/data1/yxr/结果文件",
  "use_saved": false,
  "method": "traditional",
  "min_posts": 1,
  "source_site": "新浪微博",
  "use_prior": true,
  "max_samples_per_event": 1000,
  "min_samples_per_event": 1
}
```

成功后行为：

- 会在 `<data_source_path>/cluster_events/` 下生成事件目录
- 会逐事件调用所有算法
- 会 POST 到 `http://localhost:5000/api/addHotThing` 完成入库

你也可以直接运行：

```bash
python Service/request_test.py
```

### 2) 单个算法微服务接口

所有微服务均使用 `POST` + `application/json`。

- `POST http://localhost:8001/emotion`
- `POST http://localhost:8001/yuqing`
- `POST http://localhost:8002/hot`
- `POST http://localhost:8002/cluster`
- `POST http://localhost:8003/value`
- `POST http://localhost:8003/baseinfo`

事件级接口通用请求体：

```json
{
  "event_name": "某事件",
  "csv_file_path": "/path/to/某事件.csv",
  "image_dir_path": "/path/to/images"
}
```

聚类接口请求体：

```json
{
  "data_source_path": "/path/to/data_root",
  "use_saved": false,
  "method": "traditional",
  "min_posts": 1,
  "source_site": "新浪微博",
  "use_prior": true,
  "max_samples_per_event": 1000,
  "min_samples_per_event": 1
}
```

---

## 入库数据格式（编排服务输出）

编排服务会把各算法结果整合为一个 `formatted_result` 并 POST 到 `POST /api/addHotThing`。

结构概览：

- `hot_thing`
- `user_emotion`
- `heat`
- `trend`（7 天趋势数组）
- `typical_posts`（典型帖子列表，含价值观雷达字段）
- `population_composition`（人群画像 + 人群价值观）
- `map`（省份着色数据）
- `word_cloud`（可选，base64 图）

对应数据库表（见 `init.sql`）：

- `hot_things`
- `users_emotion`
- `heat`
- `trend`
- `typical_posts` / `typical_radar`
- `population_composition` / `population_values`
- `thing_provinces`
- `word_cloud`

---


