// procurement_helpers.js
(function() {
    'use strict';

    // 添加过滤器参数到请求
    window.addFilterParams = function(params) {
        // 项目标题
        const projectTitle = $('#projectTitleFilter').val();
        if (projectTitle) {
            params.project_title = projectTitle;
        }
        
        // 采购单位
        const purchasingUnit = $('#purchasingUnitFilter').val();
        if (purchasingUnit) {
            params.purchasing_unit = purchasingUnit;
        }
        
        // 项目编号 - 替换原来的地区搜索
        const projectNumber = $('#projectNumberFilter').val();
        if (projectNumber) {
            params.project_number = projectNumber;
        }
        
        // 预算控制金额
        const priceControl = $('#priceControlFilter').val();
        if (priceControl) {
            params.total_price_control = priceControl;
        }
        
        // 只看已选择项目
        const showSelectedOnly = $('#showSelectedOnly').prop('checked');
        if (showSelectedOnly) {
            params.show_selected_only = true;
        }
        
        console.log('搜索参数:', params);
    };

    // 获取排序参数
    window.getOrderingParam = function(d, columns) {
        if (!d.order || d.order.length === 0) {
            return '-publish_date'; // 默认按发布日期降序
        }

        const order = d.order[0];
        const columnIndex = order.column;
        const column = columns[columnIndex];
        const direction = order.dir === 'asc' ? '' : '-';
        
        if (column.name) {
            return direction + column.name;
        }
        
        return '-publish_date';
    };
})();
