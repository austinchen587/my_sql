// tool/static/tool/js/chatHandlers.js
class ChatMessageHandler {
    static async handleUserMessage(message) {
        console.log('🔧 ChatMessageHandler.handleUserMessage 开始处理:', message);

        const trimmedMsg = message.trim();

        try {
            this.showLoadingState('正在处理...');
            console.log('⏳ 显示加载状态');

            // 准备请求数据
            const requestData = {
                message: trimmedMsg,
                message_type: trimmedMsg.includes('#psql') ? 'data_analysis' : 'normal_chat',
                session_id: 'default'
            };

            console.log('📦 请求数据:', requestData);

            const response = await fetch('/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                body: JSON.stringify(requestData)
            });

            console.log('📡 响应状态:', response.status, response.statusText);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('❌ 请求失败:', errorText);
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }

            const result = await response.json();
            console.log('✅ 响应数据:', result);

            if (result.status === 'success') {
                console.log('🎯 消息处理成功');
                return result.message;
            } else {
                console.error('❌ 业务逻辑失败:', result.message);
                throw new Error(result.message || '处理失败');
            }

        } catch (error) {
            console.error('💥 处理消息时发生错误:', error);
            return this.formatErrorResponse(error.message);
        } finally {
            this.hideLoadingState();
            console.log('🏁 处理完成');
        }
    }

    static formatErrorResponse(error) {
        return `<div class="alert alert-danger">错误: ${error}</div>`;
    }

    static showLoadingState(message) {
        console.log('⏳ 显示加载状态:', message);
        const sendButton = document.getElementById('send-button');
        if (sendButton) {
            sendButton.disabled = true;
            sendButton.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>发送中...';
        }
    }

    static hideLoadingState() {
        console.log('✅ 隐藏加载状态');
        const sendButton = document.getElementById('send-button');
        if (sendButton) {
            sendButton.disabled = false;
            sendButton.innerHTML = '<i class="bi bi-send-fill me-1"></i>发送';
        }
    }

    static getCSRFToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        const token = csrfToken ? csrfToken.value : '';
        console.log('🔐 CSRF Token:', token ? `找到(${token.substring(0, 10)}...)` : '未找到');
        return token;
    }
}

// 确保全局可用
if (typeof window !== 'undefined') {
    window.ChatMessageHandler = ChatMessageHandler;
    console.log('✅ ChatMessageHandler 已注册到全局');
}