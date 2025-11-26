// 简化的自定义日期排序方法
$.fn.dataTableExt.oSort['date-string-asc'] = function(a, b) {
    if (!a && !b) return 0;
    if (!a) return 1;
    if (!b) return -1;
    if (a === b) return 0;
    
    const dateA = parseDateString(a);
    const dateB = parseDateString(b);
    
    return dateA - dateB;
};

$.fn.dataTableExt.oSort['date-string-desc'] = function(a, b) {
    if (!a && !b) return 0;
    if (!a) return 1;
    if (!b) return -1;
    if (a === b) return 0;
    
    const dateA = parseDateString(a);
    const dateB = parseDateString(b);
    
    return dateB - dateA;
};

// 智能日期渲染器
function dateRenderer(data, type, row) {
    if (!data) return '-';
    
    if (type === 'display') {
        try {
            const date = new Date(data);
            return date.toLocaleDateString('zh-CN');
        } catch (e) {
            return data;
        }
    } else if (type === 'sort') {
        try {
            return new Date(data).getTime();
        } catch (e) {
            return 0;
        }
    }
    
    return data;
}

// 预算控制金额渲染器 - 简洁数字格式
function priceControlRenderer(data, type, row) {
    if (!data || data === '-') return '-';
    
    if (type === 'display') {
        // 转换为数字并格式化为两位小数
        const numericValue = convertPriceToNumber(data);
        if (numericValue !== null) {
            return numericValue.toFixed(2);
        }
        return '-';
    } else if (type === 'sort') {
        // 排序时使用数字值
        const numericValue = convertPriceToNumber(data);
        return numericValue !== null ? numericValue : 0;
    }
    
    return data;
}

// 项目标题渲染器
function projectTitleRenderer(data, type, row) {
    if (!data) return '-';
    const url = row.url || '#';
    return `<a href="${url}" target="_blank" title="${data}">${data.length > 30 ? data.substring(0, 30) + '...' : data}</a>`;
}

// 详情按钮渲染器
function detailButtonRenderer(data) {
    return `<button class="btn btn-sm btn-primary btn-detail" data-id="${data}">详情</button>`;
}

// 列配置定义
const columnDefinitions = [
    { 
        data: 'project_title', 
        name: 'project_title', 
        title: '项目标题',
        render: projectTitleRenderer 
    },
    { 
        data: 'purchasing_unit', 
        name: 'purchasing_unit', 
        title: '采购单位',
        defaultContent: '-' 
    },
    { 
        data: 'region', 
        name: 'region', 
        title: '地区',
        defaultContent: '-' 
    },
    { 
        data: 'total_price_control', 
        name: 'total_price_control', 
        title: '预算控制金额',
        defaultContent: '-',
        render: priceControlRenderer
    },
    { 
        data: 'publish_date', 
        name: 'publish_date', 
        title: '发布日期',
        render: dateRenderer
    },
    { 
        data: 'quote_end_time', 
        name: 'quote_end_time', 
       title: '报价截止时间',
        render: dateRenderer
    },
    { 
        data: 'id', 
        name: 'id', 
        title: '操作',
        orderable: false, 
        render: detailButtonRenderer 
    }
];
