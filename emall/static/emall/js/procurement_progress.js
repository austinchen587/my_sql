/**
 * 采购进度管理模块 - 全新设计
 */

// 绑定进度事件
function bindProgressEvents() {
    $('#procurementTable').off('click', '.btn-progress').on('click', '.btn-progress', function() {
        const procurementId = $(this).data('id');
        showProgressModal(procurementId);
    });
}

// 显示采购进度弹窗
function showProgressModal(procurementId) {
    if (!$('#progressModal').length) {
        createProgressModal();
    }
    
    const modal = new bootstrap.Modal('#progressModal');
    
    // 显示加载状态
    $('#progressModalContent').html(`
        <div class="modal-header bg-primary text-white">
            <h5 class="modal-title">
                <i class="fas fa-spinner fa-spin me-2"></i>加载采购进度信息...
            </h5>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body text-center py-5">
            <div class="spinner-border text-primary mb-3"></div>
            <p>正在加载数据...</p>
        </div>
    `);
    
    modal.show();
    loadProgressData(procurementId);
}

// 创建采购进度弹窗
function createProgressModal() {
    const modalHTML = `
    <div class="modal fade" id="progressModal" tabindex="-1" aria-labelledby="progressModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-xl">
            <div class="modal-content" id="progressModalContent">
                <!-- 内容将由JavaScript动态加载 -->
            </div>
        </div>
    </div>`;
    $('body').append(modalHTML);
}

// 加载采购进度数据
function loadProgressData(procurementId) {
    $.ajax({
        url: `/emall/purchasing/procurement/${procurementId}/progress/`,  // 注意这里是单数 procUrement
        type: 'GET',
        success: function(data) {
            renderProgressModal(procurementId, data);
        },
        error: function(xhr, status, error) {
            console.error('加载采购进度失败:', {
                status: status,
                error: error,
                responseText: xhr.responseText
            });
            $('#progressModalContent').html(`
                <div class="modal-header bg-danger text-white">
                    <h5 class="modal-title">错误</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="alert alert-danger">
                        <h6><i class="fas fa-exclamation-triangle me-2"></i>加载失败 (${xhr.status})</h6>
                        <p class="mb-0">${xhr.responseJSON?.error || '无法加载采购进度信息'}</p>
                        <small>URL: /emall/purchasing/procurement/${procurementId}/progress/</small>
                    </div>
                    <div class="text-center">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                    </div>
                </div>
            `);
        }
    });
}

