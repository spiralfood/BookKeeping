import base64
import os
import json
import io
import requests
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# 允许跨域请求，让手机端能够访问得到
CORS(app)

# 你的 DeepSeek API Key
DEEPSEEK_API_KEY = "DeepSeek API Key"
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

@app.route('/api/bill/import_base64', methods=['POST'])
def import_bill():
    try:
        data = request.json
        file_name = data.get('fileName', '')
        base64_data = data.get('fileData', '')

        if not base64_data:
            return jsonify({"success": False, "message": "没有收到文件数据"})

        # frontend 的 base64 通常带有头部 "data:text/csv;base64,xxxxx"
        if ',' in base64_data:
            base64_data = base64_data.split(',')[1]

        # 1. 解码文件字节流
        file_bytes = base64.b64decode(base64_data)
        
        # 兼容 Excel 格式（.xlsx / .xls），转换为 CSV 文本
        if file_name.endswith('.xlsx') or file_name.endswith('.xls'):
            print(f"正在使用 Pandas 解析 Excel 文件: {file_name}")
            df = pd.read_excel(io.BytesIO(file_bytes))
            csv_content = df.to_csv(index=False)
        else:
            # 默认为 CSV 解码
            csv_content = file_bytes.decode('utf-8', errors='ignore')

        # 2. 截取部分内容，防止 token 超出（实际应用中可以做更复杂的行列解析筛选核心字段）
        # 这里为了演示，取前 100 行
        lines = csv_content.split('\n')
        truncated_csv = '\n'.join(lines[:100])

        # 3. 构造 DeepSeek 的 Prompt
        system_prompt = """
        你是一个拥有超强逻辑的【智能财务管家】。
        用户会提供一段从支付宝或微信导出的 CSV 账单。
        你需要剔除掉那些用于退款、资金流转但不属于实际消费/收入的干扰项。
        请将真实有效的消费和收入账单提取出来，并尝试分类（餐饮美食、交通出行、日常百货、工资收入等）。
        请务必只返回标准的 JSON 数组格式，不要有任何多余的 Markdown 标记或其它寒暄文字。
        示例格式:
        [
          {"time": "2024-05-17 12:30", "desc": "海底捞", "category": "餐饮美食", "type": "expense", "amount": 380},
          {"time": "2024-05-16 08:30", "desc": "滴滴出行", "category": "交通出行", "type": "expense", "amount": 15}
        ]
        """

        # 4. 请求 DeepSeek 接口
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"以下是账单名称 {file_name} 的内容：\n{truncated_csv}"}
            ],
            "temperature": 0.1 # 降低温度保证输出稳定的结构化数据
        }

        print("正在请求 DeepSeek 大模型分析账单...")
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        result_data = response.json()
        ai_reply = result_data['choices'][0]['message']['content'].strip()

        # 尝试清理 AI 可能带上的 ```json ... ``` 标记
        if ai_reply.startswith("```"):
            # 简单去除首尾的 markdown 代码块
            ai_reply = "\n".join(ai_reply.split('\n')[1:-1])

        # 解析为 Python 对象以验证
        parsed_bills = json.loads(ai_reply)

        print(f"DeepSeek 解析成功！共找到 {len(parsed_bills)} 条有效账单。")

        return jsonify({
            "success": True,
            "code": 200,
            "count": len(parsed_bills),
            "data": parsed_bills
        })

    except Exception as e:
        print("处理过程中出现异常:", e)
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/chat/text_to_bill', methods=['POST'])
def text_to_bill():
    try:
        data = request.json
        text = data.get('text', '')

        if not text:
            return jsonify({"success": False, "message": "没有收到文字内容"})

        system_prompt = """
        你是一个拥有超强逻辑且懂生活的【智能财务管家】。
        你需要分析用户的输入意图，并严格返回 JSON 格式数据。
        
        情况1：用户在记账（如“今天吃海底捞花了380”）
        请将其解析为账单记录，返回格式：
        {
          "type": "bill",
          "message": "已为您记下这笔账！",
          "bills": [
             {"time": "2024-05-17 12:30", "desc": "海底捞", "category": "餐饮美食", "type": "expense", "amount": 380}
          ]
        }
        
        情况2：用户在问候（如“你好”），或者询问当季物价行情、理财建议（如“现在西红柿多少钱一斤”、“猪肉怎么卖”）
        请结合当前时间和常识给出合理的估价或随和的回复，返回格式：
        {
          "type": "chat",
          "message": "按照当前行情，西红柿大概在 3-5元/斤 左右。需要我帮您记下买菜的开销吗？",
          "bills": []
        }
        
        请务必只返回合法的 JSON 对象，不要有 Markdown 格式的包裹，不要其它额外文字。
        """
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"当前系统时间为 {current_time}。用户说：{text}"}
            ],
            "temperature": 0.1
        }

        print(f"正在请求 DeepSeek 分析对话: {text}...")
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        result_data = response.json()
        ai_reply = result_data['choices'][0]['message']['content'].strip()

        if ai_reply.startswith("```"):
            if "```json" in ai_reply:
                ai_reply = ai_reply.replace("```json", "").replace("```", "").strip()
            else:
                ai_reply = "\n".join(ai_reply.split('\n')[1:-1])

        parsed_result = json.loads(ai_reply)

        print(f"DeepSeek 解析成功！")

        return jsonify({
            "success": True,
            "code": 200,
            "data": parsed_result
        })

    except Exception as e:
        print("文字转账单异常:", e)
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/chat/analyze_bills', methods=['POST'])
def analyze_bills():
    try:
        data = request.json
        bills = data.get('bills', [])
        date_text = data.get('dateText', '这段时间')

        if not bills:
            return jsonify({"success": False, "message": "没有账单数据"})
        
        # 简单统计一下传入的账单
        expense_total = 0
        income_total = 0
        cat_map = {}
        for b in bills:
            amount = float(b.get('amount', 0))
            b_type = b.get('type', '')
            if b_type == 'income' or b_type == '收入' or amount < 0:
                income_total += abs(amount)
            else:
                expense_total += abs(amount)
                cat = b.get('category', '其他')
                cat_map[cat] = cat_map.get(cat, 0) + abs(amount)

        summary_text = f"时间范围：{date_text}\n总支出：{expense_total}元，总收入：{income_total}元。\n各项支出统计：\n"
        for k, v in cat_map.items():
            summary_text += f"- {k}: {v}元\n"
            
        system_prompt = """
        你是一个拥有专业财务知识的【智能账房管家】。
        用户会提供他们最近的账单汇总数据（包含总收支和各项支出分类金额）。
        请你给出一份专属的财务分析与优化清单。语气要像一个贴心、专业的管家。
        可以指出开销最大的部分，给出一些省钱小建议或理财建议。
        回复请直接输出分析的正文，不需要输出各种代码块或markdown表格。控制在200字以内，简明扼要。
        """
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"管家你好，帮我分析一下：\n{summary_text}"}
            ],
            "temperature": 0.4
        }

        print(f"正在分析 {date_text} 账单数据...")
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        result_data = response.json()
        ai_reply = result_data['choices'][0]['message']['content'].strip()

        print(f"DeepSeek 分析完成！")
        return jsonify({
            "success": True,
            "code": 200,
            "data": ai_reply
        })

    except Exception as e:
        print("账单分析异常:", e)
        return jsonify({"success": False, "message": str(e)})

if __name__ == '__main__':
    # 监听 0.0.0.0 以便手机在局域网内可以访问电脑
    print("AI 账单解析后端启动！请在 profile.vue 中将 IP 替换为你的局域网 IP。")
    app.run(host='0.0.0.0', port=5000, debug=True)