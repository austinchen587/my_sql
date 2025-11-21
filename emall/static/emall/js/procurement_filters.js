// procurement_filters.js
(function() {
    'use strict';
    
    // 搜索按钮事件
    window.bindSearchEvents = function(table) {
        $('#searchBtn').off('click').on('click', function() {
            console.log('搜索按钮点击，重新加载数据');
            table.ajax.reload();
        });

        // 重置按钮事件
        $('#resetBtn').off('click').on('click', function() {
            console.log('重置按钮点击');
            $('.filter-input').val('');
            table.ajax.reload();
        });

        // 回车键搜索
        $('.filter-input').off('keypress').on('keypress', function(e) {
            if (e.which === 13) {
                console.log('回车键搜索');
                table.ajax.reload();
            }
        });
    };
})();