// 渲染采购进度模态框内容
function renderProgressModal(procurementId, data) {
    const htmlContent = `
    <div class="modal-header bg-primary text-white">
        <h5 class="modal-title">
            <i class="fas fa-tasks me-2"></i>采购进度管理 - ${data.procurement_title || '未知项目'}
        </h5>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
    </div>
    
    <div class="modal-body p-0">
        <div class="row g-0">
            <!-- 左侧：基本信息编辑区域 -->
            <div class="col-md-6 border-end">
                <div class="p-3">
                    <h6 class="border-bottom pb-2 mb-3">
                        <i class="fas fa-edit me-2"></i>基本信息编辑
                    </h6>
                    
                    <form id="progressForm">
                        <!-- 竞标状态 -->
                        <div class="mb-3">
                            <label class="form-label fw-bold">竞标状态</label>
                            <select class="form-select" name="bidding_status">
                                <option value="not_started" ${data.bidding_status === 'not_started' ? 'selected' : ''}>未开始</option>
                                <option value="in_progress" ${data.bidding_status === 'in_progress' ? 'selected' : ''}>进行中</option>
                                <option value="successful" ${data.bidding_status === 'successful' ? 'selected' : ''}>竞标成功</option>
                                <option value="failed" ${data.bidding_status === 'failed' ? 'selected' : ''}>竞标失败</option>
                                <option value="cancelled" ${data.bidding_status === 'cancelled' ? 'selected' : ''}>已取消</option>
                            </select>
                        </div>

                        <!-- 甲方信息 -->
                        <div class="mb-3">
                            <label class="form-label fw-bold">甲方信息</label>
                            <div class="row g-2">
                                <div class="col-6">
                                    <input type="text" class="form-control form-control-sm" name="client_contact" 
                                           value="${data.client_contact || ''}" placeholder="联系人">
                                </div>
                                <div class="col-6">
                                    <input type="text" class="form-control form-control-sm" name="client_phone" 
                                           value="${data.client_phone || ''}" placeholder="联系方式">
                                </div>
                            </div>
                        </div>

                        <!-- 供应商信息 -->
                        <div class="mb-3">
                            <label class="form-label fw-bold">供应商信息</label>
                            <div class="row g-2 mb-2">
                                <div class="col-6">
                                    <select class="form-select form-select-sm" name="supplier_source">
                                        <option value="">渠道来源</option>
                                        <option value="平台推荐" ${data.supplier_source === '平台推荐' ? 'selected' : ''}>平台推荐</option>
                                        <option value="自主开发" ${data.supplier_source === '自主开发' ? 'selected' : ''}>自主开发</option>
                                        <option value="客户推荐" ${data.supplier_source === '客户推荐' ? 'selected' : ''}>客户推荐</option>
                                        <option value="其他" ${data.supplier_source === '其他' ? 'selected' : ''}>其他</option>
                                    </select>
                                </div>
                                <div class="col-6">
                                    <input type="text" class="form-control form-control-sm" name="supplier_store" 
                                           value="${data.supplier_store || ''}" placeholder="店铺名称">
                                </div>
                            </div>
                            <input type="text" class="form-control form-control-sm" name="supplier_contact" 
                                   value="${data.supplier_contact || ''}" placeholder="供应商联系方式">
                        </div>

                        <!-- 成本信息 -->
                        <div class="mb-3">
                            <label class="form-label fw-bold">成本信息</label>
                            <input type="number" class="form-control form-control-sm" name="cost" 
                                   value="${data.cost || ''}" placeholder="成本金额" step="0.01" min="0">
                        </div>
                    </form>

                    <!-- 商品信息管理 -->
                    <div class="mb-3">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <label class="form-label fw-bold mb-0">商品信息</label>
                            <button type="button" class="btn btn-sm btn-outline-primary" onclick="addCommodityRow()">
                                <i class="fas fa-plus me-1"></i>添加商品
                            </button>
                        </div>
                        <div id="commodityTable" class="table-responsive" style="max-height: 200px;">
                            ${renderCommodityTable(data.commodities_info || [])}
                        </div>
                    </div>
                </div>
            </div>

            <!-- 右侧：信息展示和备注区域 -->
            <div class="col-md-6">
                <div class="p-3">
                    <!-- 信息展示 -->
                    <div class="mb-4">
                        <h6 class="border-bottom pb-2 mb-3">
                            <i class="fas fa-info-circle me-2"></i>当前信息概览
                        </h6>
                        ${renderInfoOverview(data)}
                    </div>

                    <!-- 备注管理 -->
                    <div>
                        <h6 class="border-bottom pb-2 mb-3">
                            <i class="fas fa-comments me-2"></i>进度备注
                        </h6>
                        
                        <!-- 新增备注 -->
                        <div class="mb-3">
                            <textarea class="form-control form-control-sm" id="newRemark" 
                                      placeholder="请输入新的备注内容..." rows="2"></textarea>
                            <div class="mt-2 d-flex justify-content-between">
                                <input type="text" class="form-control form-control-sm w-50" 
                                       id="remarkCreator" placeholder="创建人" value="系统管理员">
                                <button type="button" class="btn btn-sm btn-success" onclick="addNewRemark(${procurementId})">
                                    <i class="fas fa-plus me-1"></i>添加备注
                                </button>
                            </div>
                        </div>

                        <!-- 备注历史 -->
                        <div class="remark-history" style="max-height: 250px; overflow-y: auto;">
                            ${renderRemarkHistory(data.remarks_history || [])}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
        <button type="button" class="btn btn-primary" onclick="saveProgressData(${procurementId})">
            <i class="fas fa-save me-1"></i>保存所有更改
        </button>
    </div>`;

    $('#progressModalContent').html(htmlContent);
}

