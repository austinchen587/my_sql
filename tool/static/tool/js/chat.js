// chat.js - 集成 AI 的主聊天界面逻辑
function initializeChat() {
    // DOM元素获取
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const messageArea = document.getElementById('message-area');
    const characterCount = document.getElementById('character-count');
    const clearButton = document.getElementById('clear-chat');
    const apiConfigBtn = document.getElementById('api-config-btn');
    

    // ==================== 新增：初始化历史管理器 ====================
    let historyManager = null;
    if (window.ChatHistoryManager) {
        historyManager = new ChatHistoryManager();
        console.log('历史管理器初始化成功');
    } else {
        console.warn('历史管理器未加载，历史保存功能将不可用');
    }
    // ==================== 新增结束 ====================





    // 检查是否所有必需的元素都存在
    if (!messageInput || !sendButton || !messageArea || !characterCount) {
        console.error('无法找到必需的DOM元素，请检查HTML结构');
        return;
    }

    // 配置
    const MAX_CHARACTERS = 1800;
    let isAIThinking = false;
    let thinkingElement = null;

    // ==================== 辅助函数定义 ====================

    // 更新字符计数
    function updateCharacterCount() {
        const count = messageInput.value.length;
        characterCount.textContent = `${count}/${MAX_CHARACTERS}`;
        characterCount.classList.toggle('text-danger', count > MAX_CHARACTERS * 0.9);
    }

    // 创建消息元素并添加到聊天区域
    function createMessageElement(text, type, senderName = null) {
        // 创建消息容器
        const messageElement = document.createElement('div');
        messageElement.className = `message ${type} ${type === 'thinking' ? 'thinking' : ''}`;
        
        // 创建头像
        const avatar = document.createElement('div');
        avatar.className = type === 'sent' 
            ? 'message-avatar bg-primary rounded-circle d-flex align-items-center justify-content-center'
            : type === 'thinking' 
            ? 'message-avatar bg-warning rounded-circle d-flex align-items-center justify-content-center'
            : 'message-avatar bg-success rounded-circle d-flex align-items-center justify-content-center';
        
        avatar.innerHTML = type === 'sent' 
            ? '<span class="text-white fw-bold">U</span>'
            : type === 'thinking'
            ? '<span class="text-white fw-bold">⚡</span>'
            : '<span class="text-white fw-bold">AI</span>';

        // 创建消息内容
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        // 添加发送者名称
        const sender = document.createElement('div');
        sender.className = 'message-sender';
        sender.textContent = senderName || (type === 'sent' ? '您' : 
                           type === 'thinking' ? 'AI 思考中...' : 'AI助手');

        // 添加消息文本
        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        
        if (type === 'thinking') {
            // 思考状态显示动画
            messageText.innerHTML = '<div class="thinking-dots"><span>.</span><span>.</span><span>.</span></div>';
        } else {
            messageText.textContent = text;
        }

        // 添加时间戳
        const time = document.createElement('div');
        time.className = 'message-time';
        time.textContent = new Date().toLocaleTimeString('zh-CN', {
            hour: '2-digit', 
            minute: '2-digit'
        });

        // 组装消息
        messageContent.appendChild(sender);
        messageContent.appendChild(messageText);
        messageContent.appendChild(time);

        messageElement.appendChild(avatar);
        messageElement.appendChild(messageContent);

        // 添加到聊天区域
        messageArea.appendChild(messageElement);

        // 滚动到底部显示最新消息
        messageArea.scrollTop = messageArea.scrollHeight;

        return messageElement;
    }

    // 显示思考状态
    function showThinking() {
        if (isAIThinking) return null;
        
        isAIThinking = true;
        thinkingElement = createMessageElement('', 'thinking');
        return thinkingElement;
    }

    // 隐藏思考状态
    function hideThinking() {
        if (thinkingElement) {
            thinkingElement.remove();
            thinkingElement = null;
        }
        isAIThinking = false;
    }

    // 清空聊天记录
    function clearChat() {
        messageArea.innerHTML = '';
        if (window.aiChatBot) {
            window.aiChatBot.clearHistory();
        }
        hideThinking();

        // ==================== 新增：创建新会话 ====================
    if (historyManager) {
        const newSessionId = historyManager.createNewSession();
        console.log('已创建新会话:', newSessionId);
    }
    // ==================== 新增结束 ====================
    }

    // 显示API配置界面
    function showApiConfig() {
        const currentApiKey = window.APP_CONFIG?.SILICONFLOW_API_KEY || '';
        const apiKey = prompt('请输入硅基流动 API Key:', currentApiKey);
        
        if (apiKey !== null) {
            if (window.APP_CONFIG) {
                window.APP_CONFIG.setApiKey(apiKey);
                alert('API Key 已保存');
            } else {
                alert('配置系统未加载，请刷新页面重试');
            }
        }
    }

    


    // ==================== 核心功能函数 ====================

    // 发送消息功能
    async function sendMessage() {

        console.log('sendMessage 函数被调用');
        const messageText = messageInput.value.trim();
        console.log('消息内容:', messageText);
        
        // 验证消息
        if (!messageText) {
            console.log('消息为空，取消发送');
            messageInput.focus();
            return;
        }

        if (messageText.length > MAX_CHARACTERS) {
            console.log('消息长度超限:', messageText.length);
            alert(`消息不能超过${MAX_CHARACTERS}个字符`);
            return;
        }
        console.log('开始发送消息流程...');

        // 检查AI功能是否可用
        if (!window.aiChatBot) {
            createMessageElement('AI功能未正确加载，请检查控制台错误信息', 'received');
            return;
        }

        // 检查API配置
        if (!window.APP_CONFIG?.SILICONFLOW_API_KEY) {
            createMessageElement('请先配置API Key（点击右上角设置按钮）', 'received');
            return;
        }

        // 添加用户消息
        createMessageElement(messageText, 'sent');

        // 清空输入框并更新计数
        messageInput.value = '';
        updateCharacterCount();

        // 显示思考状态
        const thinkingElement = showThinking();

        try {
            // 发送到AI
            const aiReply = await window.aiChatBot.sendMessage(messageText);
            
            // 隐藏思考状态，显示AI回复
            hideThinking();
            createMessageElement(aiReply, 'received');
            // ==================== 新增：保存历史记录 ====================
        if (historyManager && window.aiChatBot) {
            const currentHistory = window.aiChatBot.getHistory();
            historyManager.saveChatHistory(currentHistory);
            console.log('对话历史已保存');
        }
        // ==================== 新增结束 ====================

        } catch (error) {
            // 处理错误
            hideThinking();
            createMessageElement(`错误: ${error.message}`, 'received');
            console.error('发送消息失败:', error);
        }

        // 焦点回到输入框
        messageInput.focus();
    }

    // ==================== 新增：页面加载时恢复历史记录 ====================
function restoreChatHistory() {
    console.log('🔍 开始恢复历史记录...');
    console.log('历史管理器状态:', !!historyManager);
    console.log('AI聊天机器人状态:', !!window.aiChatBot);
    
    if (historyManager && window.aiChatBot) {
        const savedHistory = historyManager.loadCurrentSessionHistory();
        console.log('加载到的历史记录:', savedHistory);
        
        if (savedHistory && savedHistory.length > 0) {
            // 设置到 AI 聊天机器人
            window.aiChatBot.setHistory(savedHistory);
            
            // 清空当前消息区域
            messageArea.innerHTML = '';
            
            // 重新渲染消息到界面（跳过系统消息）
            savedHistory.forEach(message => {
                if (message.role === 'user') {
                    createMessageElement(message.content, 'sent');
                } else if (message.role === 'assistant') {
                    createMessageElement(message.content, 'received');
                }
            });
            
            console.log('✅ 已恢复历史记录:', savedHistory.length, '条消息');
            
            // 滚动到底部
            messageArea.scrollTop = messageArea.scrollHeight;
        } else {
            console.log('ℹ️ 没有历史记录需要恢复');
        }
    } else {
        console.error('❌ 无法恢复历史记录：依赖未就绪');
    }
}
// ==================== 新增结束 ====================







    // ==================== 事件监听器设置 ====================

    // 发送按钮点击事件
    sendButton.addEventListener('click', sendMessage);

    // 输入框事件
    messageInput.addEventListener('input', updateCharacterCount);

    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // 清空聊天按钮
    if (clearButton) {
        clearButton.addEventListener('click', clearChat);
    }

    // API配置按钮
    if (apiConfigBtn) {
        apiConfigBtn.addEventListener('click', showApiConfig);
    }

    // ==================== 初始化设置 ====================

    // 页面加载后焦点自动放在输入框
    messageInput.focus();
    updateCharacterCount();

    // 恢复历史记录
    // 延迟恢复历史记录，确保 aiChatBot 已初始化
setTimeout(() => {
    console.log('🔄 延迟恢复历史记录...');
    if (window.aiChatBot && historyManager) {
        restoreChatHistory();
    } else {
        console.warn('⚠️ AI聊天机器人未就绪，无法恢复历史记录');
    }
}, 500);

    // 检查配置状态
    setTimeout(() => {
    if (!window.APP_CONFIG?.SILICONFLOW_API_KEY) {
        console.warn('请先配置API Key');
        // 可以在这里添加一个提示消息
        setTimeout(() => {
            createMessageElement('请点击右上角设置按钮配置API Key以启用AI聊天功能', 'received');
        }, 1500);
    } else {
        console.log('✅ API Key 已配置，准备恢复历史记录');
        // 延迟恢复历史记录
        setTimeout(() => {
            if (window.aiChatBot && historyManager) {
                restoreChatHistory();
            }
        }, 800);
    }
}, 300);
}



// ==== 修改这部分代码（文件末尾）====

// ==== 简化的初始化逻辑 ====
console.log('chat.js 开始加载');
// 等待所有脚本加载完成
function initializeWhenReady() {
    console.log('检查依赖状态:', {
        APP_CONFIG: !!window.APP_CONFIG,
        aiChatBot: !!window.aiChatBot
    });
    
    if (window.APP_CONFIG && window.aiChatBot) {
        console.log('所有依赖已加载，开始初始化聊天界面');
        // 确保 aiChatBot 使用正确的配置
        if (window.aiChatBot && window.aiChatBot.config !== window.APP_CONFIG) {
            window.aiChatBot.config = window.APP_CONFIG;
        }
        initializeChat();
    } else {
        console.log('等待依赖加载...');
        setTimeout(initializeWhenReady, 100);
    }
}
// 页面加载后开始初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeWhenReady);
} else {
    initializeWhenReady();
}