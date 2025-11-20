// 渲染详情部分
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

// 渲染详情内容
function renderDetailContent(data) {
    // 转换预算控制金额为数字格式
    const priceControlDisplay = (function() {
        const numericValue = convertPriceToNumber(data.total_price_control);
        return numericValue !== null ? numericValue.toFixed(2) : (data.total_price_control || '-');
    })();
    
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
                            <tr><th>预算控制</th><td>${priceControlDisplay}</td></tr>
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
}

// 绑定详情按钮事件
function bindDetailEvents(table) {
    $('#procurementTable').on('click', '.btn-detail', function() {
        const id = $(this).data('id');
        showDetailModal(id);
    });
}
