// tool/static/tool/js/historyManager.js
class HistoryManager {
    constructor() {
        this.currentSessionId = 'default';
        this.isLoading = false;
    }

    init() {
        console.log('🔧 初始化历史管理器');
        this.bindEvents();
        this.loadSessions();
    }

    bindEvents() {
        // 刷新会话列表 - 修复语法错误
        const refreshBtn = document.getElementById('refresh-sessions');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadSessions();
            });
        }

        // 点击会话项加载历史
        document.addEventListener('click', (e) => {
            if (e.target.closest('.session-item')) {
                const sessionItem = e.target.closest('.session-item');
                const sessionId = sessionItem.dataset.sessionId;
                this.loadChatHistory(sessionId);
            }
        });
    }

    async loadSessions() {
        console.log('📋 加载会话列表');

        const sessionList = document.getElementById('session-list');
        if (!sessionList) {
            console.error('❌ 未找到会话列表元素');
            return;
        }

        try {
            this.isLoading = true;
            sessionList.innerHTML = `
                <div class="text-center p-3 text-muted">
                    <div class="spinner-border spinner-border-sm" role="status">
                        <span class="visually-hidden">加载中...</span>
                    </div>
                    <span class="ms-2">加载中...</span>
                </div>
            `;

            // 修改这里：使用正确的路径 /list-sessions/
            const response = await fetch('/list-sessions/');
            console.log('📡 会话列表响应状态:', response.status);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            console.log('📦 会话数据:', data);

            if (data.status === 'success') {
                this.renderSessions(data.sessions);
            } else {
                throw new Error(data.message || '加载失败');
            }

        } catch (error) {
            console.error('❌ 加载会话列表失败:', error);
            sessionList.innerHTML = `
                <div class="text-center p-3 text-danger">
                    <i class="bi bi-exclamation-triangle"></i>
                    <div>加载失败</div>
                    <small>${error.message}</small>
                </div>
            `;
        } finally {
            this.isLoading = false;
        }
    }

    renderSessions(sessions) {
        const sessionList = document.getElementById('session-list');
        if (!sessionList) return;

        if (!sessions || sessions.length === 0) {
            sessionList.innerHTML = `
                <div class="text-center p-3 text-muted">
                    <i class="bi bi-inbox"></i>
                    <div>暂无历史对话</div>
                    <small>开始新的对话后会自动保存</small>
                </div>
            `;
            return;
        }

        sessionList.innerHTML = sessions.map(session => this.createSessionItem(session)).join('');
    }

    createSessionItem(session) {
        const lastUpdated = session.last_updated ? new Date(session.last_updated) : new Date();
        const timeAgo = this.formatTimeAgo(lastUpdated);
        const isActive = session.session_id === this.currentSessionId;

        // 格式化显示名称
        const displayName = session.session_id === 'default' ? '默认会话' : `会话 ${session.session_id}`;

        return `
            <div class="list-group-item session-item ${isActive ? 'active' : ''}" 
                 data-session-id="${session.session_id}" style="cursor: pointer;">
                <div class="d-flex w-100 justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h6 class="mb-1">${displayName}</h6>
                        <small class="text-muted">
                            ${session.message_count || 0} 条消息
                        </small>
                    </div>
                    <small class="text-muted">${timeAgo}</small>
                </div>
                <div class="mt-1">
                    <small class="text-muted">
                        更新: ${lastUpdated.toLocaleString('zh-CN', { 
                            month: 'short', 
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                        })}
                    </small>
                </div>
            </div>
        `;
    }

    async loadChatHistory(sessionId) {
        console.log(`📂 加载会话历史: ${sessionId}`);

        if (this.isLoading) {
            console.log('⏳ 正在加载中，请稍候...');
            return;
        }

        try {
            this.isLoading = true;
            console.log('📤 发送加载请求...');

            // 修改这里：使用正确的路径 /load_chat/
            const response = await fetch('/load_chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                body: JSON.stringify({ session_id: sessionId })
            });

            console.log('📡 历史记录响应状态:', response.status);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('📦 历史消息数据:', data);

            if (data.status === 'success') {
                this.currentSessionId = sessionId;
                this.displayChatHistory(data.messages);
                this.highlightActiveSession(sessionId);
                console.log('✅ 历史记录加载成功');
            } else {
                throw new Error(data.message || '加载失败');
            }

        } catch (error) {
            console.error('❌ 加载聊天历史失败:', error);
            // 使用更友好的错误提示
            this.showNotification(`加载失败: ${error.message}`, 'error');
        } finally {
            this.isLoading = false;
        }
    }

    displayChatHistory(messages) {
        const messageArea = document.getElementById('message-area');
        if (!messageArea) {
            console.error('❌ 未找到消息区域元素');
            return;
        }

        console.log(`📝 显示历史消息，共 ${messages ? messages.length : 0} 条`);

        // 清空当前消息（保留欢迎消息）
        const welcomeMessage = messageArea.querySelector('.message.received');
        messageArea.innerHTML = '';
        if (welcomeMessage) {
            messageArea.appendChild(welcomeMessage);
        }

        // 添加历史消息
        if (messages && messages.length > 0) {
            // 过滤重复消息（基于内容和时间戳）
            const uniqueMessages = this.removeDuplicateMessages(messages);
            console.log(`🔍 过滤后消息数量: ${uniqueMessages.length}`);

            uniqueMessages.forEach(message => {
                this.addHistoryMessage(message);
            });
        } else {
            this.addHistoryMessage({
                role: 'assistant',
                content: '此会话暂无聊天记录',
                timestamp: new Date().toISOString()
            }, true);
        }

        messageArea.scrollTop = messageArea.scrollHeight;
    }

    // 移除重复消息的方法
    removeDuplicateMessages(messages) {
        const seen = new Set();
        return messages.filter(message => {
            const key = `${message.content}-${message.timestamp}`;
            if (seen.has(key)) {
                return false;
            }
            seen.add(key);
            return true;
        });
    }

    addHistoryMessage(message, isNotice = false) {
        const messageArea = document.getElementById('message-area');
        if (!messageArea) return;
        const messageElement = document.createElement('div');
        const type = message.role === 'user' ? 'sent' : 'received';
        const timestamp = message.timestamp ? new Date(message.timestamp) : new Date();
        if (isNotice) {
            messageElement.className = 'message notice';
            messageElement.innerHTML = `
            <div class="message-content text-center">
                <div class="message-text text-muted">
                    <i class="bi bi-info-circle"></i> ${message.content}
                </div>
            </div>
        `;
        } else {
            messageElement.className = `message ${type}`;

            // 处理消息内容
            let displayContent = message.content;
            let isHtmlContent = false;

            // 检查是否为HTML内容
            if (typeof displayContent === 'string') {
                // 检查是否包含HTML标签或特殊格式
                if (displayContent.includes('<div') ||
                    displayContent.includes('<table') ||
                    displayContent.includes('<h4') ||
                    displayContent.includes('<pre') ||
                    displayContent.includes('class="')) {
                    isHtmlContent = true;

                    // 清除多余的换行和空格，确保HTML格式正确
                    displayContent = displayContent.trim();

                    // 包装HTML内容，确保样式统一
                    if (!displayContent.includes('class="message-html"')) {
                        displayContent = `<div class="message-html">${displayContent}</div>`;
                    }
                } else {
                    // 普通文本内容，进行HTML转义
                    displayContent = this.escapeHtml(displayContent);
                    // 保留换行
                    displayContent = displayContent.replace(/\n/g, '<br>');
                }
            }
            messageElement.innerHTML = `
            <div class="message-avatar bg-${type === 'sent' ? 'primary' : 'success'} rounded-circle">
                <span>${type === 'sent' ? '👤' : '🤖'}</span>
            </div>
            <div class="message-content ${isHtmlContent ? 'html-content' : ''}">
                <div class="message-sender">${type === 'sent' ? '您' : 'AI助手'}</div>
                <div class="message-text">${displayContent}</div>
                <div class="message-time">${timestamp.toLocaleTimeString('zh-CN', {
                    hour: '2-digit',
                    minute: '2-digit'
                })}</div>
            </div>
        `;
        }
        messageArea.appendChild(messageElement);
    }

    highlightActiveSession(sessionId) {
        const sessionItems = document.querySelectorAll('.session-item');
        sessionItems.forEach(item => {
            item.classList.remove('active');
            if (item.dataset.sessionId === sessionId) {
                item.classList.add('active');
            }
        });
    }

    // 显示通知的辅助方法
    showNotification(message, type = 'info') {
        // 创建简单的通知
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : 'info'} alert-dismissible fade show`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '9999';
        notification.style.minWidth = '300px';

        document.body.appendChild(notification);

        // 3秒后自动消失
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }

    formatTimeAgo(date) {
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return '刚刚';
        if (diffMins < 60) return `${diffMins}分钟前`;
        if (diffHours < 24) return `${diffHours}小时前`;
        if (diffDays < 7) return `${diffDays}天前`;
        return date.toLocaleDateString('zh-CN');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    getCSRFToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value : '';
    }


    groupMessagesBySession(messages) {
        console.log('📊 按会话分组消息，总数:', messages.length);

        if (!messages || messages.length === 0) {
            return [];
        }

        // 按用户-助手对话对分组
        const sessions = [];
        let currentSession = [];
        let lastRole = null;

        messages.forEach((message, index) => {
            const currentRole = message.role;

            // 如果是用户消息，开始新的会话
            if (currentRole === 'user') {
                // 如果当前会话不为空，保存之前的会话
                if (currentSession.length > 0) {
                    sessions.push([...currentSession]);
                    currentSession = [];
                }
            }

            // 添加到当前会话
            currentSession.push(message);
            lastRole = currentRole;
        });

        // 添加最后一个会话
        if (currentSession.length > 0) {
            sessions.push(currentSession);
        }

        console.log('🔢 分组结果:', sessions.length, '个会话');
        return sessions;
    }
    renderSessions(sessions) {
        const sessionList = document.getElementById('session-list');
        if (!sessionList) return;
        if (!sessions || sessions.length === 0) {
            sessionList.innerHTML = `
            <div class="text-center p-3 text-muted">
                <i class="bi bi-inbox"></i>
                <div>暂无历史对话</div>
                <small>开始新的对话后会自动保存</small>
            </div>
        `;
            return;
        }
        // 获取消息数据并分组
        this.loadAndRenderGroupedSessions(sessions);
    }
    async loadAndRenderGroupedSessions(sessions) {
        const sessionList = document.getElementById('session-list');

        try {
            // 加载默认会话的详细信息来获取消息
            const response = await fetch('/load_chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                body: JSON.stringify({ session_id: 'default' })
            });
            if (response.ok) {
                const data = await response.json();
                if (data.status === 'success') {
                    const messages = data.messages || [];
                    const groupedSessions = this.groupMessagesBySession(messages);

                    sessionList.innerHTML = groupedSessions.map((session, index) =>
                        this.createSessionGroupItem(session, index)
                    ).join('');

                    return;
                }
            }
        } catch (error) {
            console.error('❌ 加载分组会话失败:', error);
        }

        // 备用：显示传统的会话列表
        sessionList.innerHTML = sessions.map(session => this.createSessionItem(session)).join('');
    }
    createSessionGroupItem(sessionMessages, index) {
        if (!sessionMessages || sessionMessages.length === 0) return '';

        const firstMessage = sessionMessages[0];
        const lastMessage = sessionMessages[sessionMessages.length - 1];
        const userMessage = sessionMessages.find(msg => msg.role === 'user');
        const assistantMessage = sessionMessages.find(msg => msg.role === 'assistant');

        const userContent = userMessage ? this.extractPreviewText(userMessage.content) : '用户消息';
        const assistantContent = assistantMessage ? this.extractPreviewText(assistantMessage.content) : 'AI回复';

        const timestamp = firstMessage.timestamp ? new Date(firstMessage.timestamp) : new Date();
        const timeAgo = this.formatTimeAgo(timestamp);

        return `
        <div class="list-group-item session-group-item" 
             data-session-index="${index}" 
             style="cursor: pointer; border-left: 4px solid #007bff;">
            <div class="d-flex w-100 justify-content-between align-items-start">
                <div class="flex-grow-1">
                    <h6 class="mb-1">对话 ${index + 1}</h6>
                    <div class="session-preview">
                        <small class="text-primary fw-bold">您:</small>
                        <small class="text-muted">${userContent.substring(0, 30)}...</small>
                        <br>
                        <small class="text-success fw-bold">AI:</small>
                        <small class="text-muted">${assistantContent.substring(0, 30)}...</small>
                    </div>
                </div>
                <small class="text-muted">${timeAgo}</small>
            </div>
            <div class="mt-1">
                <small class="text-muted">
                    ${timestamp.toLocaleString('zh-CN', { 
                        month: 'short', 
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                    })} • ${sessionMessages.length} 条消息
                </small>
            </div>
        </div>
    `;
    }
    extractPreviewText(htmlContent) {
            // 提取纯文本预览
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = htmlContent;
            let text = tempDiv.textContent || tempDiv.innerText || '';

            // 移除多余空格和换行
            text = text.replace(/\s+/g, ' ').trim();

            return text;
        }
        // 修改点击事件处理
    bindEvents() {
        const refreshBtn = document.getElementById('refresh-sessions');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadSessions();
            });
        }
        // 点击会话项加载历史
        document.addEventListener('click', (e) => {
            const sessionItem = e.target.closest('.session-item');
            if (sessionItem) {
                const sessionId = sessionItem.dataset.sessionId;
                this.loadChatHistory(sessionId);
            }

            // 新增：处理分组会话项点击
            const sessionGroupItem = e.target.closest('.session-group-item');
            if (sessionGroupItem) {
                const sessionIndex = sessionGroupItem.dataset.sessionIndex;
                this.loadSessionGroup(sessionIndex);
            }
        });
    }
    async loadSessionGroup(sessionIndex) {
        console.log(`📂 加载会话组: ${sessionIndex}`);

        try {
            const response = await fetch('/load_chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                body: JSON.stringify({ session_id: 'default' })
            });
            if (response.ok) {
                const data = await response.json();
                if (data.status === 'success') {
                    const messages = data.messages || [];
                    const groupedSessions = this.groupMessagesBySession(messages);

                    if (sessionIndex < groupedSessions.length) {
                        const sessionMessages = groupedSessions[sessionIndex];
                        this.displayChatHistory(sessionMessages);
                        this.highlightActiveSessionGroup(sessionIndex);
                    }
                }
            }
        } catch (error) {
            console.error('❌ 加载会话组失败:', error);
            this.showNotification('加载对话失败', 'error');
        }
    }
    highlightActiveSessionGroup(sessionIndex) {
        const sessionItems = document.querySelectorAll('.session-group-item');
        sessionItems.forEach(item => {
            item.classList.remove('active');
            if (item.dataset.sessionIndex === sessionIndex.toString()) {
                item.classList.add('active');
                item.style.borderLeftColor = '#28a745';
            } else {
                item.style.borderLeftColor = '#007bff';
            }
        });
    }








}

// 全局注册
if (typeof window !== 'undefined') {
    window.HistoryManager = new HistoryManager();
    console.log('✅ HistoryManager 已注册到全局');
}