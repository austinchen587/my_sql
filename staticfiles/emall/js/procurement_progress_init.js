/**
 * 采购进度管理初始化模块
 */

// 在页面加载时创建模态框
$(document).ready(function() {
    // 初始化模态框堆栈
    modalStack = [];
    
    // 监听所有模态框的显示事件
    $(document).on('show.bs.modal', '.modal', function() {
        const modalId = $(this).attr('id');
        if (modalId && !modalStack.includes(modalId)) {
            modalStack.push(modalId);
            updateModalZIndexes();
        }
    });
    
    // 监听所有模态框的隐藏事件
    $(document).on('hidden.bs.modal', '.modal', function() {
        const modalId = $(this).attr('id');
        const index = modalStack.indexOf(modalId);
        if (index > -1) {
            modalStack.splice(index, 1);
            updateModalZIndexes();
        }
    });
});
