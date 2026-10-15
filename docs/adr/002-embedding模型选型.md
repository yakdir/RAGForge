# ADR-002: Embedding 模型选型 — 本地 bge-m3 vs OpenAI API

## 状态

已采纳

## 背景

RAGForge 需要把文本转换成向量（embedding），有两种方案：

- **本地模型**：在自己的 GPU/CPU 上跑 embedding 模型（如 bge-m3、sentence-transformers）
- **API 调用**：调用 OpenAI / Cohere / 智谱等云服务的 embedding API

## 决策

选择 **本地 bge-m3 模型**，全本地运行。

## 理由

1. **零 API 成本**
   - 本地跑模型不花钱
   - 适合开发调试，不用每次调用都产生费用
   - 符合"零 API 成本"的产品定位

2. **数据隐私**
   - 文档内容不需要传到第三方服务器
   - 适合处理敏感文档（内部文档、私有数据）
   - 没有数据泄露风险

3. **中文效果好**
   - bge-m3 是 BAAI 开源的多语言 embedding 模型
   - 在中文 C-MTEB 榜单上表现优秀
   - 比 OpenAI 的 text-embedding-ada-002 中文效果好

4. **延迟可控**
   - 本地跑，网络延迟为 0
   - GPU 上每次推理约 50-100ms
   - 比调用远程 API（网络往返 200-500ms）更快

5. **为什么不选 API？**
   - 要钱：OpenAI embedding 每 1M token $0.02，开发阶段测试多了也不少
   - 要网：国内调用 OpenAI API 不稳定，需要代理
   - 要 key：需要申请 API key，增加使用门槛

## 代价

- 需要下载模型（bge-m3 约 2GB）
- 需要 GPU 才能跑得快（CPU 也能跑，但慢）
- 首次加载模型需要几秒钟

## 未来扩展

- 可以加一个配置项，让用户选择用本地模型还是 API
- 默认用本地，API 作为高级选项
- 这样既有本地免费方案，又有云端高精度方案

## 参考

- [bge-m3 模型](https://huggingface.co/BAAI/bge-m3)
- [C-MTEB 中文 embedding 榜单](https://huggingface.co/spaces/mteb/leaderboard)
- [OpenAI Embeddings API](https://platform.openai.com/docs/guides/embeddings)
