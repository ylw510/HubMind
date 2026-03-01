# DeepSeek API 配置指南

DeepSeek 是 HubMind 的默认 LLM 提供商，具有高性价比、优秀的中文支持和强大的代码生成能力。

## 快速配置

### 1. 获取 API Key

1. 访问 [DeepSeek 平台](https://platform.deepseek.com/)
2. 注册/登录账号
3. 进入 API Keys 页面
4. 创建新的 API Key
5. 复制 API Key

### 2. 配置环境变量

在项目根目录的 `.env` 文件中添加：

```env
# LLM Provider Configuration
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat

# DeepSeek API Configuration
DEEPSEEK_API_KEY=sk-your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

### 3. 验证配置

```bash
python3 -c "from config import Config; Config.validate(); print('✅ 配置验证成功！')"
```

## 使用方法

### CLI 模式

```bash
# 查看今日热门项目
python main.py trending

# 交互式对话
python main.py interactive
```

### 交互式对话示例

```bash
python main.py interactive
```

然后输入：
```
You: 给我看看今天最火的 5 个 Python 项目
HubMind: [显示结果]

You: microsoft/vscode 今天有什么重要的 PR 吗？
HubMind: [显示有价值的 PR]
```

## 故障排除

### 错误: DEEPSEEK_API_KEY is required

- 检查 `.env` 文件中是否设置了 `DEEPSEEK_API_KEY`
- 确保 API Key 有效且有余额
- 验证 API Key 格式：应以 `sk-` 开头

### API 调用失败

- 检查网络连接
- 确认 API Key 有效且有余额
- 查看 DeepSeek 平台服务状态
- 检查 API 调用频率限制

### 验证 API Key

```bash
# 使用 curl 测试 API Key
curl https://api.deepseek.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## 优势

- **性价比高** - 价格实惠，适合大量使用
- **中文支持优秀** - 对中文理解能力强
- **代码能力强** - 代码生成和理解能力出色
- **OpenAI 兼容** - 使用 OpenAI 兼容 API，易于集成

## 更多信息

- [DeepSeek 官方文档](https://platform.deepseek.com/docs)
- [LLM 支持说明](../LLM_SUPPORT.md) - 查看其他 LLM 提供商配置
