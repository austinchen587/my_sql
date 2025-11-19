// 辅助函数：填充列表数据
function populateList(items, selector) {
    $(selector).empty();
    if (items && items.length) {
        items.forEach(item => {
            if (item) {
                $(selector).append(`<li class="list-group-item">${item}</li>`);
            }
        });
    }
}

$(document).ready(function() {
    // 初始化DataTable
    const table = $('#procurementTable').DataTable({
        ajax: {
            url: '/emall/procurements/',
            dataSrc: ''
        },
        columns: [
            { data: 'project_title' },
            { data: 'total_price_control' },
            { data: 'publish_date' },
            { data: 'purchasing_unit' },
            { data: 'quote_start_time' },
            { data: 'quote_end_time' },
            { 
                data: 'id',
                render: function(data, type, row) {
                    return `<button class="btn btn-sm btn-primary view-detail" data-id="${data}">查看详情</button>`;
                }
            }
        ],
        order: [[2, 'desc']], // 默认按发布日期降序排序
        language: {
            url: '//cdn.datatables.net/plug-ins/1.13.6/i18n/zh.json'
        }
    });
    
    // 搜索功能
    $('#searchBtn').click(function() {
        table.columns(0).search($('#projectTitleFilter').val());
        table.columns(3).search($('#purchasingUnitFilter').val());
        table.columns(1).search($('#priceControlFilter').val());
        table.draw();
    });
    
    // 重置搜索
    $('#resetBtn').click(function() {
        $('#projectTitleFilter').val('');
        $('#purchasingUnitFilter').val('');
        $('#priceControlFilter').val('');
        table.search('').columns().search('').draw();
    });
    
    // 查看详情按钮事件
    $(document).on('click', '.view-detail', function() {
        const id = $(this).data('id');
        $.get(`/emall/procurements/${id}/`, function(data) {
            $('#detailModalTitle').text(data.project_title || data.project_name);
            $('#detailRegion').text(data.region);
            $('#detailProjectNumber').text(data.project_number);
            $('#detailPriceControl').text(data.total_price_control);
            $('#detailPublishDate').text(data.publish_date);
            $('#detailPurchasingUnit').text(data.purchasing_unit);
            $('#detailQuoteStart').text(data.quote_start_time);
            $('#detailQuoteEnd').text(data.quote_end_time);
            $('#detailUrl').attr('href', data.url).text(data.url);
            
            // 填充数组数据
            populateList(data.commodity_names, '#detailCommodityNames');
            populateList(data.parameter_requirements, '#detailParams');
            populateList(data.purchasequantities, '#detailQuantities');
            populateList(data.suggested_brands, '#detailSuggestedBrands');
            
            // 处理相关链接
            $('#detailLinks').empty();
            if (data.related_links && data.related_links.length) {
                data.related_links.forEach(link => {
                    if (link) {
                        $('#detailLinks').append(`<li class="list-group-item"><a href="${link}" target="_blank">${link}</a></li>`);
                    }
                });
            }
            
            // 处理下载文件
            $('#detailFiles').empty();
            if (data.download_files && data.download_files.length) {
                data.download_files.forEach(file => {
                    if (file) {
                        $('#detailFiles').append(`<li class="list-group-item">${file}</li>`);
                    }
                });
            }
            
            // 商务要求
            $('#detailBusinessReq').empty();
            if (data.business_requirements && data.business_requirements.length) {
                data.business_requirements.forEach(req => {
                    if (req) {
                        $('#detailBusinessReq').append(`<p>${req}</p>`);
                    }
                });
            }
            
            // 显示模态框
            const detailModal = new bootstrap.Modal(document.getElementById('detailModal'));
            detailModal.show();
        }).fail(function() {
            alert('获取详情失败，请稍后重试');
        });
    });
});
