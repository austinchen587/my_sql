// chat_ai.js - AI 聊天功能核心逻辑（支持上下文对话）
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

        // 初始化历史管理器
        this.historyManager = window.ChatHistoryManager ? new ChatHistoryManager() : null;
        if (this.historyManager) {
            console.log('对话历史管理器已初始化');
            this.loadConversationHistory();
        }

        // 上下文设置
        this.maxHistoryMessages = 10; // 最多保留最近的10条消息作为上下文
        this.includeSystemMessage = true; // 是否包含系统消息
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

    // 加载对话历史
    loadConversationHistory() {
        try {
            if (this.historyManager) {
                const savedHistory = this.historyManager.loadCurrentSessionHistory();
                if (savedHistory && savedHistory.length > 0) {
                    this.conversationHistory = savedHistory;
                    console.log(`✅ 已加载 ${savedHistory.length} 条历史消息`);
                }
            }
        } catch (error) {
            console.error('加载对话历史失败:', error);
        }
    }

    // 保存对话历史
    saveConversationHistory() {
        try {
            if (this.historyManager) {
                this.historyManager.saveChatHistory(this.conversationHistory);
                console.log('💾 对话历史已保存');
            }
        } catch (error) {
            console.error('保存对话历史失败:', error);
        }
    }

    // 构建上下文消息（限制数量，保留最近的对话）
    buildContextMessages(userMessage) {
        let messages = [];

        // 可选：添加系统消息（只在对话开始时添加一次）
        if (this.includeSystemMessage && this.conversationHistory.length === 0) {
            messages.push({
                role: 'system',
                content: '你是一个专业、友好的AI助手，请用清晰、准确的中文回答用户的问题。'
            });
        }

        // 添加历史消息（限制数量）
        const recentHistory = this.conversationHistory.slice(-this.maxHistoryMessages * 2);
        messages = messages.concat(recentHistory);

        // 添加当前用户消息
        messages.push({
            role: 'user',
            content: userMessage
        });

        console.log(`📝 构建上下文: ${messages.length} 条消息`, messages);
        return messages;
    }

    // 发送消息到 AI（支持上下文）
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
            // 构建包含上下文的消息
            const contextMessages = this.buildContextMessages(userMessage);

            // 显示思考中的状态
            if (this.onThinking) {
                this.onThinking();
            }

            // 准备请求数据
            const requestData = {
                model: this.config.AI_MODEL,
                messages: contextMessages,
                temperature: this.config.AI_TEMPERATURE,
                max_tokens: this.config.AI_MAX_TOKENS,
                top_p: this.config.AI_TOP_P,
                stream: false
            };

            // 发送请求到硅基流动 API
            const response = await fetch(this.config.SILICONFLOW_API_URL + '/chat/completions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + this.config.SILICONFLOW_API_KEY,
                    'Accept': 'application/json'
                },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error('API 请求失败: ' + response.status + ' - ' + errorText);
            }

            const data = await response.json();
            const aiReply = data.choices[0] ? data.choices[0].message.content : '';

            if (!aiReply) {
                throw new Error('AI 回复为空或格式不正确');
            }

            // 添加用户消息和AI回复到对话历史
            this.conversationHistory.push({
                role: 'user',
                content: userMessage
            });

            this.conversationHistory.push({
                role: 'assistant',
                content: aiReply
            });

            // 保存到本地存储
            this.saveConversationHistory();

            // 限制历史记录长度（防止内存过大）
            if (this.conversationHistory.length > this.maxHistoryMessages * 2 + 10) {
                this.conversationHistory = this.conversationHistory.slice(-this.maxHistoryMessages * 2);
                console.log('🗑️ 已清理过长的对话历史');
            }

            return aiReply;

        } catch (error) {
            console.error('AI 请求错误:', error);

            // 错误处理：不将失败的用户消息添加到历史
            throw new Error('AI 服务暂时不可用: ' + error.message);
        } finally {
            this.isProcessing = false;
        }
    }

    // 清空对话历史和存储
    clearHistory() {
        this.conversationHistory = [];

        if (this.historyManager) {
            this.historyManager.clearAllHistory();
        }

        console.log('🗑️ 对话历史已清空');
    }

    // 获取对话历史
    getHistory() {
        return [...this.conversationHistory];
    }

    // 设置对话历史
    setHistory(history) {
        this.conversationHistory = Array.isArray(history) ? [...history] : [];

        if (this.historyManager) {
            this.historyManager.saveChatHistory(this.conversationHistory);
        }
    }

    // 获取对话上下文摘要（调试用）
    getContextSummary() {
        return {
            totalMessages: this.conversationHistory.length,
            userMessages: this.conversationHistory.filter(msg => msg.role === 'user').length,
            assistantMessages: this.conversationHistory.filter(msg => msg.role === 'assistant').length,
            recentContext: this.conversationHistory.slice(-this.maxHistoryMessages * 2)
        };
    }

    // 设置上下文长度
    setMaxHistoryMessages(maxMessages) {
        this.maxHistoryMessages = Math.max(1, Math.min(maxMessages, 20)); // 限制在1-20条之间
        console.log(`📊 上下文长度设置为: ${this.maxHistoryMessages} 条消息`);
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