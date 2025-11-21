// procurement_modal.js
(function() {
    'use strict';

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

    // 安全数组处理
    function safeArray(arr) {
        return Array.isArray(arr) ? arr : [];
    }

    // 金额转换函数（确保与utils一致）
    function convertPriceToNumber(priceStr) {
        if (!priceStr || priceStr === '-') return null;
        
        try {
            const cleanStr = priceStr.toString().replace(/[\s,]/g, '');
            
            if (cleanStr.includes('万元') && !cleanStr.includes('元万元')) {
                const numberMatch = cleanStr.match(/(\d+\.?\d*)\s*万元/);
                if (numberMatch) {
                    const numberValue = parseFloat(numberMatch[1]);
                    return numberValue * 10000;
                }
            }
            
            if (cleanStr.includes('元万元')) {
                const numberMatch = cleanStr.match(/(\d+\.?\d*)/);
                if (numberMatch) {
                    return parseFloat(numberMatch[1]);
                }
            }
            
            if (cleanStr.includes('元') && !cleanStr.includes('万元')) {
                const numberMatch = cleanStr.match(/(\d+\.?\d*)\s*元/);
                if (numberMatch) {
                    return parseFloat(numberMatch[1]);
                }
            }
            
            const numberValue = parseFloat(cleanStr);
            if (!isNaN(numberValue)) {
                return numberValue;
            }
        } catch (e) {
            console.warn('金额转换失败:', priceStr, e);
        }
        
        return null;
    }

    // 格式化日期显示
    function formatDate(dateString, format = 'full') {
        if (!dateString) return '-';
        try {
            const date = new Date(dateString);
            if (format === 'short') {
                return date.toLocaleDateString('zh-CN');
            }
            return date.toLocaleString('zh-CN');
        } catch (e) {
            return dateString;
        }
    }

    // 渲染商品信息表格
    function renderSectionAsTable(title, dataArrays, columns) {
        const arrays = dataArrays.map(arr => safeArray(arr));
        
        // 检查是否有数据
        const hasData = arrays.some(arr => arr.length > 0);
        if (!hasData) return '';
        
        // 获取最大行数
        const maxRows = Math.max(...arrays.map(arr => arr.length));
        if (maxRows === 0) return '';
        
        // 生成表格行
        let tableRows = '';
        for (let i = 0; i < maxRows; i++) {
            const cells = arrays.map(arr => {
                const cellValue = arr[i] || '-';
                // 对长内容进行截断处理
                if (cellValue.length > 100) {
                    return `<span title="${cellValue.replace(/"/g, '&quot;')}">${cellValue.substring(0, 100)}...</span>`;
                }
                return cellValue;
            }).join('</td><td>');
            tableRows += `<tr><td>${cells}</td></tr>`;
        }
        
        // 生成表头
        const tableHeaders = columns.map(col => `<th class="bg-light-blue text-dark">${col}</th>`).join('');
        
        return `
            <div class="mb-4">
                <h6 class="section-title bg-primary text-white px-3 py-2 rounded-top mb-0">
                    <i class="fas fa-table me-2"></i>${title}
                </h6>
                <div class="table-responsive border">
                    <table class="table table-sm table-hover mb-0">
                        <thead>
                            <tr>${tableHeaders}</tr>
                        </thead>
                        <tbody>
                            ${tableRows}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    // 渲染详情内容
    function renderDetailContent(data) {
        // 转换预算控制金额为数字格式
        const priceControlDisplay = (function() {
            const numericValue = convertPriceToNumber(data.total_price_control);
            return numericValue !== null ? '¥' + numericValue.toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : (data.total_price_control || '-');
        })();
        
        // 检查项目是否已过期
        const isExpired = isDateTimeBeforeNow(data.quote_end_time);
        const expiredBadge = isExpired ? '<span class="badge bg-warning text-dark ms-2"><i class="fas fa-exclamation-triangle me-1"></i>已过期</span>' : '';
        
        const htmlContent = `
            <div class="modal-header bg-gradient-primary text-white">
                <h5 class="modal-title mb-0">
                    <i class="fas fa-shopping-cart me-2"></i>
                    ${data.project_title || '采购项目详情'}
                    ${expiredBadge}
                </h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body custom-scrollbar" style="max-height: 75vh; overflow-y: auto;">
                <!-- 基本信息卡片 -->
                <div class="card mb-4 shadow-sm">
                    <div class="card-header bg-light-blue text-dark">
                        <h6 class="mb-0"><i class="fas fa-info-circle me-2"></i>基本信息</h6>
                    </div>
                    <div class="card-body p-3">
                        <div class="row">
                            <div class="col-md-6">
                                <table class="table table-sm table-borderless mb-0">
                                    <tbody>
                                        <tr><th class="w-35 text-muted">采购单位</th><td class="fw-bold">${data.purchasing_unit || '-'}</td></tr>
                                        <tr><th class="text-muted">项目编号</th><td class="font-monospace">${data.project_number || '-'}</td></tr>
                                    </tbody>
                                </table>
                            </div>
                            <div class="col-md-6">
                                <table class="table table-sm table-borderless mb-0">
                                    <tbody>
                                        <tr><th class="w-35 text-muted">预算控制</th><td class="fw-bold text-success">${priceControlDisplay}</td></tr>
                                        <tr><th class="text-muted">地区</th><td><span class="badge bg-secondary">${data.region || '-'}</span></td></tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- 时间信息卡片 -->
                <div class="card mb-4 shadow-sm">
                    <div class="card-header bg-light-green text-dark">
                        <h6 class="mb-0"><i class="fas fa-clock me-2"></i>时间信息</h6>
                    </div>
                    <div class="card-body p-3">
                        <div class="row">
                            <div class="col-md-4 text-center">
                                <div class="time-block ${isDateTimeBeforeNow(data.publish_date) ? 'text-success' : 'text-muted'}">
                                    <div class="time-icon"><i class="fas fa-calendar-alt"></i></div>
                                    <div class="time-label small">发布日期</div>
                                    <div class="time-value fw-bold">${formatDate(data.publish_date, 'short')}</div>
                                </div>
                            </div>
                            <div class="col-md-4 text-center">
                                <div class="time-block ${isDateTimeBeforeNow(data.quote_start_time) ? 'text-primary' : 'text-muted'}">
                                    <div class="time-icon"><i class="fas fa-play-circle"></i></div>
                                    <div class="time-label small">报价开始</div>
                                    <div class="time-value fw-bold">${formatDate(data.quote_start_time, 'short')}</div>
                                </div>
                            </div>
                            <div class="col-md-4 text-center">
                                <div class="time-block ${isExpired ? 'text-danger' : 'text-warning'}">
                                    <div class="time-icon"><i class="fas fa-stop-circle"></i></div>
                                    <div class="time-label small">报价截止</div>
                                    <div class="time-value fw-bold">${formatDate(data.quote_end_time, 'short')}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- 商品信息表格 -->
                ${renderSectionAsTable('商品信息', 
                    [safeArray(data.commodity_names), safeArray(data.parameter_requirements), safeArray(data.purchase_quantities), safeArray(data.control_amounts), safeArray(data.suggested_brands)],
                    ['商品名称', '参数要求', '购买数量', '控制金额(元)', '建议品牌']
                )}
                
                <!-- 商务要求表格 -->
                ${renderSectionAsTable('商务要求', 
                    data.business_items && data.business_items.length > 0 ? 
                        [safeArray(data.business_items), safeArray(data.business_requirements)] : 
                        [Array.from({length: Math.max(safeArray(data.business_requirements).length, 1)}, (_, i) => i + 1), safeArray(data.business_requirements)],
                    ['商务项目', '商务要求']
                )}
                
                <!-- 下载文件 -->
                ${renderSection('下载文件', safeArray(data.download_files))}
                
                <!-- 操作按钮 -->
                <div class="text-center mt-4 pt-3 border-top">
                    <a href="${data.url || '#'}" target="_blank" class="btn btn-primary btn-lg px-4">
                        <i class="fas fa-external-link-alt me-2"></i>查看原链接
                    </a>
                    <button type="button" class="btn btn-outline-secondary btn-lg px-4 ms-2" data-bs-dismiss="modal">
                        <i class="fas fa-times me-2"></i>关闭
                    </button>
                </div>
            </div>
        `;
        
        $('#detailModalContent').html(htmlContent);
    }

    // 渲染文件下载部分
    function renderSection(title, items) {
        if (!items || items.length === 0) return '';
        
        const itemsHtml = items.map((item, index) => {
            let displayItem = item || '-';
            let linkHtml = displayItem;
            
            // 如果是URL链接，转换为可点击链接
            if (typeof item === 'string' && item.startsWith('http')) {
                const fileName = item.split('/').pop() || `文件${index + 1}`;
                linkHtml = `<a href="${item}" target="_blank" class="text-decoration-none">
                    <i class="fas fa-download me-2 text-primary"></i>${fileName}
                </a>`;
            } else if (typeof item === 'object' && item.url) {
                linkHtml = `<a href="${item.url}" target="_blank" class="text-decoration-none">
                    <i class="fas fa-download me-2 text-primary"></i>${item.name || `文件${index + 1}`}
                </a>`;
            }
            
            return `<li class="list-group-item d-flex justify-content-between align-items-center">
                <span>${linkHtml}</span>
                <button class="btn btn-sm btn-outline-primary copy-btn" data-text="${displayItem}">
                    <i class="fas fa-copy"></i>
                </button>
            </li>`;
        }).join('');
        
        return `
            <div class="mb-4">
                <h6 class="section-title bg-info text-white px-3 py-2 rounded-top mb-0">
                    <i class="fas fa-download me-2"></i>${title}
                </h6>
                <ul class="list-group list-group-flush border">
                    ${itemsHtml}
                </ul>
            </div>
        `;
    }

    // 显示详情弹窗函数
    window.showDetailModal = function(id) {
        const modalEl = document.getElementById('detailModal');
        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        
        console.log('正在请求详情数据，ID:', id);
        
        // 先显示加载状态
        $('#detailModalContent').html(`
            <div class="modal-header bg-gradient-primary text-white">
                <h5 class="modal-title mb-0">
                    <i class="fas fa-spinner fa-spin me-2"></i>加载中...
                </h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body text-center py-5">
                <div class="spinner-border text-primary mb-3" style="width: 3rem; height: 3rem;"></div>
                <h5 class="text-muted">加载项目详情...</h5>
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
                    initCopyButtons();
                } catch (error) {
                    console.error('渲染详情失败:', error);
                    $('#detailModalContent').html(`
                        <div class="modal-header bg-danger text-white">
                            <h5 class="modal-title mb-0"><i class="fas fa-exclamation-triangle me-2"></i>错误</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="alert alert-danger">
                                <h5><i class="fas fa-times-circle me-2"></i>渲染失败</h5>
                                <p class="mb-0">${error.message || '渲染详情内容时出错'}</p>
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
                    <div class="modal-header bg-danger text-white">
                        <h5 class="modal-title mb-0"><i class="fas fa-exclamation-triangle me-2"></i>错误</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="alert alert-danger">
                            <h5><i class="fas fa-times-circle me-2"></i>加载失败</h5>
                            <p class="mb-0">${xhr.responseJSON?.detail || '无法加载项目详情，请稍后重试'}</p>
                        </div>
                    </div>
                `);
            }
        });
    };

    // 复制按钮初始化
    function initCopyButtons() {
        $(document).on('click', '.copy-btn', function() {
            const text = $(this).data('text');
            navigator.clipboard.writeText(text).then(() => {
                const originalHtml = $(this).html();
                $(this).html('<i class="fas fa-check"></i>');
                $(this).removeClass('btn-outline-primary').addClass('btn-success');
                
                setTimeout(() => {
                    $(this).html(originalHtml);
                    $(this).removeClass('btn-success').addClass('btn-outline-primary');
                }, 2000);
            });
        });
    }

    // 添加CSS样式
    function addModalStyles() {
        if (!$('#modal-styles').length) {
            $('head').append(`
                <style id="modal-styles">
                    .bg-gradient-primary {
                        background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
                    }
                    .bg-light-blue {
                        background-color: #e3f2fd !important;
                    }
                    .bg-light-green {
                        background-color: #e8f5e8 !important;
                    }
                    .section-title {
                        font-weight: 600;
                        font-size: 0.95rem;
                    }
                    .time-block {
                        padding: 10px;
                        border-radius: 8px;
                        transition: all 0.3s ease;
                    }
                    .time-block:hover {
                        background-color: #f8f9fa;
                        transform: translateY(-2px);
                    }
                    .time-icon {
                        font-size: 1.5rem;
                        margin-bottom: 5px;
                    }
                    .time-label {
                        color: #6c757d;
                        margin-bottom: 3px;
                    }
                    .time-value {
                        font-size: 0.9rem;
                    }
                    .custom-scrollbar::-webkit-scrollbar {
                        width: 8px;
                    }
                    .custom-scrollbar::-webkit-scrollbar-track {
                        background: #f1f1f1;
                        border-radius: 4px;
                    }
                    .custom-scrollbar::-webkit-scrollbar-thumb {
                        background: #c1c1c1;
                        border-radius: 4px;
                    }
                    .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                        background: #a8a8a8;
                    }
                    .table th {
                        font-weight: 600;
                        border-bottom: 2px solid #dee2e6;
                    }
                    .card {
                        border: none;
                        border-radius: 10px;
                    }
                    .card-header {
                        border-radius: 10px 10px 0 0 !important;
                        border: none;
                        font-weight: 600;
                    }
                </style>
            `);
        }
    }

    // 初始化
    $(document).ready(function() {
        addModalStyles();
    });
})();
