# RAGForge — RAG 评估与优化平台

> 全本地运行的 RAG 系统评估与优化平台 · 多检索策略对比 · Recall@K / nDCG / MRR 量化评估 · 零 API 成本

## 项目简介

RAGForge 是一个端到端的 RAG（检索增强生成）系统评估平台，帮助开发者：

1. **上传文档** → 自动解析、分块、向量化
2. **检索查询** → 多种策略可切换对比（稠密向量 / BM25 / 混合检索 + Reranker 重排序）
3. **量化评估** → 自动生成测试数据集，计算 Recall@K / nDCG / MRR 等指标
4. **对比优化** → 不同配置的效果可视化对比，找到最优检索方案

## 技术栈

| 层 | 技术 |
|---|---|
| 后端框架 | Django 6.1 |
| 任务队列 | Celery（开发环境用同步模式） |
| 向量数据库 | ChromaDB |
| Embedding 模型 | BAAI/bge-m3（本地运行） |
| Reranker 模型 | BAAI/bge-reranker-v2-m3 |
| 关键词检索 | BM25 (rank_bm25 + jieba 中文分词) |
| 前端 | Tailwind CSS + Chart.js + HTMX |
| 数据库 | SQLite（开发）/ MySQL（生产） |

## 核心功能

### 📄 文档管理
- 支持 PDF / DOCX / Markdown / TXT 格式
- 自动递归分块（512 字符 / 64 重叠）
- bge-m3 向量化，存入 ChromaDB

### 🔍 检索引擎
- **稠密检索**：基于向量语义相似度
- **BM25 检索**：基于关键词精确匹配
- **混合检索**：向量 + BM25 加权融合
- **Reranker 重排序**：交叉编码器精排，提升排序质量

### 📊 评估框架
- 自动从知识库生成评估问题
- 量化指标：Recall@K / nDCG@K / MRR
- 多策略对比图表（Chart.js 柱状图）
- 逐题结果详情

### 👤 用户系统
- 邮箱登录
- 个人中心 + 修改密码

## 快速开始

### 环境要求
- Python 3.12+
- Conda
- GPU 推荐（RTX 4090 测试通过，纯 CPU 也能跑）

### 安装步骤

```bash
# 1. 创建 conda 环境
conda create -n ragforge python=3.12 -y
conda activate ragforge

# 2. 安装依赖
pip install -r requirements.txt

# 3. 国内用户建议配置 HuggingFace 镜像加速
# Windows PowerShell:
$env:HF_ENDPOINT="https://hf-mirror.com"
# Linux/Mac:
export HF_ENDPOINT=https://hf-mirror.com

# 4. 数据库迁移
python manage.py migrate

# 5. 创建超级用户
python manage.py createsuperuser

# 6. 启动开发服务器
python manage.py runserver
```

访问 http://127.0.0.1:8000/ 开始使用。

## 项目架构

```
RAGForge/
├── config/                 # Django 配置层
│   ├── settings/
│   │   ├── base.py        # 基础配置
│   │   ├── dev.py         # 开发环境
│   │   └── prod.py        # 生产环境
│   ├── urls.py
│   └── celery.py
├── apps/
│   ├── accounts/          # 用户系统（登录/个人中心/修改密码）
│   ├── documents/         # 文档管理（上传/解析/分块/向量化）
│   ├── retrieval/         # 检索引擎（稠密/BM25/混合/重排序）
│   ├── evaluation/        # 评估框架（数据集/指标/对比图表）
│   └── dashboard/         # 首页统计面板
├── templates/             # 前端模板
├── chroma_data/           # ChromaDB 持久化目录
├── uploads/               # 上传文件目录
└── manage.py
```

## 检索流程

```
用户查询
    ↓
┌─────────────────────────┐
│  召回阶段（Retrieval）   │
│  ├─ 稠密向量检索        │
│  ├─ BM25 关键词检索     │
│  └─ 混合检索（加权融合） │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│  精排阶段（Reranking）   │
│  bge-reranker-v2-m3     │
└───────────┬─────────────┘
            ↓
        Top-K 结果
```

## 评估指标说明

| 指标 | 说明 |
|---|---|
| Recall@K | 前 K 条结果中是否包含正确答案 |
| nDCG@K | 考虑排序位置的综合评分 |
| MRR | 第一个正确答案的排名倒数 |

## 开发路线图

- [x] 第1周：环境搭建 + Django 骨架
- [x] 第2周：文档上传 → 解析 → 分块 → 向量化
- [x] 第3周：检索功能（稠密 / BM25 / 混合）
- [x] 第4-5周：评估框架 + 对比图表
- [x] 第6周：Reranker 重排序
- [x] 用户系统 + 首页 Dashboard
- [ ] 第7周：生产环境部署（Docker Compose）
- [ ] 第8周：前端优化 + 文档完善

## License

MIT
