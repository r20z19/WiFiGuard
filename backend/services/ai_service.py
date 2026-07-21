import json
import urllib.request
import urllib.error
from database import get_db


# Provider configurations
PROVIDERS = {
    "deepseek": {
        "name": "DeepSeek",
        "url": "https://api.deepseek.com/v1/chat/completions",
        "model": "deepseek-chat",
    },
    "qwen": {
        "name": "通义千问",
        "url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "model": "qwen-plus",
    },
    "glm": {
        "name": "智谱GLM",
        "url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "model": "glm-4-flash",
    },
}


def get_config():
    conn = get_db()
    row = conn.execute("SELECT * FROM ai_config WHERE id = 1").fetchone()
    conn.close()
    if not row:
        return {"provider": "deepseek", "apiKey": "", "enabled": False}
    return {
        "provider": row["provider"],
        "apiKey": row["api_key"],
        "enabled": bool(row["enabled"]),
    }


def save_config(provider, api_key, enabled):
    conn = get_db()
    conn.execute(
        "UPDATE ai_config SET provider=?, api_key=?, enabled=? WHERE id=1",
        (provider, api_key, 1 if enabled else 0),
    )
    conn.commit()
    conn.close()
    return get_config()


def _call_ai(system_prompt, user_message):
    """Call the configured AI provider and return the response text."""
    config = get_config()
    if not config["enabled"] or not config["apiKey"]:
        return None, "AI 功能未启用或未配置 API Key"

    provider = PROVIDERS.get(config["provider"], PROVIDERS["deepseek"])

    body = {
        "model": provider["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.7,
        "max_tokens": 800,
    }

    req = urllib.request.Request(
        provider["url"],
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['apiKey']}",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            content = result["choices"][0]["message"]["content"]
            return content, None
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        try:
            err = json.loads(error_body)
            msg = err.get("error", {}).get("message", error_body[:200])
        except Exception:
            msg = error_body[:200] or f"HTTP {e.code}"
        return None, f"AI 调用失败 ({provider['name']}): {msg}"
    except Exception as e:
        return None, f"AI 调用异常: {str(e)[:200]}"


def interpret_alert(alert, frames=None):
    """Generate a natural-language interpretation of a security alert, with optional frame data."""
    system_prompt = """你是 WiFiGuard 无线安全系统的 AI 安全助手。请用通俗易懂的中文解读告警信息。
对于每条告警，请简要说明：
1. 这是什么攻击（用日常语言解释原理）
2. 对用户有什么影响（具体风险）
3. 如果有报文数据，结合报文分析攻击模式
4. 建议的处置措施（具体可操作）
回复控制在 200 字以内，语气友好专业。"""

    user_message = f"""请解读以下 WiFi 安全告警：
- 攻击类型：{alert.get('type', '未知')}
- 严重等级：{alert.get('severity', '未知')}
- 攻击源 MAC：{alert.get('sourceMac', alert.get('source_mac', '未知'))}
- 目标 MAC：{alert.get('targetMac', alert.get('target_mac', '无'))}
- 时间：{alert.get('timestamp', '未知')}
{f"- 处置建议：{alert.get('suggestion', '')}" if alert.get('suggestion') else ""}"""

    if frames:
        user_message += f"\n\n📡 相关报文数据：\n{json.dumps(frames, ensure_ascii=False, indent=2)}"

    return _call_ai(system_prompt, user_message)


def chat_advisor(question, context=""):
    """Chat with the AI security advisor."""
    system_prompt = f"""你是 WiFiGuard 无线安全系统的 AI 安全顾问。请根据用户的提问提供专业的 WiFi 安全建议。
当前系统状态：{context}

回答要求：
- 用通俗易懂的中文
- 给出具体可操作的建议
- 如果问题超出 WiFi 安全范围，礼貌说明你是 WiFi 安全专家
- 回复控制在 300 字以内"""

    return _call_ai(system_prompt, question)


def generate_report(summary):
    """Generate a comprehensive natural-language security report."""
    system_prompt = """你是 WiFiGuard 的安全报告生成助手。请根据提供的系统数据，生成一份专业、易懂的网络安全报告。
报告结构：
1. 📊 总体评估（一句话概括网络安全状况）
2. 🔴 主要威胁（列出最严重的威胁及其影响）
3. 📱 设备概况（在线设备数量和异常设备）
4. 🛡 防御状态（黑白名单、访问控制状态）
5. 💡 改进建议（3-5 条具体可操作的建议）
用自然段落形式书写，不要用列表。语气专业但友好，面向普通家庭/办公用户。控制在 500 字以内。"""

    user_message = json.dumps(summary, ensure_ascii=False, indent=2)
    return _call_ai(system_prompt, user_message)


def identify_device(device):
    """Infer the specific device type from its characteristics."""
    system_prompt = """你是 WiFiGuard 的设备识别专家。请根据提供的设备信息，推断这是什么样的设备。
请综合 MAC 厂商（OUI）、信号强度、连接时长、SSID 等信息进行推断。
请给出：
1. 设备大概率是什么（如 "iPhone 15 Pro"、"联想 ThinkPad"、"小米智能摄像头"、"TP-Link 路由器"）
2. 置信度（高/中/低）
3. 推断依据（简短一句话）
回复控制在 80 字以内。"""

    user_message = json.dumps(device, ensure_ascii=False, indent=2)
    return _call_ai(system_prompt, user_message)


def detect_anomalies(devices_data):
    """Analyze device behavior for anomalies using AI."""
    system_prompt = """你是 WiFiGuard 的异常行为检测专家。请综合分析设备列表和攻击数据，识别所有异常设备和行为。

分析优先级（从高到低）：
1. **攻击关联（最重要！）**：设备是否出现在攻击数据中？是攻击源还是攻击目标？涉及多少次攻击？什么类型？→ 这是最明确的异常信号
2. **信号强度**：是否异常弱（<-75dBm 可能来自室外/邻居）？
3. **连接时段**：是否在深夜等非常规时段？
4. **加密方式**：是否使用WEP/TKIP过时协议？
5. **系统标记**：是否已被系统标记为可疑？

判定规则：
- 设备是攻击源 → 至少 medium，若是严重攻击 → high
- 设备被多次攻击 → medium
- 信号<-80dBm 且无攻击关联 → low/medium
- 仅加密弱 → low

请返回 JSON 数组（只要异常设备）：
[{"device":"MAC","risk":"high/medium/low","issue":"简述15字","reason":"判断理由50-100字，引用具体数据","advice":"建议措施"}]"""

    # Build comprehensive context with attack data
    context = {
        "在线设备数": len(devices_data),
        "设备列表": devices_data,
        "活跃攻击数": devices_data[0].get("_alertCount", 0) if devices_data else 0,
        "设备攻击关联": devices_data[0].get("_attackContext", "") if devices_data else "",
    }
    user_message = json.dumps(context, ensure_ascii=False, indent=2)
    return _call_ai(system_prompt, user_message)

    user_message = json.dumps(devices_data, ensure_ascii=False, indent=2)
    return _call_ai(system_prompt, user_message)


def predict_threats(current_data):
    """Predict potential future threats based on current attack patterns."""
    system_prompt = """你是 WiFiGuard 攻击预测专家。根据提供的攻击数据评估风险并预测威胁。

规则：
1. 如果有活跃攻击 → riskLevel至少为medium；有高危/严重攻击 → riskLevel为high
2. 必须在 "reason" 字段中用具体数据解释判断依据（如"检测到3次Deauth攻击和1次钓鱼AP，攻击源持续活跃"）
3. 每条预测必须包含 "reason" 说明依据

返回JSON格式（严格遵守，不要markdown代码块）：
{"riskLevel":"high/medium/low","summary":"简短总结","reason":"详细理由100-150字，引用攻击次数、类型等具体数据","predictions":[{"threat":"威胁描述","probability":"高/中/低","target":"MAC或整体网络","reason":"预测依据50-80字","advice":"建议"}]}"""

    # Pass detailed attack data
    attack_detail = {
        "攻击总数": current_data.get("alertCount", 0),
        "攻击类型": current_data.get("alertTypes", []),
        "严重攻击数": current_data.get("criticalCount", 0),
        "高危攻击数": current_data.get("highCount", 0),
        "在线设备": current_data.get("deviceCount", 0),
        "可疑设备": current_data.get("suspiciousCount", 0),
        "攻击详情": current_data.get("alerts", [])[:20],
    }
    user_message = json.dumps(attack_detail, ensure_ascii=False, indent=2)
    return _call_ai(system_prompt, user_message)

    user_message = json.dumps(current_data, ensure_ascii=False, indent=2)
    return _call_ai(system_prompt, user_message)


def chat_with_context(messages, context=""):
    """Multi-turn chat with context."""
    config_ = get_config()
    if not config_["enabled"] or not config_["apiKey"]:
        return None, "AI 功能未启用或未配置 API Key"

    provider = PROVIDERS.get(config_["provider"], PROVIDERS["deepseek"])

    system_msg = {
        "role": "system",
        "content": f"你是 WiFiGuard 无线安全系统的 AI 安全顾问。请提供专业的 WiFi 安全建议。当前系统状态：{context}",
    }
    body = {
        "model": provider["model"],
        "messages": [system_msg] + messages,
        "temperature": 0.7,
        "max_tokens": 800,
    }

    req = urllib.request.Request(
        provider["url"],
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config_['apiKey']}",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"], None
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        try:
            err = json.loads(error_body)
            msg = err.get("error", {}).get("message", error_body[:200])
        except Exception:
            msg = error_body[:200] or f"HTTP {e.code}"
        return None, f"AI 调用失败 ({provider['name']}): {msg}"
    except Exception as e:
        return None, f"AI 调用异常: {str(e)[:200]}"
