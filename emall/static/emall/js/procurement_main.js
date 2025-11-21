// procurement_main.js
(function() {
    'use strict';
    
    // 加载指示器
    $(document).ajaxStart(function() {
        $("#loading").show();
    }).ajaxStop(function() {
        $("#loading").hide();
    });

    // 绑定详情事件 - 使用全局函数
    function bindDetailEvents() {
        $('#procurementTable').off('click', '.btn-detail').on('click', '.btn-detail', function() {
            const procurementId = $(this).data('id');
            console.log('详情按钮点击，ID:', procurementId);
            
            // 使用全局的showDetailModal函数
            if (typeof showDetailModal === 'function') {
                showDetailModal(procurementId);
            } else {
                console.error('showDetailModal函数未定义');
                alert('详情功能暂不可用');
            }
        });
    }

    // 绑定进度事件
    function bindProgressEvents() {
        $('#procurementTable').off('click', '.btn-progress').on('click', '.btn-progress', function() {
            const procurementId = $(this).data('id');
            console.log('采购进度按钮点击，ID:', procurementId);
            
            if (typeof showProgressModal === 'function') {
                showProgressModal(procurementId);
            } else {
                console.error('showProgressModal函数未定义');
                alert('采购进度功能暂不可用');
            }
        });
    }

    // 主初始化函数
    $(document).ready(function() {
        console.log('页面加载完成，开始初始化DataTable');
        
        // 确保所有依赖函数都已加载
        if (typeof window.initializeDataTable === 'function') {
            const table = window.initializeDataTable();
            
            // 绑定搜索事件
            if (typeof window.bindSearchEvents === 'function') {
                window.bindSearchEvents(table);
            }
            
            // 绑定详情和进度事件
            bindDetailEvents();
            bindProgressEvents();
            
            console.log('DataTable初始化完成，所有事件已绑定');
        } else {
            console.error('initializeDataTable 函数未定义');
        }
    });
})();
