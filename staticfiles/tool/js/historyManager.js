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
        const refreshBtn = document.getElementById('refresh-sessions');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadSessions();
            });
        }

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

    // 修复：会话列表按时间升序排列（最新的在前面）
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

        // 按最后更新时间升序排列（最新的在前面）
        const sortedSessions = sessions.sort((a, b) => {
            const timeA = new Date(a.last_updated || 0).getTime();
            const timeB = new Date(b.last_updated || 0).getTime();
            return timeB - timeA; // 降序排列（时间戳大的在前面）
        });

        sessionList.innerHTML = sortedSessions.map(session => this.createSessionItem(session)).join('');
    }

    createSessionItem(session) {
        const lastUpdated = session.last_updated ? new Date(session.last_updated) : new Date();
        const timeAgo = this.formatTimeAgo(lastUpdated);
        const isActive = session.session_id === this.currentSessionId;

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
            this.showNotification(`加载失败: ${error.message}`, 'error');
        } finally {
            this.isLoading = false;
        }
    }

    // 修复：按时间升序排列（最新的消息在最上面）
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

        // 添加历史消息 - 按时间升序排列（最新的在最上面）
        if (messages && messages.length > 0) {
            // 过滤重复消息
            const uniqueMessages = this.removeDuplicateMessages(messages);

            // 按时间戳升序排列（最新的在前面）
            const sortedMessages = this.sortMessagesByTime(uniqueMessages, 'asc');

            console.log(`🔍 过滤后消息数量: ${sortedMessages.length}, 按时间升序排列`);

            // 将排序后的消息添加到页面
            sortedMessages.forEach(message => {
                this.addHistoryMessage(message, false, true); // 第三个参数表示是历史消息
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

    // 修复：排序逻辑正确理解
    sortMessagesByTime(messages, order = 'asc') {
        return messages.sort((a, b) => {
            const timeA = new Date(a.timestamp || 0).getTime();
            const timeB = new Date(b.timestamp || 0).getTime();

            if (order === 'asc') {
                // 升序排列：时间戳小的在前面（最新的消息时间戳更大）
                return timeB - timeA; // 时间戳大的排前面
            } else {
                // 降序排列：时间戳大的在前面
                return timeA - timeB;
            }
        });
    }

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

    // 修复：添加历史消息时保持正确的顺序
    addHistoryMessage(message, isNotice = false, isHistoryMessage = false) {
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

            let displayContent = message.content;
            let isHtmlContent = false;

            if (typeof displayContent === 'string') {
                if (displayContent.includes('<div') ||
                    displayContent.includes('<table') ||
                    displayContent.includes('<h4') ||
                    displayContent.includes('<pre') ||
                    displayContent.includes('class="')) {
                    isHtmlContent = true;
                    displayContent = displayContent.trim();
                    if (!displayContent.includes('class="message-html"')) {
                        displayContent = `<div class="message-html">${displayContent}</div>`;
                    }
                } else {
                    displayContent = this.escapeHtml(displayContent);
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

        // 对于历史消息，添加到欢迎消息之后
        if (isHistoryMessage) {
            const welcomeMessage = messageArea.querySelector('.message.received');
            if (welcomeMessage) {
                messageArea.appendChild(messageElement);
            } else {
                messageArea.appendChild(messageElement);
            }
        } else {
            // 新消息添加到最下面
            messageArea.appendChild(messageElement);
        }
    }

    showNotification(message, type = 'info') {
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

    // 修复：对话分组按时间升序排列
    groupMessagesBySession(messages) {
        console.log('📊 按会话分组消息，总数:', messages.length);
        if (!messages || messages.length === 0) {
            return [];
        }

        // 首先按时间升序排列所有消息（最新的在前面）
        const sortedMessages = this.sortMessagesByTime(messages, 'asc');

        // 按用户-助手对话对分组
        const sessions = [];
        let currentSession = [];

        // 从最新的消息开始处理
        for (let i = 0; i < sortedMessages.length; i++) {
            const message = sortedMessages[i];
            const currentRole = message.role;

            // 如果是用户消息，开始新的会话
            if (currentRole === 'user') {
                // 如果当前会话不为空，保存之前的会话
                if (currentSession.length > 0) {
                    sessions.push([...currentSession]); // 使用push保持顺序
                    currentSession = [];
                }
            }

            // 添加到当前会话
            currentSession.push(message);
        }

        // 添加最后一个会话
        if (currentSession.length > 0) {
            sessions.push(currentSession);
        }

        console.log('🔢 分组结果:', sessions.length, '个会话，按时间升序排列');
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

        this.loadAndRenderGroupedSessions(sessions);
    }

    async loadAndRenderGroupedSessions(sessions) {
        const sessionList = document.getElementById('session-list');

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

                    sessionList.innerHTML = groupedSessions.map((session, index) =>
                        this.createSessionGroupItem(session, index, groupedSessions.length)
                    ).join('');

                    return;
                }
            }
        } catch (error) {
            console.error('❌ 加载分组会话失败:', error);
        }

        // 备用方案
        const sortedSessions = sessions.sort((a, b) => {
            const timeA = new Date(a.last_updated || 0).getTime();
            const timeB = new Date(b.last_updated || 0).getTime();
            return timeB - timeA; // 最新的在前面
        });

        sessionList.innerHTML = sortedSessions.map(session => this.createSessionItem(session)).join('');
    }

    // 修复：会话组项显示正确的顺序
    createSessionGroupItem(sessionMessages, index, totalCount) {
        if (!sessionMessages || sessionMessages.length === 0) return '';

        // 会话内的消息按时间升序排列（最新的在前面）
        const sortedSessionMessages = this.sortMessagesByTime(sessionMessages, 'asc');

        const firstMessage = sortedSessionMessages[0]; // 最新的消息
        const lastMessage = sortedSessionMessages[sortedSessionMessages.length - 1]; // 最旧的消息
        const userMessage = sortedSessionMessages.find(msg => msg.role === 'user');
        const assistantMessage = sortedSessionMessages.find(msg => msg.role === 'assistant');

        const userContent = userMessage ? this.extractPreviewText(userMessage.content) : '用户消息';
        const assistantContent = assistantMessage ? this.extractPreviewText(assistantMessage.content) : 'AI回复';

        const timestamp = firstMessage.timestamp ? new Date(firstMessage.timestamp) : new Date();
        const timeAgo = this.formatTimeAgo(timestamp);

        // 会话序号：最新的会话序号为1
        const sessionNumber = index + 1;

        return `
            <div class="list-group-item session-group-item" 
                 data-session-index="${index}" 
                 style="cursor: pointer; border-left: 4px solid #007bff;">
                <div class="d-flex w-100 justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h6 class="mb-1">对话 ${sessionNumber}</h6>
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
                        更新: ${timestamp.toLocaleString('zh-CN', { 
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
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = htmlContent;
        let text = tempDiv.textContent || tempDiv.innerText || '';
        text = text.replace(/\s+/g, ' ').trim();
        return text;
    }

    bindEvents() {
        const refreshBtn = document.getElementById('refresh-sessions');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadSessions();
            });
        }

        document.addEventListener('click', (e) => {
            const sessionItem = e.target.closest('.session-item');
            if (sessionItem) {
                const sessionId = sessionItem.dataset.sessionId;
                this.loadChatHistory(sessionId);
            }

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