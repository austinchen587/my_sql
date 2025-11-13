// 在文件开头添加Markdown工具函数
// Markdown渲染器类
class MarkdownRenderer {
    static render(markdownText) {
        if (!markdownText) return '';
        
        try {
            // 配置marked选项
            marked.setOptions({
                breaks: true,
                gfm: true,
                tables: true,
                sanitize: false // 使用DOMPurify进行清理
            });
            
            const rawHtml = marked.parse(markdownText);
            const cleanHtml = DOMPurify.sanitize(rawHtml);
            return cleanHtml;
        } catch (error) {
            console.error('Markdown渲染错误:', error);
            return `<div class="alert alert-warning">渲染错误: ${error.message}</div>`;
        }
    }
    
    static isMarkdown(text) {
        if (!text || typeof text !== 'string') return false;
        
        const markdownPatterns = [
            /^#+\s/, // 标题
            /\*\*.+?\*\*/, // 粗体
            /\*.+?\*/, // 斜体
            /\[.+\]\(.+\)/, // 链接
            /^- /, // 列表
            /`[^`]+`/, // 行内代码
            /```[\s\S]*?```/, // 代码块
            /\|.+\|/, // 表格
            />\s+.+/ // 引用
        ];
        
        return markdownPatterns.some(pattern => pattern.test(text));
    }
}




// chat.js - 集成 AI 的主聊天界面逻辑
// 主聊天初始化函数
function initializeChat() {
    // DOM元素获取
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const messageArea = document.getElementById('message-area');
    const characterCount = document.getElementById('character-count');
    const clearButton = document.getElementById('clear-chat');
    const apiConfigBtn = document.getElementById('api-config-btn');
    // 初始化历史管理器
    let historyManager = null;
    if (window.ChatHistoryManager) {
        historyManager = new ChatHistoryManager();
        console.log('历史管理器初始化成功');
    } else {
        console.warn('历史管理器未加载，历史保存功能将不可用');
    }
    // 检查必需元素
    if (!messageInput || !sendButton || !messageArea || !characterCount) {
        console.error('无法找到必需的DOM元素，请检查HTML结构');
        return;
    }
    // 配置
    const MAX_CHARACTERS = 1800;
    let isAIThinking = false;
    let thinkingElement = null;
    // 更新字符计数
    function updateCharacterCount() {
        const count = messageInput.value.length;
        characterCount.textContent = `${count}/${MAX_CHARACTERS}`;
        characterCount.classList.toggle('text-danger', count > MAX_CHARACTERS * 0.9);
    }
    // 创建消息元素（支持Markdown）
    function createMessageElement(text, type, senderName = null, isFormatted = false) {
    const messageElement = document.createElement('div');
    messageElement.className = `message ${type}`;
    const avatar = document.createElement('div');
    avatar.className = type === 'sent' 
        ? 'message-avatar bg-primary rounded-circle d-flex align-items-center justify-content-center'
        : 'message-avatar bg-success rounded-circle d-flex align-items-center justify-content-center';
    avatar.innerHTML = type === 'sent' 
        ? '<span class="text-white fw-bold">👤</span>'
        : '<span class="text-white fw-bold">🤖</span>';
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    const sender = document.createElement('div');
    sender.className = 'message-sender';
    sender.textContent = senderName || (type === 'sent' ? '您' : 'AI助手');
    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    if (type === 'thinking') {
        messageText.innerHTML = '<div class="thinking-dots"><span></span><span></span><span></span></div>';
    } else if (isFormatted || 
               (typeof text === 'string' && 
                (text.includes('<div') || 
                 text.includes('class=') || 
                 text.trim().startsWith('<') && text.includes('>') || 
                 MarkdownRenderer.isMarkdown(text)))) {
        // 如果是HTML内容或Markdown，直接渲染
        if (text.trim().startsWith('<') && text.includes('>')) {
            // 直接HTML内容
            messageText.innerHTML = DOMPurify.sanitize(text);
        } else {
            // Markdown内容
            messageText.innerHTML = MarkdownRenderer.render(text);
        }
    } else {
        // 纯文本内容
        messageText.textContent = text;
    }
    const time = document.createElement('div');
    time.className = 'message-time';
    time.textContent = new Date().toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
    });
    messageContent.appendChild(sender);
    messageContent.appendChild(messageText);
    messageContent.appendChild(time);
    messageElement.appendChild(avatar);
    messageElement.appendChild(messageContent);
    messageArea.appendChild(messageElement);
    messageArea.scrollTop = messageArea.scrollHeight;
    return messageElement;
}
    // 显示思考状态
    function showThinking() {
        if (isAIThinking) return null;
        isAIThinking = true;
        
        const thinkingElement = document.createElement('div');
        thinkingElement.className = 'message thinking';
        thinkingElement.innerHTML = `
            <div class="message-avatar bg-warning rounded-circle d-flex align-items-center justify-content-center">
                <span class="text-white fw-bold">⚡</span>
            </div>
            <div class="message-content">
                <div class="message-sender">AI思考中...</div>
                <div class="message-text">
                    <div class="thinking-dots"><span></span><span></span><span></span></div>
                </div>
                <div class="message-time">${new Date().toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit'})}</div>
            </div>
        `;
        
        messageArea.appendChild(thinkingElement);
        messageArea.scrollTop = messageArea.scrollHeight;
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
        if (confirm('确定要清空当前对话吗？')) {
            messageArea.innerHTML = '';
            // 保留欢迎消息
            const welcomeMsg = `
                <div class="message received">
                    <div class="message-avatar bg-success rounded-circle d-flex align-items-center justify-content-center">
                        <span class="text-white fw-bold">🤖</span>
                    </div>
                    <div class="message-content">
                        <div class="message-sender">AI助手</div>
                        <div class="message-text">
                            <h4>👋 对话已清空</h4>
                            <p>请开始新的对话吧！</p>
                        </div>
                        <div class="message-time">${new Date().toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit'})}</div>
                    </div>
                </div>
            `;
            messageArea.innerHTML = welcomeMsg;
            
            if (window.aiChatBot) {
                window.aiChatBot.clearHistory();
            }
            
            if (historyManager) {
                const newSessionId = historyManager.createNewSession();
                console.log('已创建新会话:', newSessionId);
            }
        }
    }
    // API配置
    function showApiConfig() {
        const currentApiKey = (window.APP_CONFIG && window.APP_CONFIG.SILICONFLOW_API_KEY) || '';
        const apiKey = prompt('请输入硅基流动 API Key:', currentApiKey);
        if (apiKey !== null) {
            if (window.APP_CONFIG) {
                window.APP_CONFIG.setApiKey(apiKey);
                alert('API Key 已保存');
                location.reload();
            } else {
                alert('配置系统未加载，请刷新页面重试');
            }
        }
    }
    // 发送消息
    async function sendMessage() {
        const messageText = messageInput.value.trim();
        
        if (!messageText) {
            messageInput.focus();
            return;
        }
        if (messageText.length > MAX_CHARACTERS) {
            alert(`消息不能超过${MAX_CHARACTERS}个字符`);
            return;
        }
        if (!window.ChatMessageHandler) {
            createMessageElement('消息处理功能未正确加载', 'received');
            return;
        }
        // 添加用户消息
        createMessageElement(messageText, 'sent');
        messageInput.value = '';
        updateCharacterCount();
        thinkingElement = showThinking();
        try {
            const aiReply = await window.ChatMessageHandler.handleUserMessage(messageText);
            hideThinking();
            // 检查是否为格式化内容
            const isFormatted = typeof aiReply === 'string' && (
                aiReply.includes('<div') || 
                aiReply.includes('class=') ||
                MarkdownRenderer.isMarkdown(aiReply)
            );
            
            createMessageElement(aiReply, 'received', null, isFormatted);
            // 保存历史记录
            if (historyManager) {
                const newHistoryEntry = [
                    { role: 'user', content: messageText },
                    { role: 'assistant', content: aiReply }
                ];
                const currentHistory = historyManager.loadCurrentSessionHistory();
                const updatedHistory = [...currentHistory, ...newHistoryEntry];
                historyManager.saveChatHistory(updatedHistory);
            }
        } catch (error) {
            hideThinking();
            createMessageElement(`错误: ${error.message}`, 'received');
            console.error('发送消息失败:', error);
        }
        messageInput.focus();
    }
    // 恢复历史记录
    function restoreChatHistory() {
        if (historyManager && window.aiChatBot) {
            const savedHistory = historyManager.loadCurrentSessionHistory();
            if (savedHistory && savedHistory.length > 0) {
                window.aiChatBot.setHistory(savedHistory);
                
                // 重新渲染历史消息
                savedHistory.forEach(message => {
                    if (message.role === 'user') {
                        createMessageElement(message.content, 'sent');
                    } else if (message.role === 'assistant') {
                        const isFormatted = typeof message.content === 'string' && (
                            message.content.includes('<div') || 
                            message.content.includes('class=') ||
                            MarkdownRenderer.isMarkdown(message.content)
                        );
                        createMessageElement(message.content, 'received', null, isFormatted);
                    }
                });
                
                console.log('✅ 已恢复历史记录:', savedHistory.length, '条消息');
            }
        }
    }
    // 事件监听
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('input', updateCharacterCount);
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    if (clearButton) clearButton.addEventListener('click', clearChat);
    if (apiConfigBtn) apiConfigBtn.addEventListener('click', showApiConfig);
    // 初始化
    messageInput.focus();
    updateCharacterCount();
    
    // 延迟恢复历史记录
    setTimeout(() => {
        if (window.aiChatBot && historyManager) {
            restoreChatHistory();
        }
    }, 1000);
}
// 启动函数
console.log('chat.js 开始加载');
function initializeWhenReady() {
    if (window.APP_CONFIG && window.aiChatBot) {
        console.log('所有依赖已加载，开始初始化聊天界面');
        if (window.aiChatBot.config !== window.APP_CONFIG) {
            window.aiChatBot.config = window.APP_CONFIG;
        }
        initializeChat();
    } else {
        setTimeout(initializeWhenReady, 100);
    }
}
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeWhenReady);
} else {
    initializeWhenReady();
}