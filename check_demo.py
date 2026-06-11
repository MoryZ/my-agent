import json
import requests

# 1. 配置参数
OLLAMA_URL = "http://localhost:11434/api/generate"
CLASSIFY_MODEL = "gemma3:4b"  # 快速分类
CODER_MODEL = "qwen2.5-coder:14b"  # 核心诊断

# 模拟从 Loki 拉取到的一条待处理日志
mock_loki_log = (
    "2026-06-10 20:15:32.124 [http-nio-8080-exec-3] ERROR c.s.content.service.impl.ContentServiceImpl "
    "- [ContentId: 10293] Failed to process content matching. NullPointerException at ContentServiceImpl.java:45"
)

# 模拟本地 RAG 检索出来的业务源码上下文
mock_source_code_context = """
public class ContentServiceImpl implements ContentService {
    @Override
    public ContentVo getAndMatchTags(Long contentId) {
        Content content = contentRepository.findById(contentId); // 查数据库
        List<Tag> tags = tagService.getTagsByContentId(contentId);
        
        // 第45行：如果内容被下架，content可能为null，直接调用导致NPE
        if (content.getStatus() == ContentStatus.PUBLISHED) { 
            return convertToVo(content, tags);
        }
        return null;
    }
}
"""

# 🚀 步骤一：使用快思考模型 (Gemma3) 进行日志自动分类与打标签
def classify_and_tag(log_line):
    prompt = f"""
    你是一个自动化运维网关。请分析以下单行日志，提取其【服务名】、【异常类型】，并判定是否需要研发介入（TRUE/FALSE）。
    严格以 JSON 格式输出，不要包含任何多余的解释。
    
    日志: {log_line}
    """

    payload = {"model": CLASSIFY_MODEL, "prompt": prompt, "stream": False, "format": "json"}
    response = requests.post(OLLAMA_URL, json=payload)
    return json.loads(response.json()["response"])

# 🚀 步骤二：使用核心代码模型 (Qwen2.5-Coder) 进行故障深度诊断
def diagnose_fault(log_line, code_context):
    prompt = f"""
    你是一个资深的 Java 后端架构师与高级专家。
    请结合生产环境的【Loki 错误日志】和检索出的【相关业务源码】，指出根本原因并给出修复方案（代码 Patch）。
    
    【Loki 错误日志】: {log_line}
    【相关业务源码】: {code_context}
    """

    payload = {"model": CODER_MODEL, "prompt": prompt, "stream": True}  # 开启流式输出
    response = requests.post(OLLAMA_URL, json=payload, stream=True)

    print("\n💡 [AI 诊断专家团] 正在为您流式输出故障分析报告：\n" + "="*50 + "\n")
    for line in response.iter_lines():
        if line:
            chunk = json.loads(line.decode("utf-8"))
            print(chunk.get("response", ""), end="", flush=True)
    print("\n" + "="*50)

# 🏃 执行闭环流程
if __name__ == "__main__":
    # 1. 过滤分类
    tag_result = classify_and_tag(mock_loki_log)
    print("📌 日志自动化打标结果:", json.dumps(tag_result, ensure_ascii=False, indent=2))

    # 2. 如果需要研发介入，触发深度诊断
    if tag_result.get("需要研发介入") or tag_result.get("need_developer", True):
        diagnose_fault(mock_loki_log, mock_source_code_context)