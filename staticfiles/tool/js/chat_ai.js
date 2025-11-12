// chat_ai.js - AI 聊天功能核心逻辑
class AIChatBot {
    constructor() {
            // 延迟设置 config，确保 APP_CONFIG 已加载
            setTimeout(() => {
                this.config = window.APP_CONFIG || this.createDefaultConfig();
                console.log('AIChatBot 配置加载完成');
            }, 0);

            this.conversationHistory = [];
            this.isProcessing = false;
            this.onThinking = null;
            this.onError = null;
        }
        // 创建默认配置的备用方法
    createDefaultConfig() {
            return {
                SILICONFLOW_API_URL: 'https://api.siliconflow.cn/v1',
                SILICONFLOW_API_KEY: '',
                AI_MODEL: 'deepseek-ai/DeepSeek-V3.1-Terminus',
                AI_TEMPERATURE: 0.7,
                AI_MAX_TOKENS: 2000,
                AI_TOP_P: 0.9,
                validateConfig: function() {
                    return !!this.SILICONFLOW_API_KEY;
                }
            };
        }
        // 发送消息到 AI
    async sendMessage(userMessage) {
        // 检查配置
        if (!this.config.validateConfig()) {
            throw new Error('API 配置不完整，请先设置 API Key');
        }
        // 防止重复发送
        if (this.isProcessing) {
            throw new Error('正在处理上一个请求，请稍候...');
        }
        this.isProcessing = true;
        try {
            // 添加用户消息到对话历史
            this.conversationHistory.push({
                role: 'user',
                content: userMessage
            });
            // 显示思考中的状态
            if (this.onThinking) {
                this.onThinking();
            }

            // 准备请求数据 - 修正字段名拼写错误
            const requestData = {
                model: this.config.AI_MODEL, // 修正: modle -> model
                messages: this.conversationHistory, // 修正: message -> messages
                temperature: this.config.AI_TEMPERATURE, // 修正: TEPERATURE -> TEMPERATURE
                max_tokens: this.config.AI_MAX_TOKENS,
                top_p: this.config.AI_TOP_P,
                stream: false // 修正: fasle -> false
            };
            // 发送请求到硅基流动 API - 修正 URL 拼写错误
            const response = await fetch(this.config.SILICONFLOW_API_URL + '/chat/completions', { // 修正: SILICONFLOW_API_RUL -> SILICONFLOW_API_URL
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + this.config.SILICONFLOW_API_KEY, // 修复：去掉模板字符串语法错误
                    'Accept': 'application/json'
                },
                body: JSON.stringify(requestData)
            });
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error('API 请求失败: ' + response.status + ' - ' + errorText); // 修复：字符串连接
            }
            const data = await response.json(); // 添加: 解析响应数据
            const aiReply = data.choices[0] ? data.choices[0].message.content : ''; // 修复：去掉可选链操作符
            if (!aiReply) {
                throw new Error('AI 回复为空或格式不正确');
            }
            // 添加 AI 回复到对话历史
            this.conversationHistory.push({
                role: 'assistant',
                content: aiReply
            });
            return aiReply;
        } catch (error) {
            console.error('AI 请求错误:', error);
            // 从对话历史中移除失败的用户消息
            this.conversationHistory.pop();
            throw new Error('AI 服务暂时不可用: ' + error.message); // 修正: ErrorEvent -> Error
        } finally {
            this.isProcessing = false;
        }
    }

    // 清空对话历史
    clearHistory() {
        this.conversationHistory = [];
    }

    // 获取对话历史
    getHistory() {
        return [...this.conversationHistory];
    }

    // 设置对话历史
    setHistory(history) {
        this.conversationHistory = history;
    }

    // 回调函数设置
    onThinking(callback) {
        this.onThinking = callback;
    }

    onError(callback) {
        this.onError = callback;
    }
}

// 创建全局实例
window.aiChatBot = new AIChatBot();