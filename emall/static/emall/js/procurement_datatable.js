// procurement_datatable.js
(function() {
    'use strict';

    // 预算控制金额转换函数 - 与后端和modal保持一致
    window.convertPriceToNumber = function(priceStr) {
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
    };

    // 列配置 - 移除地区列，添加项目编号列
    window.columnDefinitions = [
        { 
            data: null,
            name: 'select',
            title: '选择',
            orderable: false,
            width: '50px',
            render: function(data, type, row) {
                return `<input type="checkbox" class="select-checkbox" data-id="${row.id}" ${row.is_selected ? 'checked' : ''}>`;
            }
        },
        { 
            data: 'project_title', 
            name: 'project_title', 
            title: '项目标题',
            render: function(data, type, row) {
                const url = row.url || '#';
                const titleClass = row.is_selected ? 'text-danger fw-bold' : '';
                return `<a href="${url}" target="_blank" class="${titleClass}" title="${data}">${data.length > 30 ? data.substring(0, 30) + '...' : data}</a>`;
            }
        },
        { 
            data: 'project_number',  // 改为项目编号
            name: 'project_number', 
            title: '项目编号',
            render: function(data, type, row) {
                const textClass = row.is_selected ? 'text-danger fw-bold' : '';
                return `<span class="${textClass} font-monospace">${data || '-'}</span>`;
            }
        },
        { 
            data: 'purchasing_unit', 
            name: 'purchasing_unit', 
            title: '采购单位',
            render: function(data, type, row) {
                const textClass = row.is_selected ? 'text-danger fw-bold' : '';
                return `<span class="${textClass}">${data || ''}</span>`;
            }
        },
        { 
            data: 'total_price_control', 
            name: 'total_price_control', 
            title: '预算控制金额',
            render: function(data, type, row) {
                const textClass = row.is_selected ? 'text-danger fw-bold' : '';
                
                // 修复：添加金额转换逻辑
                if (!data || data === '-' || data === '') {
                    return `<span class="${textClass}">-</span>`;
                }
                
                // 显示处理：转换为数字并格式化
                if (type === 'display') {
                    const numericValue = window.convertPriceToNumber(data);
                    if (numericValue !== null) {
                        // 使用toLocaleString格式化数字，保留2位小数，添加千分位分隔符
                        return `<span class="${textClass} fw-bold text-success">¥${numericValue.toFixed(2)}</span>`;
                    }
                    // 如果无法转换，显示原始值
                    return `<span class="${textClass}">${data}</span>`;
                } 
                // 排序处理：使用数字值进行排序
                else if (type === 'sort') {
                    const numericValue = window.convertPriceToNumber(data);
                    return numericValue !== null ? numericValue : 0;
                }
                
                return `<span class="${textClass}">${data}</span>`;
            }
        },
        { 
            data: 'publish_date', 
            name: 'publish_date', 
            title: '发布日期',
            render: function(data, type, row) {
                const textClass = row.is_selected ? 'text-danger fw-bold' : '';
                return `<span class="${textClass}">${data || ''}</span>`;
            }
        },
        { 
            data: 'quote_end_time', 
            name: 'quote_end_time', 
            title: '报价截止时间',
            render: function(data, type, row) {
                const textClass = row.is_selected ? 'text-danger fw-bold' : '';
                return `<span class="${textClass}">${data || ''}</span>`;
            }
        },
        { 
            data: null,
            name: 'actions',
            title: '操作',
            orderable: false,
            width: '150px',
            render: function(data, type, row) {
                const detailBtn = `<button class="btn btn-sm btn-primary btn-detail me-1" data-id="${row.id}">详情</button>`;
                const progressBtn = row.is_selected ? `<button class="btn btn-sm btn-warning btn-progress me-1" data-id="${row.id}">采购进度</button>` : '';
                return detailBtn + progressBtn;
            }
        }
    ];

    // 检查日期时间是否早于当前时间
    window.isDateTimeBeforeNow = function(dateTimeString) {
        if (!dateTimeString) return false;
        
        try {
            const targetDateTime = new Date(dateTimeString);
            const currentDateTime = new Date();
            return targetDateTime < currentDateTime;
        } catch (e) {
            console.warn('日期时间解析错误:', dateTimeString, e);
            return false;
        }
    };

    // DataTables配置
    window.initializeDataTable = function() {
        return $('#procurementTable').DataTable({
            processing: true,
            serverSide: true,
            ajax: {
                url: '/emall/procurements/',
                type: 'GET',
                data: function(d) {
                    const params = {
                        draw: d.draw,
                        start: d.start,
                        length: d.length,
                        search: d.search.value,
                        ordering: window.getOrderingParam(d, window.columnDefinitions)
                    };
                    
                    window.addFilterParams(params);
                    return params;
                },
                dataSrc: function(json) {
                    console.log('API响应数据:', json);
                    if (!json || json.error) {
                        console.error('API返回错误:', json ? json.error : '无响应数据');
                        return [];
                    }
                    
                    if (json.recordsFiltered === undefined) {
                        json.recordsFiltered = json.recordsTotal || 0;
                    }
                    
                    return json.data;
                },
                error: function(xhr) {
                    console.error('DataTables AJAX错误:', xhr);
                    alert('加载数据时发生错误');
                }
            },
            columns: window.columnDefinitions,
            language: {
                processing: "处理中...",
                lengthMenu: "显示 _MENU_ 条",
                zeroRecords: "没有找到匹配的记录",
                info: "显示第 _START_ 至 _END_ 条，共 _TOTAL_ 条",
                infoEmpty: "没有记录",
                infoFiltered: "(从 _MAX_ 条记录中筛选)",
                search: "搜索:",
                paginate: {
                    first: "首页",
                    last: "末页",
                    next: "下一页",
                    previous: "上一页"
                }
            },
            responsive: true,
            order: [[5, 'desc']], // 调整为新的列索引
            pageLength: 25,
            lengthMenu: [
                [10, 25, 50, 100, 500, -1],
                ['10 条', '25 条', '50 条', '100 条', '500 条', '所有']
            ],
            createdRow: function(row, data, dataIndex) {
                if (data.is_selected) {
                    $(row).addClass('selected-row');
                    $(row).find('td').not(':first').addClass('text-danger');
                }
                
                // 使用全局函数判断是否过期
                if (window.isDateTimeBeforeNow(data.quote_end_time)) {
                    const cells = $(row).find('td');
                    cells.css('background-color', '#F9E7B2');
                    $(row).addClass('expired-row');
                    $(row).attr('title', '该项目报价已截止');
                }
            },
            initComplete: function() {
                console.log('DataTables初始化完成');
                if (window.initSelectionModule) {
                    window.initSelectionModule(this.api());
                }
            },
            drawCallback: function() {
                console.log('表格重绘完成，共渲染 ' + this.api().rows().count() + ' 行数据');
                if (window.initSelectionModule) {
                    window.initSelectionModule(this.api());
                }
                
                const expiredCount = $('.expired-row').length;
                if (expiredCount > 0) {
                    console.log('发现 ' + expiredCount + ' 个已过期项目');
                }
                
                // 绑定详情按钮事件
                $('#procurementTable').off('click', '.btn-detail').on('click', '.btn-detail', function() {
                    const procurementId = $(this).data('id');
                    console.log('详情按钮点击，ID:', procurementId);
                    
                    if (typeof window.showDetailModal === 'function') {
                        window.showDetailModal(procurementId);
                    } else {
                        console.error('showDetailModal函数未定义');
                        alert('详情功能暂不可用');
                    }
                });
                
                // 绑定进度按钮事件
                $('#procurementTable').off('click', '.btn-progress').on('click', '.btn-progress', function() {
                    const procurementId = $(this).data('id');
                    console.log('采购进度按钮点击，ID:', procurementId);
                    
                    if (typeof window.showProgressModal === 'function') {
                        window.showProgressModal(procurementId);
                    } else {
                        console.error('showProgressModal函数未定义');
                        alert('采购进度功能暂不可用');
                    }
                });
            }
        });
    };
})();
