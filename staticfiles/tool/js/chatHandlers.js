// static/js/chatHandlers.js

class ChatMessageHandler {
    /**
     * 主路由函数 - 前端判断消息类型
     * 这个函数将替代 chat.js 中的AI调用逻辑
     */
    static async handleUserMessage(message) {
        const trimmedMsg = message.trim();

        console.log('前端判断消息类型:', trimmedMsg);

        // 前端关键词判断：检查是否以#psql结尾
        if (trimmedMsg.endsWith('#psql')) {
            console.log('✅ 检测到#psql关键词，触发数据分析流程');
            return await this.handleDataAnalysisRequest(trimmedMsg);
        } else {
            console.log('💬 普通聊天消息，走AI聊天流程');
            return await this.handleNormalChatRequest(trimmedMsg);
        }
    }

    /**
     * 处理数据分析请求
     */
    static async handleDataAnalysisRequest(fullMessage) {
        try {
            // 显示加载状态
            this.showLoadingState('正在分析数据...');

            // 发送到后端的chat端点（使用现有路由）
            const response = await fetch('/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                body: JSON.stringify({
                    message: fullMessage, // 包含#psql的完整消息
                    message_type: 'data_analysis' // 明确标识消息类型
                })
            });

            if (!response.ok) {
                throw new Error(`请求失败: ${response.status}`);
            }

            const result = await response.json();
            return this.formatDataAnalysisResponse(result);

        } catch (error) {
            console.error('数据分析请求错误:', error);
            return this.formatErrorResponse(`数据分析失败: ${error.message}`);
        } finally {
            this.hideLoadingState();
        }
    }

    /**
     * 处理普通聊天请求 - 调用现有的AI聊天功能
     */
    static async handleNormalChatRequest(message) {
        try {
            // 使用现有的AI聊天机器人
            if (window.aiChatBot) {
                console.log('使用AI聊天机器人处理消息');
                const aiReply = await window.aiChatBot.sendMessage(message);
                return aiReply;
            } else {
                // 如果AI聊天机器人不可用，使用备用方案
                console.warn('AI聊天机器人未加载，使用备用方案');
                return await this.handleNormalChatBackup(message);
            }
        } catch (error) {
            console.error('AI聊天请求错误:', error);
            return `AI聊天失败: ${error.message}`;
        }
    }

    /**
     * 备用聊天处理方案
     */
    static async handleNormalChatBackup(message) {
        try {
            const response = await fetch('/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                body: JSON.stringify({
                    message: message,
                    message_type: 'normal_chat'
                })
            });

            const data = await response.json();
            return data.response || `收到您的消息: ${message}`;

        } catch (error) {
            console.error('备用聊天请求错误:', error);
            return '网络连接出现问题，请稍后重试';
        }
    }

    /**
     * 显示加载状态
     */
    static showLoadingState(message) {
        // 可以在这里添加全局加载指示器
        if (window.showGlobalLoading) {
            window.showGlobalLoading(message);
        } else {
            console.log('🔄', message);
        }
    }

    /**
     * 隐藏加载状态
     */
    static hideLoadingState() {
        if (window.hideGlobalLoading) {
            window.hideGlobalLoading();
        } else {
            console.log('✅ 加载完成');
        }
    }

    /**
     * 获取CSRF Token
     */
    static getCSRFToken() {
        try {
            // 多种方式尝试获取CSRF token
            const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
            if (tokenElement && tokenElement.value) {
                return tokenElement.value;
            }

            // 备用方案：从meta标签获取
            const metaToken = document.querySelector('meta[name="csrf-token"]');
            if (metaToken) {
                return metaToken.getAttribute('content');
            }

            console.warn('CSRF token未找到，请求可能失败');
            return '';
        } catch (error) {
            console.error('获取CSRF token时出错:', error);
            return '';
        }
    }

    /**
     * 格式化数据分析响应
     */
    static formatDataAnalysisResponse(result) {
            if (result.status === 'data_analysis') {
                // 创建更好的数据分析结果展示
                let dataHtml = '';
                let analysisHtml = '';

                if (result.data && result.data.length > 0) {
                    dataHtml = `
            <div class="data-preview mt-3">
                <details open>
                    <summary><strong>📋 查询结果 (${result.data.length} 条记录)</strong></summary>
                    <div class="data-table mt-2">
                        ${this.formatDataAsTable(result.data)}
                    </div>
                </details>
            </div>
            `;
                } else {
                    dataHtml = '<div class="alert alert-warning mt-3">⚠️ 未查询到相关数据</div>';
                }

                if (result.analysis) {
                    analysisHtml = `
            <div class="analysis-summary mt-3">
                <h5>💡 分析结论</h5>
                <div class="alert alert-info">${result.analysis}</div>
            </div>
            `;
                }
                return `
        <div class="data-analysis-result">
            <div class="analysis-header d-flex justify-content-between align-items-center">
                <h4>📊 数据分析结果</h4>
                <span class="badge bg-success">数据库查询</span>
            </div>
            
            ${result.sql_query ? `
            <div class="sql-preview mt-3">
                <details>
                    <summary><strong>🔍 执行的SQL查询</strong></summary>
                    <pre class="bg-dark text-light p-3 rounded mt-2"><code class="sql">${result.sql_query}</code></pre>
                </details>
            </div>
            ` : ''}
            
            ${dataHtml}
            ${analysisHtml}
            
            <div class="mt-3 text-muted small">
                <i>查询时间: ${new Date(result.timestamp).toLocaleString()}</i>
            </div>
        </div>
        `;
    } else if (result.status === 'error') {
        return this.formatErrorResponse(result.error);
    } else {
        return '未知响应格式';
    }
}

    /**
     * 格式化数据为表格
     */
    static formatDataAsTable(data) {
        if (!data || data.length === 0) return '<p>暂无数据</p>';
        
        const headers = Object.keys(data[0]);
        const rows = data.slice(0, 10); // 只显示前10条
        
        return `
            <table class="table table-sm table-striped">
                <thead>
                    <tr>${headers.map(h => `<th>${this.escapeHtml(h)}</th>`).join('')}</tr>
                </thead>
                <tbody>
                    ${rows.map(row => `
                        <tr>${headers.map(h => 
                            `<td>${this.escapeHtml(String(row[h] || ''))}</td>`
                        ).join('')}</tr>
                    `).join('')}
                </tbody>
            </table>
            ${data.length > 10 ? `<p class="small">显示前10条，共${data.length}条记录</p>` : ''}
        `;
    }

    /**
     * HTML转义
     */
    static escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 格式化错误响应
     */
    static formatErrorResponse(error) {
        return `
            <div class="alert alert-danger">
                <strong>❌ 处理失败</strong>
                <p>${this.escapeHtml(error)}</p>
                <small>请检查查询语法或稍后重试</small>
            </div>
        `;
    }
}

// 全局注册，方便chat.js调用
window.ChatMessageHandler = ChatMessageHandler;