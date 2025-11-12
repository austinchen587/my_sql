// chat_ai_history.js - 对话历史管理功能

class ChatHistoryManager {
    constructor() {
        this.CHAT_HISTORY_KEY = 'ai_chat_history';
        this.MAX_HISTORY_SESSIONS = 20; // 最大保存的对话会话数
        this.currentSessionId = this.getCurrentSessionId();
    }

    // 获取当前对话会话ID
    getCurrentSessionId() {
        let sessionId = localStorage.getItem('current_chat_session');
        if (!sessionId) {
            sessionId = 'session_' + Date.now();
            localStorage.setItem('current_chat_session', sessionId);

        }
        return sessionId;
    }

     // 创建新会话
     createNewSession() {
        this.currentSessionId = 'session_' + Date.now();
        localStorage.setItem('current_chat_session', this.currentSessionId)
        return this.currentSessionId;
     }

     // 保存对话记录到本地存储
     saveChatHistory(history) {
        try {
            const sessionData = {
                id: this.currentSessionId,
                title: this.generateSessionTitle(history),
                history: history,
                lastUpdated: Date.now(),
                messageCount: history.length,
                created: Date.now()
            };

             // 获取所有会话历史
             const allSessions = this.getAllSessions();


             // 更新当前会话 - 新增这一行
             allSessions[this.currentSessionId] = sessionData;




              // 限制保存的会话数量
              this.limitSessionsCount(allSessions);

              localStorage.setItem(this.CHAT_HISTORY_KEY, JSON.stringify(allSessions));
              console.log('对话历史已保存', sessionData);
              return true;
        } catch (error) {
            console.error('保存对话历史失败:', error);
            return false;
        }
     }

      // 从本地存储加载当前会话的历史
      loadCurrentSessionHistory() {
        try {
            const allSessions = this.getAllSessions();
            const currentSession = allSessions[this.currentSessionId];

            if (currentSession && currentSession.history) {
                console.log('对话历史已加载', currentSession.history.length, '条消息');
                return currentSession.history;
            }
        } catch (error) {
            console.error('加载对话历史失败:', error);
        }
        return [];       
      }

       // 加载指定会话的历史
       loadSessionHistory(sessionId) {
        try {
            const allSessions = this.getAllSessions();
            const session = allSessions[sessionId];
            
            if (session && session.history) {
                this.currentSessionId = sessionId;
                localStorage.setItem('current_chat_session', sessionId);
                return session.history;
            }
        } catch (error) {
            console.error('加载指定会话历史失败:', error);
        }
        return [];

       }

       // 获取所有会话列表
       getAllSessions() {
        try {
            const sessionsJson = localStorage.getItem(this.CHAT_HISTORY_KEY);
            return sessionsJson ? JSON.parse(sessionsJson) : {};
        } catch (error) {
            console.error('获取会话列表失败:', error);
            return {};

        }
       }

       // 获取会话列表（按时间倒序）
       getSessionList() {
        const allSessions = this.getAllSessions();
        return Object.values(allSessions)
            .sort((a, b) => b.lastUpdated - a.lastUpdated);
    }


     // 删除指定会话

     deleteSession(sessionId) {
        try {
            const allSessions = this.getAllSessions();
            delete allSessions[sessionId];
            localStorage.setItem(this.CHAT_HISTORY_KEY, JSON.stringify(allSessions));
            
            // 如果删除的是当前会话，创建新会话
            if (sessionId === this.currentSessionId) {
                this.createNewSession();
            }
            
            return true;
        } catch (error) {
            console.error('删除会话失败:', error);
            return false;
        }
    }

     // 清空所有历史记录
     clearAllHistory() {
        try {
            localStorage.removeItem(this.CHAT_HISTORY_KEY);
            this.createNewSession();
            return true;
        } catch (error) {
            console.error('清空历史记录失败:', error);
            return false;
        }
    }

     // 导出所有历史记录为JSON文件
     exportHistory() {
        try {
            const allSessions = this.getAllSessions();
            const dataStr = JSON.stringify(allSessions, null, 2);
            const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
            
            const exportFileDefaultName = `ai_chat_history_${new Date().toISOString().split('T')[0]}.json`;
            
            const linkElement = document.createElement('a');
            linkElement.setAttribute('href', dataUri);
            linkElement.setAttribute('download', exportFileDefaultName);
            linkElement.click();
            
            return true;
        } catch (error) {
            console.error('导出历史记录失败:', error);
            return false;
        }
    }

    // 导入历史记录
    importHistory(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const importedSessions = JSON.parse(e.target.result);
                    const existingSessions = this.getAllSessions();
                    
                    // 合并会话（避免ID冲突）
                    const mergedSessions = { ...importedSessions, ...existingSessions };
                    localStorage.setItem(this.CHAT_HISTORY_KEY, JSON.stringify(mergedSessions));
                    
                    resolve(true);
                } catch (error) {
                    reject(new Error('文件格式错误'));
                }
            };
            reader.onerror = () => reject(new Error('文件读取失败'));
            reader.readAsText(file);
        });
    }

    // 生成会话标题（基于第一条用户消息）
    generateSessionTitle(history) {
        const firstUserMessage = history.find(msg => msg.role === 'user');
        if (firstUserMessage && firstUserMessage.content) {
            const content = firstUserMessage.content;
            return content.length > 25 ? content.substring(0, 25) + '...' : content;
        }
        return '新对话 ' + new Date().toLocaleDateString();
    }

     // 限制会话数量
     limitSessionsCount(allSessions) {
        const sessionIds = Object.keys(allSessions);
        if (sessionIds.length > this.MAX_HISTORY_SESSIONS) {
            // 按时间排序，删除最旧的会话
            const sortedSessions = sessionIds.sort((a, b) => 
                allSessions[a].lastUpdated - allSessions[b].lastUpdated
            );
            
            const sessionsToDelete = sortedSessions.slice(0, sessionIds.length - this.MAX_HISTORY_SESSIONS);
            sessionsToDelete.forEach(sessionId => {
                delete allSessions[sessionId];
            });
        }
    }


    // 获取当前会话信息

    getCurrentSessionInfo() {
        const allSessions = this.getAllSessions();
        return allSessions[this.currentSessionId];
    }
}


// 创建全局实例
window.ChatHistoryManager = ChatHistoryManager;




















