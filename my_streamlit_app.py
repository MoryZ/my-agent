import time
import streamlit as st

# 设置页面气场：宽屏、科技蓝主题
st.set_page_config(page_title="AI-Ops 智能日志诊断专家系统", layout="wide")

st.title("🛠 AI-Ops 智能日志诊断与自动化定位系统 (MVP Demo)")
st.caption("基于多模态大模型与 RAG 架构的分布式系统效能工具")

# 侧边栏：模拟环境配置（显得很专业）
st.sidebar.header("⚙️ 系统配置")
st.sidebar.selectbox("数据源连接", ["Grafana Loki (Mock)", "Kibana (Elasticsearch)"])
st.sidebar.selectbox("推理引擎后端", ["DeepSeek-R1 (混合云部署)", "Qwen2.5-Coder"])
st.sidebar.slider("RAG 检索相似度阈值", 0.0, 1.0, 0.75)

# 核心案例库
CASES = {
    "案例一：C端筛选接口 TiDB 全表扫描性能灾难": {
        "log": "2026-06-11 10:15:22 [TiKV-Query-Worker-1] WARN - [SQL_ID: 99c71a] Slow query detected. scan_detail: {total_process_keys: 15000000, rocksdb: {delete_skipped_count: 0}}, sql: SELECT * FROM content c JOIN content_tag ct ...",
        "source": "/* TiDB 关联查询 */\nSELECT * FROM content c \nLEFT JOIN content_content_tag cct ON c.id = cct.content_id \nLEFT JOIN content_tag ct ON cct.tag_id = ct.id \nWHERE ct.name = '保险产品';",
        "diagnosis": "### 🔍 故障根因\n分布式数据库 **TiDB** 优化器在处理多对多关联查询时执行计划走偏，未命中 `idx_tag_name` 索引，触发了对 `content_tag` 表的 **全表扫描（Table Scan）**，导致分布式存储节点（TiKV）间发生海量数据哈希关联，接口 RT 飙升至 3.2秒。\n\n### 💡 架构级修复方案\n1. **SQL 干预**：在查询中显式引入 `FORCE INDEX` 纠正优化器行为。\n2. **引入双向缓存**：利用 Redis 缓存高性能筛选标签关系，避免高频请求穿透至分布式数据库。\n\n```sql\n-- 修正后的 SQL\nSELECT * FROM content c FORCE INDEX(idx_content_id) ...\n```",
    },
    "案例二：多模态 AI 审核链路高并发线程阻塞故障": {
        "log": "2026-06-11 10:45:10 [http-nio-8080-exec-12] ERROR - Connection Pool Timeout. Active connections: 200, Tomcat thread pool exhausted while waiting for Core-AI-Service response.",
        "source": "// 原始同步调用代码\npublic ReviewResult reviewContent(Content c) {\n    // 同步调用内部算法团队的大模型接口，RT 平均达 1.5s\n    return aiServiceClient.syncVerify(c.getText(), c.getImageUrl()); \n}",
        "diagnosis": "### 🔍 故障根因\n系统在处理海量海报和文本审核时，后端**同步调用**了内部算法的多模态推理服务。由于 AI 推理（文生图/图生图/智能打标）天然属于高延迟（高RT）场景，导致 Tomcat 核心工作线程被长时间挂起，连接池瞬间爆满，引发系统雪崩。\n\n### 💡 架构级修复方案\n1. **异步解耦**：将同步审核改为基于 **RocketMQ 的异步消息队列** 处理，引入状态机管理内容状态。\n2. **流式交互优化**：前端引入 **流式输出（Streaming / SSE）**，实现处理结果的动态渐进式呈现，降低首字延迟（TTFB）。",
    },
}

# 页面布局：左右分栏
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📥 生产环境实时异常日志流 (Loki)")
    selected_case = st.selectbox("🎯 选择要触发诊断的典型故障案例：", list(CASES.keys()))

    st.code(CASES[selected_case]["log"], language="log")

    st.subheader("📑 自动化 RAG 召回的相关业务源码上下文")
    st.code(CASES[selected_case]["source"], language="java")

    trigger_btn = st.button("🚀 启动 AI Agent 故障多维诊断", type="primary")

with col2:
    st.subheader("🤖 AI-Ops 专家团故障诊断报告")
    if trigger_btn:
        with st.spinner("Agent 正在调用混合云模型进行思维链推理..."):
            # 模拟流式打印效果，增强视觉冲击力
            report_placeholder = st.empty()
            full_text = CASES[selected_case]["diagnosis"]
            current_text = ""
            for char in full_text:
                current_text += char
                report_placeholder.markdown(current_text)
                time.sleep(0.005)  # 逼真的流式效果
        st.success("✨ 诊断完成！修复策略已同步至运维知识库。")
    else:
        st.info("请在左侧点击按钮，触发大模型流式诊断演示。")