// config.js - 从环境变量或默认值加载配置

window.APP_CONFIG = {
    // API 配置 - 使用 localStorage 或默认值
    SILICONFLOW_API_URL: localStorage.getItem('SILICONFLOW_API_URL') || 'https://api.siliconflow.cn/v1',
    SILICONFLOW_API_KEY: localStorage.getItem('SILICONFLOW_API_KEY') || '',
    AI_MODEL: localStorage.getItem('AI_MODEL') || 'deepseek-ai/DeepSeek-V3.1-Terminus',
    AI_TEMPERATURE: parseFloat(localStorage.getItem('AI_TEMPERATURE')) || 0.7,
    AI_MAX_TOKENS: parseInt(localStorage.getItem('AI_MAX_TOKENS')) || 2000,
    AI_TOP_P: parseFloat(localStorage.getItem('AI_TOP_P')) || 0.9,
    AI_STREAM: localStorage.getItem('AI_STREAM') === 'true' || false,

    // 验证配置
    validateConfig() {
        return !!this.SILICONFLOW_API_KEY;
    },

    // 设置 API Key（用于页面配置）
    setApiKey(apiKey) {
        this.SILICONFLOW_API_KEY = apiKey;
        localStorage.setItem('SILICONFLOW_API_KEY', apiKey);
        console.log('API Key 已保存到 localStorage');
    },

    // 获取配置信息（不包含敏感信息）
    getSafeConfig() {
        return {
            API_URL: this.SILICONFLOW_API_URL,
            AI_MODEL: this.AI_MODEL,
            AI_TEMPERATURE: this.AI_TEMPERATURE,
            AI_MAX_TOKENS: this.AI_MAX_TOKENS,
            AI_TOP_P: this.AI_TOP_P,
            isConfigured: !!this.SILICONFLOW_API_KEY
        };
    }
};