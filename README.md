# AI智能记账APP - BookKeeping

基于DeepSeek大模型开发的跨平台智能记账应用，彻底解决传统记账工具操作繁琐、效率低下的痛点，实现"说话即记账"和"一键导入自动整理"的极致体验。

## ✨ 核心功能
- 🎙️ **语音记账**：按住说话自动识别，AI提取时间、金额、分类生成账单
- 💬 **自然语言记账**：像聊天一样记账，支持"今天中午吃海底捞花了380"这种口语化描述
- 📊 **批量导入账单**：支持支付宝、微信导出的CSV/Excel格式账单，AI自动过滤退款、转账等干扰项并分类
- 🤖 **AI财务分析**：基于历史账单生成个性化消费分析和优化建议
- 📈 **多维度报表**：支持周/月/年收支统计，环形图展示消费构成
- 🔒 **纯本地存储**：所有数据保存在用户设备本地，无需注册登录，保护财务隐私

## 🛠️ 技术栈
### 前端
- 框架：uni-app + Vue3
- 开发工具：HBuilderX
- 语音识别：百度语音识别SDK
- 数据存储：uni-app本地缓存

### 后端
- 框架：Python Flask
- AI引擎：DeepSeek-chat大模型API
- 文件处理：Pandas（Excel解析）

## 🚀 快速开始
### 1. 后端启动
```bash
# 安装依赖
pip install flask flask-cors requests pandas openpyxl

# 替换为你自己的DeepSeek API Key
# 打开 bookkeeping_backend.py，修改 DEEPSEEK_API_KEY 变量
DEEPSEEK_API_KEY = "你的DeepSeek API Key"

# 启动后端服务
python bookkeeping_backend.py
