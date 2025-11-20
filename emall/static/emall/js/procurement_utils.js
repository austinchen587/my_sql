// 日期字符串解析函数
function parseDateString(dateStr) {
    if (!dateStr) return new Date(0);
    
    const cleanStr = dateStr.replace(/\(.*\)/g, '').trim();
    
    const formats = [
        /^(\d{4})-(\d{2})-(\d{2})$/,
        /^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})$/,
        /^(\d{4})\/(\d{2})\/(\d{2})$/,
        /^(\d{4})\/(\d{2})\/(\d{2}) (\d{2}):(\d{2}):(\d{2})$/
    ];
    
    for (let format of formats) {
        const match = cleanStr.match(format);
        if (match) {
            if (match.length === 4) {
                return new Date(match[1], match[2] - 1, match[3]);
            } else if (match.length === 7) {
                return new Date(match[1], match[2] - 1, match[3], match[4], match[5], match[6]);
            }
        }
    }
    
    return new Date(cleanStr);
}

// 格式化日期显示
function formatDate(dateString) {
    if (!dateString) return '-';
    try {
        return new Date(dateString).toLocaleString('zh-CN');
    } catch (e) {
        return dateString;
    }
}

// 安全数组处理
function safeArray(arr) {
    return Array.isArray(arr) ? arr : [];
}

// 排序参数生成函数
function getOrderingParam(d, columns) {
    if (!d.order || d.order.length === 0) return '';
    
    const orderParams = [];
    
    d.order.forEach(orderItem => {
        const columnIndex = orderItem.column;
        const dir = orderItem.dir;
        const columnName = columns[columnIndex]?.name;
        
        if (columnName) {
            const param = dir === 'desc' ? `-${columnName}` : columnName;
            orderParams.push(param);
        }
    });
    
    return orderParams.join(',');
}

// 添加筛选参数
function addFilterParams(params) {
    const filters = {
        project_title: $('#projectTitleFilter').val(),
        purchasing_unit: $('#purchasingUnitFilter').val(),
        total_price_control: $('#priceControlFilter').val(),
        region: $('#regionFilter').val()
    };
    
    Object.keys(filters).forEach(key => {
        if (filters[key]) {
            params[key] = filters[key];
        }
    });
}
