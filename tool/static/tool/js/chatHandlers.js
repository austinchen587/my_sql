// static/js/chatHandlers.js

class ChatMessageHandler {
    /**
     * 主路由函数 - 前端判断消息类型
     */
    static async handleUserMessage(message) {
        const trimmedMsg = message.trim();

        console.log('前端判断消息类型:', trimmedMsg);

        if (trimmedMsg.includes('#psql')) {
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
            this.showLoadingState('正在分析数据...');

            const response = await fetch('/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                body: JSON.stringify({
                    message: fullMessage,
                    message_type: 'data_analysis'
                })
            });

            if (!response.ok) {
                throw new Error(`请求失败: ${response.status}`);
            }

            const result = await response.json();
            console.log('后端响应详情:', result);

            return this.processBackendResponse(result);

        } catch (error) {
            console.error('数据分析请求错误:', error);
            return this.formatErrorResponse(`数据分析失败: ${error.message}`);
        } finally {
            this.hideLoadingState();
        }
    }

    /**
     * 处理后端响应 - 增强版，支持多种响应类型
     */
    static processBackendResponse(result) {
        console.log('处理后端响应:', result);

        // 保存处理日志供调试
        if (result.process_log) {
            console.log('📋 处理过程日志:', result.process_log);
        }

        if (result.status === 'success') {
            // 根据 response_type 处理不同类型的成功响应
            switch (result.response_type) {
                case 'intelligent_analysis':
                    console.log('🎯 处理智能分析响应');
                    return this.handleIntelligentAnalysis(result);

                case 'data_analysis':
                    console.log('📊 处理标准数据分析响应');
                    return this.handleDataAnalysis(result);

                case 'database_intro':
                    console.log('🏛️ 处理数据库介绍响应');
                    return this.handleDatabaseIntroduction(result);

                case 'normal_chat':
                    console.log('💬 处理普通聊天响应');
                    return result.message;

                default:
                    console.warn('⚠️ 未知响应类型，使用默认处理:', result.response_type);
                    return this.handleDefaultResponse(result);
            }
        } else if (result.status === 'error') {
            return this.formatErrorResponse(result.message);
        } else {
            console.warn('❓ 未知响应状态:', result.status);
            return '未知响应格式，请联系管理员';
        }
    }

    /**
     * 处理智能分析响应
     */
    static handleIntelligentAnalysis(result) {
        console.log('处理智能分析，数据量:', result.data_count);

        // 直接使用后端返回的HTML内容
        if (result.message && this.isHtmlContent(result.message)) {
            return result.message;
        }

        // 如果消息不是HTML，进行包装
        return `
        <div class="intelligent-analysis-result">
            <div class="alert alert-success">
                <h4>🧠 智能分析结果</h4>
                <p><strong>处理完成:</strong> 基于 ${result.data_count || 0} 条数据</p>
            </div>
            <div class="analysis-content">
                ${this.escapeHtml(result.message || '暂无分析内容')}
            </div>
            ${this.renderProcessLog(result.process_log)}
        </div>
        `;
    }

    /**
     * 处理标准数据分析响应
     */
    static handleDataAnalysis(result) {
        // 如果后端已经提供了格式化内容，直接使用
        if (result.message && this.isHtmlContent(result.message)) {
            return result.message;
        }

        // 否则使用前端格式化
        return this.formatDataAnalysisResponse(result);
    }

    /**
     * 处理数据库介绍响应
     */
    static handleDatabaseIntroduction(result) {
        if (result.message && this.isHtmlContent(result.message)) {
            return result.message;
        }

        return `
        <div class="database-intro-container">
            <div class="alert alert-info">
                <h4>🏛️ 数据库介绍</h4>
                <div class="intro-content">
                    ${this.escapeHtml(result.message || '数据库连接成功')}
                </div>
            </div>
        </div>
        `;
    }

    /**
     * 处理默认响应
     */
    static handleDefaultResponse(result) {
        // 尝试提取可能的有效内容
        if (result.message) {
            if (this.isHtmlContent(result.message)) {
                return result.message;
            }
            return this.escapeHtml(result.message);
        }

        if (result.response) {
            if (this.isHtmlContent(result.response)) {
                return result.response;
            }
            return this.escapeHtml(result.response);
        }

        return '收到响应，但内容为空';
    }

    /**
     * 渲染处理过程日志（调试用）
     */
    static renderProcessLog(processLog) {
            if (!processLog || !Array.isArray(processLog)) {
                return '';
            }

            return `
        <details class="mt-3">
            <summary class="btn btn-sm btn-outline-secondary">🔍 查看处理过程</summary>
            <div class="mt-2 p-3 bg-light border rounded small">
                <h6>处理过程日志:</h6>
                <div style="max-height: 200px; overflow-y: auto;">
                    ${processLog.map(log => `
                        <div class="border-bottom pb-1 mb-1">
                            <strong>${log.timestamp}</strong> 
                            <span class="badge bg-primary">${log.stage}</span>
                            <div>${this.escapeHtml(log.message)}</div>
                            ${log.data ? `<pre class="mt-1 mb-0 small">${JSON.stringify(log.data, null, 2)}</pre>` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        </details>
        `;
    }

    /**
     * 检查是否为HTML内容
     */
    static isHtmlContent(text) {
        if (typeof text !== 'string') return false;
        const trimmed = text.trim();
        return trimmed.startsWith('<') && trimmed.includes('>') && trimmed.endsWith('>');
    }

    /**
     * 格式化数据分析响应（备选方案）
     */
    static formatDataAnalysisResponse(result) {
        let dataHtml = '';
        let analysisHtml = '';
        
        if (result.data && result.data.length > 0) {
            dataHtml = this.formatDataAsFullTable(result.data);
        } else {
            dataHtml = '<div class="alert alert-warning">⚠️ 未查询到相关数据</div>';
        }
        
        if (result.analysis) {
            if (this.isHtmlContent(result.analysis)) {
                analysisHtml = result.analysis;
            } else {
                analysisHtml = `
                <div class="analysis-summary mt-4">
                    <h4>💡 分析结论</h4>
                    <div class="alert alert-info p-3">${this.escapeHtml(result.analysis)}</div>
                </div>
                `;
            }
        }

        return `
        <div class="data-analysis-result">
            <div class="analysis-header d-flex justify-content-between align-items-center mb-3">
                <h3 class="mb-0">📊 数据分析结果</h3>
                <span class="badge bg-primary">数据表: ${result.table_used || '未知'}</span>
            </div>
            
            ${result.sql_query ? `
            <div class="sql-preview mb-4">
                <details class="border rounded">
                    <summary class="p-3 bg-light fw-bold">🔍 查看执行的SQL查询</summary>
                    <pre class="p-3 mb-0"><code class="sql">${this.escapeHtml(result.sql_query)}</code></pre>
                </details>
            </div>
            ` : ''}
            
            <div class="data-section mb-4">
                <h4>📋 查询结果 <span class="badge bg-success">${result.data ? result.data.length : 0} 条记录</span></h4>
                ${dataHtml}
            </div>
            
            ${analysisHtml}
            
            <div class="mt-4 text-muted small border-top pt-2">
                <i>查询时间: ${new Date().toLocaleString('zh-CN')}</i>
            </div>
            
            ${this.renderProcessLog(result.process_log)}
        </div>
        `;
    }

    /**
     * 格式化完整数据表格
     */
    static formatDataAsFullTable(data) {
        if (!data || data.length === 0) return '<p class="text-muted">暂无数据</p>';
        
        const headers = Object.keys(data[0]);
        const totalRecords = data.length;
        
        // 限制显示条数，避免界面卡顿
        const displayData = data.slice(0, 100);
        const showAll = totalRecords <= 100;
        
        return `
            <div class="table-responsive" style="max-height: 400px; overflow-y: auto;">
                <table class="table table-hover table-striped">
                    <thead class="table-dark sticky-top">
                        <tr>${headers.map(h => `<th>${this.formatHeaderName(h)}</th>`).join('')}</tr>
                    </thead>
                    <tbody>
                        ${displayData.map((row, index) => `
                            <tr>
                                ${headers.map(h => `
                                    <td title="${this.escapeHtml(String(row[h] || ''))}">
                                        ${this.formatCellValue(row[h])}
                                    </td>
                                `).join('')}
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            <div class="mt-2 text-end">
                <small class="text-muted">
                    显示 ${displayData.length} 条记录
                    ${!showAll ? `，共 ${totalRecords} 条记录（只显示前100条）` : ''}
                </small>
            </div>
        `;
    }

    /**
     * 格式化表头名称
     */
    static formatHeaderName(header) {
        const headerMap = {
            'url': '🔗 链接',
            'title': '📝 标题',
            'jurisdiction': '📍 管辖区域',
            'info_type': '📊 信息类型',
            'publish_time': '📅 发布时间',
            'intention_budget_amount': '💰 预算金额',
            'intention_procurement_unit': '🏢 采购单位',
            'content': '📄 内容',
            'bid_type': '📋 招标类型',
            'notice_content': '📄 公告内容'
        };
        return headerMap[header] || header;
    }

    /**
     * 格式化单元格值
     */
    static formatCellValue(value) {
        if (value === null || value === undefined) {
            return '<span class="text-muted">-</span>';
        }
        
        if (typeof value === 'number') {
            if (value > 1000000) {
                return `¥${(value/1000000).toFixed(2)}万`;
            } else if (value > 10000) {
                return `¥${(value/10000).toFixed(2)}万`;
            }
            return `¥${value.toLocaleString()}`;
        }
        
        if (typeof value === 'string') {
            // 如果是URL
            if (value.startsWith('http')) {
                return `<a href="${this.escapeHtml(value)}" target="_blank" class="text-primary">🔗 链接</a>`;
            }
            // 如果是长文本，截断显示
            if (value.length > 50) {
                return `<span title="${this.escapeHtml(value)}">${this.escapeHtml(value.substring(0, 50))}...</span>`;
            }
        }
        
        // 处理JSON对象
        if (typeof value === 'object') {
            try {
                const jsonStr = JSON.stringify(value, null, 2);
                if (jsonStr.length > 100) {
                    return `<details><summary>📋 JSON数据</summary><pre class="small mt-1">${this.escapeHtml(jsonStr.substring(0, 200))}...</pre></details>`;
                }
                return `<pre class="small">${this.escapeHtml(jsonStr)}</pre>`;
            } catch (e) {
                return '<span class="text-muted">[对象]</span>';
            }
        }
        
        return this.escapeHtml(String(value));
    }

    /**
     * HTML转义
     */
    static escapeHtml(text) {
        if (text === null || text === undefined) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 格式化错误响应
     */
    static formatErrorResponse(error) {
        if (this.isHtmlContent(error)) {
            return error;
        }
        
        return `
            <div class="alert alert-danger">
                <strong>❌ 处理失败</strong>
                <p>${this.escapeHtml(error)}</p>
                <small>请检查查询语法或稍后重试</small>
            </div>
        `;
    }





    

    /**
     * 处理普通聊天请求
     */
    static async handleNormalChatRequest(message) {
        try {
            if (window.aiChatBot) {
                console.log('使用AI聊天机器人处理消息');
                const aiReply = await window.aiChatBot.sendMessage(message);
                return aiReply;
            } else {
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
            
            if (data.status === 'success') {
                return data.message || data.response || `收到: ${message}`;
            } else if (data.status === 'error') {
                return this.formatErrorResponse(data.message);
            }
            
            return data.message || `收到您的消息: ${message}`;

        } catch (error) {
            console.error('备用聊天请求错误:', error);
            return '网络连接出现问题，请稍后重试';
        }
    }

    /**
     * 显示加载状态
     */
    static showLoadingState(message) {
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
            const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
            if (tokenElement && tokenElement.value) {
                return tokenElement.value;
            }

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
}

// 全局注册
window.ChatMessageHandler = ChatMessageHandler;