// 渲染商品信息表格
function renderCommodityTable(commodities) {
    if (!commodities || commodities.length === 0) {
        return `<div class="text-muted text-center py-3">暂无商品信息</div>`;
    }

    let tableHTML = `
    <table class="table table-sm table-hover">
        <thead>
            <tr>
                <th>商品名</th>
                <th>规格</th>
                <th>价格</th>
                <th>数量</th>
                <th>操作</th>
            </tr>
        </thead>
        <tbody>`;

    commodities.forEach((commodity, index) => {
        tableHTML += `
        <tr>
            <td><input type="text" class="form-control form-control-sm" name="commodity_names" value="${commodity.name || ''}"></td>
            <td><input type="text" class="form-control form-control-sm" name="product_specifications" value="${commodity.specification || ''}"></td>
            <td><input type="number" class="form-control form-control-sm" name="prices" value="${commodity.price || ''}" step="0.01"></td>
            <td><input type="number" class="form-control form-control-sm" name="quantities" value="${commodity.quantity || ''}"></td>
            <td><button type="button" class="btn btn-sm btn-outline-danger" onclick="removeCommodityRow(this)"><i class="fas fa-trash"></i></button></td>
        </tr>`;
    });

    tableHTML += `</tbody></table>`;
    return tableHTML;
}

// 渲染信息概览
function renderInfoOverview(data) {
    return `
    <div class="row g-2 small">
        <div class="col-6">
            <span class="text-muted">竞标状态:</span>
            <br><span class="fw-bold">${data.bidding_status_display || '未开始'}</span>
        </div>
        <div class="col-6">
            <span class="text-muted">商品数量:</span>
            <br><span class="fw-bold">${data.commodities_count || 0}个</span>
        </div>
        <div class="col-6">
            <span class="text-muted">总金额:</span>
            <br><span class="fw-bold text-success">¥${data.total_amount || '0.00'}</span>
        </div>
        <div class="col-6">
            <span class="text-muted">更新时间:</span>
            <br><span class="fw-bold">${data.updated_at ? new Date(data.updated_at).toLocaleString() : '未知'}</span>
        </div>
    </div>`;
}

// 渲染备注历史
function renderRemarkHistory(remarks) {
    if (!remarks || remarks.length === 0) {
        return `<div class="text-muted text-center py-3">暂无备注记录</div>`;
    }

    let remarksHTML = '';
    remarks.forEach(remark => {
        remarksHTML += `
        <div class="card mb-2">
            <div class="card-body py-2">
                <div class="d-flex justify-content-between align-items-start">
                    <small class="text-primary fw-bold">${remark.created_by}</small>
                    <small class="text-muted">${remark.created_at_display}</small>
                </div>
                <p class="mb-0 small">${remark.remark_content}</p>
            </div>
        </div>`;
    });

    return remarksHTML;
}

// 添加商品行
function addCommodityRow() {
    const tbody = $('#commodityTable tbody');
    if (!tbody.length) {
        $('#commodityTable').html(`
            <table class="table table-sm table-hover">
                <thead>
                    <tr>
                        <th>商品名</th>
                        <th>规格</th>
                        <th>价格</th>
                        <th>数量</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        `);
    }
    
    $('#commodityTable tbody').append(`
        <tr>
            <td><input type="text" class="form-control form-control-sm" name="commodity_names" placeholder="商品名"></td>
            <td><input type="text" class="form-control form-control-sm" name="product_specifications" placeholder="规格"></td>
            <td><input type="number" class="form-control form-control-sm" name="prices" placeholder="价格" step="0.01"></td>
            <td><input type="number" class="form-control form-control-sm" name="quantities" placeholder="数量"></td>
            <td><button type="button" class="btn btn-sm btn-outline-danger" onclick="removeCommodityRow(this)"><i class="fas fa-trash"></i></button></td>
        </tr>
    `);
}

