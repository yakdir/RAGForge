# ADR-001: 向量数据库选型 — ChromaDB

## 状态

已采纳

## 背景

RAGForge 需要一个向量数据库来存储文档分块的嵌入向量，支持相似度检索。可选方案包括：

- **ChromaDB**：轻量级开源向量数据库，支持持久化，Python 原生集成
- **pgvector**：PostgreSQL 扩展，把向量存在关系型数据库里
- **FAISS**：Facebook 开源的向量检索库，纯本地，无服务
- **Milvus**：分布式向量数据库，生产级，但部署复杂

## 决策

选择 **ChromaDB** 作为向量数据库。

## 理由

1. **开发效率优先**
   - ChromaDB 一行代码就能跑起来：`chromadb.PersistentClient(path="./chroma_data")`
   - 不需要额外部署一个数据库服务
   - 对开发阶段来说，零运维成本

2. **本地优先的定位**
   - RAGForge 的目标是全本地运行，零 API 成本
   - ChromaDB 是嵌入式的，和 Python 进程一起跑，不需要独立服务
   - 符合"本地工具"的产品定位

3. **功能足够用**
   - 支持 cosine / L2 / IP 距离度量
   - 支持持久化存储
   - 支持元数据过滤
   - 对中小规模知识库（万级 chunk）性能足够

4. **为什么不选 pgvector？**
   - 开发阶段用 SQLite，没有 PostgreSQL
   - pgvector 需要额外部署 PostgreSQL 服务，增加复杂度
   - 如果后续需要生产部署，可以再切换到 pgvector（接口抽象已经做好了）

5. **为什么不选 Milvus？**
   - 太重了，需要部署一堆组件（etcd、MinIO、Milvus 本体）
   - 对一个本地工具来说过度工程化

## 后果

- 好处：开发快，部署简单，零运维
- 坏处：不支持分布式，不适合大规模（百万级 chunk）场景
- 未来：如果需要生产级部署，可以迁移到 pgvector 或 Milvus，检索层接口已经抽象好了

## 参考

- [ChromaDB 官方文档](https://docs.trychroma.com/)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
