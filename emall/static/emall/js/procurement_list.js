$(document).ajaxStart(function() {
    $("#loading").show();
}).ajaxStop(function() {
 $("#loading").hide();
});

$(function() {
    // 注册自定义日期排序插件（处理字符串格式的日期）
    $.fn.dataTable.ext.type.order['date-string-asc'] = function(a, b) {
        // 处理空值
        if (!a) return 1;
        if (!b) return -1;
        if (a === b) return 0;
        
        // 尝试解析日期字符串
        const dateA = parseDateString(a);
        const dateB = parseDateString(b);
        
        return dateA - dateB;
    };

    $.fn.dataTable.ext.type.order['date-string-desc'] = function(a, b) {
        // 处理空值
        if (!a) return 1;
        if (!b) return -1;
        if (a === b) return 0;
        
        // 尝试解析日期字符串
        const dateA = parseDateString(a);
        const dateB = parseDateString(b);
        
        return dateB - dateA;
    };

    // 日期字符串解析函数
    function parseDateString(dateStr) {
        if (!dateStr) return new Date(0); // 返回最小日期
        
        // 尝试常见的日期格式
        const formats = [
            /^(\d{4})-(\d{2})-(\d{2})$/, // YYYY-MM-DD
            /^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})$/, // YYYY-MM-DD HH:MM:SS
            /^(\d{4})\/(\d{2})\/(\d{2})$/, // YYYY/MM/DD
            /^(\d{4})\/(\d{2})\/(\d{2}) (\d{2}):(\d{2}):(\d{2})$/ // YYYY/MM/DD HH:MM:SS
        ];
        
        for (let format of formats) {
            const match = dateStr.match(format);
            if (match) {
                if (match.length === 4) {
                    // YYYY-MM-DD 格式
                    return new Date(match[1], match[2] - 1, match[3]);
                } else if (match.length === 7) {
                    // YYYY-MM-DD HH:MM:SS 格式
                    return new Date(match[1], match[2] - 1, match[3], match[4], match[5], match[6]);
                }
            }
        }
        
        // 如果无法解析，返回原始字符串的Date对象（可能无效）
        return new Date(dateStr);
    }

    // 定义列配置（确保与后端字段一致）
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
            defaultContent: '-' 
        },
        { 
            data: 'publish_date', 
            name: 'publish_date', 
            title: '发布日期',
            render: dateRenderer,
            type: 'date-string'  // 使用自定义日期排序类型
        },
        { 
            data: 'quote_end_time', 
            name: 'quote_end_time', 
            title: '报价截止时间',
            render: dateRenderer,
            type: 'date-string'  // 使用自定义日期排序类型
        },
        { 
            data: 'id', 
            name: 'id', 
            title: '操作',
            orderable: false, 
            render: detailButtonRenderer 
        }
    ];

    // 初始化DataTables
    const table = $('#procurementTable').DataTable({
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
                    ordering: getOrderingParam(d, columnDefinitions)
                };

                // 添加筛选参数
                addFilterParams(params);

                console.log('AJAX请求参数:', params);
                return params;
            },
            dataSrc: function(json) {
                console.log('API响应数据:', json);
                if (!json || json.error) {
                    console.error('API返回错误:', json ? json.error : '无响应数据');
                    return [];
                }
                
                // 确保recordsFiltered正确设置
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
        columns: columnDefinitions,
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
        order: [[4, 'asc']], // 修改为按发布日期升序排列
        pageLength: 25,
        lengthMenu: [
        [10, 25, 50, 100, 500, -1],
        ['10 条', '25 条', '50 条', '100 条', '500 条', '所有']// 下拉选项的显示文字
    ],
        initComplete: function() {
            console.log('DataTables初始化完成');
        },
        drawCallback: function() {
            console.log('表格重绘完成');
        }
    });

    // 排序参数生成函数 - 修复排序参数格式问题
    function getOrderingParam(d, columns) {
        if (!d.order || d.order.length === 0) return '';
        
        const orderParams = [];
        
        d.order.forEach(orderItem => {
            const columnIndex = orderItem.column;
            const dir = orderItem.dir;
            const columnName = columns[columnIndex]?.name;
            
            if (columnName) {
                // DRF期望的格式：字段名（升序）或-字段名（降序）
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

    // 项目标题渲染器
    function projectTitleRenderer(data, type, row) {
        if (!data) return '-';
        const url = row.url || '#';
        return `<a href="${url}" target="_blank" title="${data}">${data.length > 30 ? data.substring(0, 30) + '...' : data}</a>`;
    }

    // 日期渲染器
    function dateRenderer(data) {
        if (!data) return '-';
        try {
            return new Date(data).toLocaleDateString('zh-CN');
        } catch (e) {
            return data; // 如果日期格式无效，返回原始值
        }
    }

    // 详情按钮渲染器
    function detailButtonRenderer(data) {
        return `<button class="btn btn-sm btn-primary btn-detail" data-id="${data}">详情</button>`;
    }

    // 搜索按钮事件
    $('#searchBtn').on('click', function() {
        table.ajax.reload();
    });

    // 重置按钮事件
    $('#resetBtn').on('click', function() {
        $('.filter-input').val('');
        table.ajax.reload();
    });

    // 回车键搜索
    $('.filter-input').on('keypress', function(e) {
        if (e.which === 13) {
            table.ajax.reload();
        }
    });

    // 详情按钮点击事件
    $('#procurementTable').on('click', '.btn-detail', function() {
        const id = $(this).data('id');
        showDetailModal(id);
    });

    // 显示详情弹窗
    function showDetailModal(id) {
        const modalEl = document.getElementById('detailModal');
        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        
        console.log('正在请求详情数据，ID:', id);
        
        // 先显示加载状态
        $('#detailModalContent').html(`
            <div class="modal-header">
                <h5 class="modal-title">加载中...</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body text-center py-4">
                <div class="spinner-border text-primary"></div>
                <p class="mt-2">加载项目详情...</p>
            </div>
        `);
        
        modal.show();
        
        $.ajax({
            url: `/emall/procurements/${id}/`,
            type: 'GET',
            success: function(data) {
                console.log('详情数据响应:', data);
                try {
                    renderDetailContent(data);
                } catch (error) {
                    console.error('渲染详情失败:', error);
                    $('#detailModalContent').html(`
                        <div class="modal-header">
                            <h5 class="modal-title">错误</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="alert alert-danger">
                                <h5>渲染失败</h5>
                                <p>${error.message || '渲染详情内容时出错'}</p>
                            </div>
                        </div>
                    `);
                }
            },
            error: function(xhr, status, error) {
                console.error('加载详情失败:', {
                    status: status,
                    error: error,
                    responseText: xhr.responseText,
                    responseJSON: xhr.responseJSON
                });
                $('#detailModalContent').html(`
                    <div class="modal-header">
                        <h5 class="modal-title">错误</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="alert alert-danger">
                            <h5>加载失败</h5>
                            <p>${xhr.responseJSON?.detail || '无法加载项目详情，请稍后重试'}</p>
                        </div>
                    </div>
                `);
            }
        });

        function renderDetailContent(data) {
            // 确保数组字段不为undefined/null
            const safeArray = (arr) => Array.isArray(arr) ? arr : [];
            
            const htmlContent = `
                <div class="modal-header">
                    <h5 class="modal-title">${data.project_title || '采购项目详情'}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <h6>基本信息</h6>
                            <table class="table table-sm table-borderless">
                                <tbody>
                                    <tr><th class="w-25">采购单位</th><td>${data.purchasing_unit || '-'}</td></tr>
                                    <tr><th>项目编号</th><td>${data.project_number || '-'}</td></tr>
                                    <tr><th>预算控制</th><td>${data.total_price_control || '-'}</td></tr>
                                    <tr><th>地区</th><td>${data.region || '-'}</td></tr>
                                </tbody>
                            </table>
                        </div>
                        <div class="col-md-6">
                            <h6>时间信息</h6>
                            <table class="table table-sm table-borderless">
                                <tbody>
                                    <tr><th class="w-25">发布日期</th><td>${formatDate(data.publish_date)}</td></tr>
                                    <tr><th>报价开始</th><td>${formatDate(data.quote_start_time)}</td></tr>
                                    <tr><th>报价截止</th><td>${formatDate(data.quote_end_time)}</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    ${renderSection('商品信息', safeArray(data.commodity_names))}
                    ${renderSection('技术参数', safeArray(data.parameter_requirements))}
                    ${renderSection('采购数量', safeArray(data.purchase_quantities))}
                    ${renderSection('控制金额', safeArray(data.control_amounts))}
                    ${renderSection('推荐品牌', safeArray(data.suggested_brands))}
                    ${renderSection('商务要求', safeArray(data.business_requirements))}
                    ${renderSection('下载文件', safeArray(data.download_files))}
                    
                    <div class="text-end mt-3">
                        <a href="${data.url || '#'}" target="_blank" class="btn btn-outline-primary">查看原链接</a>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                </div>
            `;
            
            $('#detailModalContent').html(htmlContent);
        }

        function formatDate(dateString) {
            if (!dateString) return '-';
            try {
                return new Date(dateString).toLocaleString('zh-CN');
            } catch (e) {
                return dateString;
            }
        }

        function renderSection(title, items) {
            if (!items || items.length === 0) return '';
            
            const itemsHtml = items.map(item => 
                `<li class="list-group-item">${item || '-'}</li>`
            ).join('');
            
            return `
                <div class="mb-3">
                    <h6 class="border-bottom pb-1">${title}</h6>
                    <ul class="list-group list-group-flush">
                        ${itemsHtml}
                    </ul>
                </div>
            `;
        }
    }
});