// 移除商品行
function removeCommodityRow(button) {
    $(button).closest('tr').remove();
}

// 添加新备注
function addNewRemark(procurementId) {
    const content = $('#newRemark').val().trim();
    const creator = $('#remarkCreator').val().trim();
    
    if (!content) {
        showToast('请输入备注内容', 'warning');
        return;
    }
    
    if (!creator) {
        showToast('请输入创建人', 'warning');
        return;
    }
    
    // 这里可以立即在界面显示新备注，然后统一保存
    const newRemark = {
        created_by: creator,
        created_at_display: '刚刚',
        remark_content: content
    };
    
    // 添加到历史记录
    const historyContainer = $('.remark-history');
    const remarkHTML = `
    <div class="card mb-2 border-success">
        <div class="card-body py-2">
            <div class="d-flex justify-content-between align-items-start">
                <small class="text-success fw-bold">${newRemark.created_by}</small>
                <small class="text-muted">${newRemark.created_at_display}</small>
            </div>
            <p class="mb-0 small">${newRemark.remark_content}</p>
        </div>
    </div>`;
    
    historyContainer.prepend(remarkHTML);
    
    // 清空输入框
    $('#newRemark').val('');
    
    showToast('备注已添加（待保存）', 'success');
}

// 保存所有数据
// 保存所有数据
function saveProgressData(procurementId) {
    const formData = collectFormData();
    
    $.ajax({
        url: `/emall/purchasing/procurement/${procurementId}/progress/`,  // 修正为单数
        type: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        contentType: 'application/json',
        data: JSON.stringify(formData),
        beforeSend: function() {
            $('#progressModal .btn-primary').prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-1"></i>保存中...');
        },
        success: function(response) {
            if (response.success) {
                showToast('采购进度保存成功', 'success');
                $('#progressModal').modal('hide');
                if (typeof procurementTable !== 'undefined') {
                    procurementTable.ajax.reload();
                }
            } else {
                showToast(response.errors || '保存失败', 'error');
            }
        },
        error: function(xhr, status, error) {
            console.error('保存进度失败:', {status, error, responseText: xhr.responseText});
            showToast('保存失败: ' + (xhr.responseJSON?.error || '网络错误'), 'error');
        },
        complete: function() {
            $('#progressModal .btn-primary').prop('disabled', false).html('<i class="fas fa-save me-1"></i>保存所有更改');
        }
    });
}

// 收集表单数据
function collectFormData() {
    const formData = {
        // 基本表单数据
        bidding_status: $('select[name="bidding_status"]').val(),
        client_contact: $('input[name="client_contact"]').val(),
        client_phone: $('input[name="client_phone"]').val(),
        supplier_source: $('select[name="supplier_source"]').val(),
        supplier_store: $('input[name="supplier_store"]').val(),
        supplier_contact: $('input[name="supplier_contact"]').val(),
        cost: $('input[name="cost"]').val(),
        
        // 商品数据
        commodity_names: [],
        product_specifications: [],
        prices: [],
        quantities: []
    };
    
    // 收集商品信息
    $('input[name="commodity_names"]').each(function() {
        formData.commodity_names.push($(this).val());
    });
    $('input[name="product_specifications"]').each(function() {
        formData.product_specifications.push($(this).val());
    });
    $('input[name="prices"]').each(function() {
        formData.prices.push($(this).val() ? parseFloat($(this).val()) : null);
    });
    $('input[name="quantities"]').each(function() {
        formData.quantities.push($(this).val() ? parseInt($(this).val()) : null);
    });
    
    // 处理新备注
    const newRemarkContent = $('#newRemark').val().trim();
    const remarkCreator = $('#remarkCreator').val().trim();
    if (newRemarkContent && remarkCreator) {
        formData.new_remark = {
            content: newRemarkContent,
            created_by: remarkCreator
        };
    }
    
    return formData;
}
