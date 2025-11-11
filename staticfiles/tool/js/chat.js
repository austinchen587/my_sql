
// 聊天对话框功能
document.addEventListener('DOMContentLoaded',function() {
    // DOM元素获取
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('sent-button');
    const messageArea = document.getElementById('message-area');
    const characterCont =document.getElementById('character-count');

     // 最大字符数限制
     const MAX_CHARACTERS = 1800;

     // 更新字符计数
     function updateCharacterCount() {
        const count =messageInput.value.length;
        characterCont.textContent = `${count}/${MAX_CHARACTERS}`;

        // 当接近或超过限制时改变颜色
        if (count > MAX_CHARACTERS * 0.9) {
            characterCont.classList.add('warning');

        } else {
            characterCont.classList.remove('warning');
        }

     }

     // 发送消息功能
     function sentMessage() {
        const messageText = messageInput.value.trim();
        
        // 验证消息
        if (!messageText) {
            messageInput.focus();
            return;
        }

        if (messageText.length > MAX_CHARACTERS) {
            alert('消息不能超过${MAX_CHARACTERS}个字符');
            return;
        }

         // 创建消息元素
         createMessageElement(messageText,'sent');

          // 模拟回复（2秒后）
          setTimeout(() => {
            const replies = [
                "感谢您的消息！",
                "我明白了，请继续。",
                "这是一个很好的问题，让我查一下相关信息。",
                "我已经记录下您的反馈。",
                "我们正在处理您的请求，请稍等片刻。"

            ];
            const randomReply = replies[Math.floor(Math.random() * replies.length)];
            createMessageElement(randomReply,'received');
          },2000);

          // 清空输入框并更新计数
          messageInput.value='';
          updateCharacterCount();

          // 焦点回到输入框
          messageInput.focus();

     }

     // 创建消息元素并添加到聊天区域
     function createMessageElement(text,tpye) {
        // 创建消息容器
        const messageElement = document.cteateElement('div');
        avatar.className = 'message-avatar d-flex align-items-center justify-content-center';
        avatar.innerHTML = type === 'sent'?
        '<span class="text-white fw-bold>U</span>':
        '<span class="text-white fw-bold">AI</span>';


         // 创建消息内容
         const messageContent = document.createElement('div');
         messageContent.className = 'message-content';


         // 添加发送者名称
         const sender = document.createElement('div');
         sender.className = 'message-sender';
         sender.textContent = type === 'sent' ? '您' : '客服助手';

         // 添加消息文本
         const messageText = document.createElement('div');
         messageText.className = 'message-text';
         messageText.textContent = text;

         // 添加时间戳
         const time = document.createElement('div');
         time.className = 'message-time';
         time.textContent = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

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

     }

     // 事件监听器
     sendButton.addEventListener('click', sendMessage);

     messageInput.addEventListener('keyup',function(e) {
        updateCharacterCount();

        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
        }

     }
    );

    // 页面加载后焦点自动放在输入框
    messageInput.focus();
    updateCharacterCount();






}

)