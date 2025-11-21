// procurement_datatable.js
(function() {
    'use strict';

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
                return `<span class="${textClass}">${data || ''}</span>`;
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

    // 检查日期时间是否早于当前时间（移至全局作用域）
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
