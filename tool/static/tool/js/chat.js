// tool/static/tool/js/chat.js
console.log('🚀 chat.js 开始加载');

// HTML转义函数 - 移到全局作用域顶部
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function initializeChat() {
    console.log('🔧 开始初始化聊天功能');

    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const messageArea = document.getElementById('message-area');
    const clearButton = document.getElementById('clear-chat');

    console.log('📋 元素获取状态:', {
        messageInput: !!messageInput,
        sendButton: !!sendButton,
        messageArea: !!messageArea,
        clearButton: !!clearButton
    });

    // 检查关键元素是否存在
    if (!messageInput || !sendButton || !messageArea) {
        console.error('❌ 关键元素未找到，延迟重试...');
        setTimeout(initializeChat, 500);
        return;
    }

    // 检查ChatMessageHandler是否已加载
    if (typeof window.ChatMessageHandler === 'undefined') {
        console.error('❌ ChatMessageHandler未加载，延迟重试...');
        setTimeout(initializeChat, 500);
        return;
    }

    console.log('✅ 所有依赖项检查通过');

    async function sendMessage() {
        const messageText = messageInput.value.trim();
        console.log('📤 准备发送消息:', messageText);

        if (!messageText) {
            console.log('⏹️ 消息为空，不发送');
            return;
        }

        // 禁用发送按钮防止重复发送
        sendButton.disabled = true;

        // 添加用户消息到界面
        createMessageElement(messageText, 'sent');
        messageInput.value = '';
        updateButtonState();

        try {
            console.log('🚀 调用ChatMessageHandler...');
            const response = await window.ChatMessageHandler.handleUserMessage(messageText);
            console.log('✅ 收到响应:', response);
            createMessageElement(response, 'received', true);
        } catch (error) {
            console.error('❌ 处理消息时出错:', error);
            createMessageElement(`错误: ${error.message}`, 'received');
        } finally {
            // 重新启用发送按钮
            sendButton.disabled = false;
            messageInput.focus();
        }
    }

    function createMessageElement(text, type, isFormatted = false) {
        console.log(`📝 创建消息元素，类型: ${type}`);

        const messageElement = document.createElement('div');
        messageElement.className = `message ${type}`;

        const displayText = isFormatted ? text : escapeHtml(text);

        messageElement.innerHTML = `
            <div class="message-avatar bg-${type === 'sent' ? 'primary' : 'success'} rounded-circle">
                <span>${type === 'sent' ? '👤' : '🤖'}</span>
            </div>
            <div class="message-content">
                <div class="message-sender">${type === 'sent' ? '您' : 'AI助手'}</div>
                <div class="message-text">${displayText}</div>
                <div class="message-time">${new Date().toLocaleTimeString('zh-CN', {
                    hour: '2-digit',
                    minute: '2-digit'
                })}</div>
            </div>
        `;

        messageArea.appendChild(messageElement);
        messageArea.scrollTop = messageArea.scrollHeight;
        console.log('✅ 消息元素添加完成');
    }

    // 更新按钮状态
    function updateButtonState() {
        const hasText = messageInput.value.trim().length > 0;
        sendButton.disabled = !hasText;

        // 字符计数
        const countElement = document.getElementById('character-count');
        if (countElement) {
            countElement.textContent = `${messageInput.value.length}/1800`;
        }

        console.log('📊 输入框状态:', {
            hasText: hasText,
            length: messageInput.value.length,
            buttonDisabled: !hasText
        });
    }

    // 清空聊天记录
    function clearChat() {
        if (confirm('确定要清空聊天记录吗？')) {
            const messages = messageArea.querySelectorAll('.message');
            messages.forEach((msg, index) => {
                // 保留欢迎消息
                if (index > 0) {
                    msg.remove();
                }
            });
        }
    }

    // 事件监听绑定 - 修复版本
    console.log('🔗 开始绑定事件监听器...');

    // 发送按钮点击事件
    sendButton.addEventListener('click', function(e) {
        console.log('🖱️ 发送按钮被点击');
        sendMessage();
    });

    // 输入框回车事件
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            console.log('⌨️ 回车键被按下');
            e.preventDefault();
            sendMessage();
        }
    });

    // 清空按钮事件
    if (clearButton) {
        clearButton.addEventListener('click', clearChat);
    }

    // 输入框输入事件
    messageInput.addEventListener('input', updateButtonState);

    // 初始按钮状态
    updateButtonState();

    console.log('🎉 聊天功能初始化完成！');

    // 安全检查函数是否存在再调用
    if (typeof getEventListeners !== 'undefined') {
        console.log('发送按钮事件监听器:', getEventListeners(sendButton));
        console.log('输入框事件监听器:', getEventListeners(messageInput));
    } else {
        console.log('✅ 事件监听器绑定完成 (getEventListeners仅在控制台可用)');
    }
}

// 改进的初始化逻辑
function safeInitialize() {
    try {
        initializeChat();
    } catch (error) {
        console.error('❌ 初始化失败:', error);
        // 3秒后重试
        setTimeout(safeInitialize, 3000);
    }
}

// 多重初始化保障
document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 DOMContentLoaded - 开始初始化聊天');
    setTimeout(safeInitialize, 100);
});

window.addEventListener('load', function() {
    console.log('🔄 window.load - 页面完全加载，再次检查初始化');
    setTimeout(safeInitialize, 200);
});

// 手动初始化函数（用于调试）
window.manualInitializeChat = function() {
    console.log('🔧 手动初始化聊天功能');
    safeInitialize();
};

// 测试函数
window.testChatFunctionality = function() {
    console.log('🧪 测试聊天功能');
    const input = document.getElementById('message-input');
    const button = document.getElementById('send-button');

    if (input && button) {
        input.value = '测试消息 ' + new Date().toLocaleTimeString();
        console.log('设置测试消息:', input.value);

        // 更新按钮状态
        input.dispatchEvent(new Event('input'));

        // 点击发送
        button.click();
    } else {
        console.error('测试失败：元素未找到');
    }
};

// 检查事件监听器的替代方法
window.checkEventListeners = function() {
    const sendButton = document.getElementById('send-button');
    const messageInput = document.getElementById('message-input');

    console.log('🔍 检查事件监听器:');
    console.log('发送按钮 onclick:', sendButton.onclick);
    console.log('发送按钮事件属性:', sendButton._events || '无内部事件数据');
    console.log('输入框 onkeydown:', messageInput.onkeydown);
    console.log('输入框 oninput:', messageInput.oninput);
};

console.log('✅ chat.js 加载完成');