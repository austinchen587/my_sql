// 检查日期时间是否早于当前时间
function isDateTimeBeforeNow(dateTimeString) {
    if (!dateTimeString) return false;
    
    try {
        const targetDateTime = new Date(dateTimeString);
        const currentDateTime = new Date();
        return targetDateTime < currentDateTime;
    } catch (e) {
        console.warn('日期时间解析错误:', dateTimeString, e);
        return false;
    }
}

// DataTables配置
function initializeDataTable() {
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
                    ordering: getOrderingParam(d, columnDefinitions)
                };
                
                console.log('分页调试 - 前端发送:', {
                    start: d.start,
                    length: d.length,
                    calculated_page: Math.floor(d.start / d.length) + 1
                });
                
                addFilterParams(params);
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
        order: [[4, 'desc']],
        pageLength: 25,
        lengthMenu: [
            [10, 25, 50, 100, 500, -1],
            ['10 条', '25 条', '50 条', '100 条', '500 条', '所有']
        ],
        createdRow: function(row, data, dataIndex) {
            // 检查报价截止时间是否早于当前时间
            if (isDateTimeBeforeNow(data.quote_end_time)) {
                // 设置每个单元格的背景色
                const cells = $(row).find('td');
                cells.css('background-color', '#F9E7B2');
                $(row).addClass('expired-row');
                
                // 可选：为过期行添加提示
                $(row).attr('title', '该项目报价已截止');
            }
        },
        initComplete: function() {
            console.log('DataTables初始化完成');
        },
        drawCallback: function() {
            console.log('表格重绘完成，共渲染 ' + this.api().rows().count() + ' 行数据');
            
            // 可选：统计过期项目数量
            const expiredCount = $('.expired-row').length;
            if (expiredCount > 0) {
                console.log('发现 ' + expiredCount + ' 个已过期项目');
            }
        }
    });
}
