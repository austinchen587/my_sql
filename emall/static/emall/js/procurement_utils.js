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

// 预算控制金额转换为数字值（修正版）
function convertPriceToNumber(priceStr) {
    if (!priceStr || priceStr === '-') return null;
    
    try {
        // 移除空格和逗号
        const cleanStr = priceStr.toString().replace(/[\s,]/g, '');
        
        // 1. 先检查"万元"（不包含"元万元"的情况）
        if (cleanStr.includes('万元') && !cleanStr.includes('元万元')) {
            // 处理"万元"情况：提取数字部分乘以10000
            const numberMatch = cleanStr.match(/(\d+\.?\d*)\s*万元/);
            if (numberMatch) {
                const numberValue = parseFloat(numberMatch[1]);
                return numberValue * 10000;
            }
        }
        
        // 2. 处理"元万元"情况（直接提取数字，不乘以10000）
        if (cleanStr.includes('元万元')) {
            const numberMatch = cleanStr.match(/(\d+\.?\d*)/);
            if (numberMatch) {
                return parseFloat(numberMatch[1]);
            }
        }
        
        // 3. 处理单独的"元"情况
        if (cleanStr.includes('元') && !cleanStr.includes('万元')) {
            const numberMatch = cleanStr.match(/(\d+\.?\d*)\s*元/);
            if (numberMatch) {
                return parseFloat(numberMatch[1]);
            }
        }
        
        // 4. 如果没有单位，尝试直接解析为数字
        const numberValue = parseFloat(cleanStr);
        if (!isNaN(numberValue)) {
            return numberValue;
        }
    } catch (e) {
        console.warn('金额转换失败:', priceStr, e);
    }
    
    return null;
}

// 解析搜索操作符和数值
function parsePriceSearch(searchValue) {
    if (!searchValue) return null;
    
    const trimmedValue = searchValue.trim();
    
    // 匹配操作符：> >= < <= = ==
    const operatorMatch = trimmedValue.match(/^(>=|<=|>|<|=|==)\s*(\d+\.?\d*)$/);
    if (operatorMatch) {
        const operator = operatorMatch[1];
        const numberValue = parseFloat(operatorMatch[2]);
        return { operator, value: numberValue };
    }
    
    // 匹配范围：1000-5000
    const rangeMatch = trimmedValue.match(/^(\d+\.?\d*)\s*-\s*(\d+\.?\d*)$/);
    if (rangeMatch) {
        return { 
            operator: 'range', 
            min: parseFloat(rangeMatch[1]), 
            max: parseFloat(rangeMatch[2]) 
        };
    }
    
    // 纯数字：视为等于
    const numberValue = parseFloat(trimmedValue);
    if (!isNaN(numberValue)) {
        return { operator: '=', value: numberValue };
    }
    
    return null;
}

// 添加筛选参数（增强版）
function addFilterParams(params) {
    const filters = {
        project_title: $('#projectTitleFilter').val(),
        purchasing_unit: $('#purchasingUnitFilter').val(),
        total_price_control: $('#priceControlFilter').val(),
        region: $('#regionFilter').val()
    };
    
    Object.keys(filters).forEach(key => {
        if (filters[key]) {
            // 特殊处理预算控制金额搜索
            if (key === 'total_price_control') {
                const searchParams = parsePriceSearch(filters[key]);
                if (searchParams) {
                    params[`${key}_search`] = JSON.stringify(searchParams);
                } else {
                    // 如果无法解析为数字搜索，使用原来的模糊搜索
                    params[key] = filters[key];
                }
            } else {
                params[key] = filters[key];
            }
        }
    });
}
