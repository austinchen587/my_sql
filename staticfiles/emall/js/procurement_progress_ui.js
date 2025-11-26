/**
 * 采购进度UI渲染模块
 */
// 渲染供应商分页功能
function renderSuppliersPagination(suppliers) {
    const totalSuppliers = suppliers.length;
    const totalPages = Math.ceil(totalSuppliers / suppliersPerPage);
    const startIndex = (currentSupplierPage - 1) * suppliersPerPage;
    const endIndex = Math.min(startIndex + suppliersPerPage, totalSuppliers);
    const currentSuppliers = suppliers.slice(startIndex, endIndex);
    let paginationHTML = `
    <div class="d-flex justify-content-between align-items-center mb-3">
        <small class="text-muted">显示 ${startIndex + 1}-${endIndex} 共 ${totalSuppliers} 个供应商</small>
        ${renderPaginationControls(totalPages)}
    </div>`;
    if (currentSuppliers.length === 0) {
        paginationHTML += `<div class="text-center text-muted py-5">暂无供应商信息</div>`;
    } else {
        currentSuppliers.forEach((supplier, index) => {
            paginationHTML += renderSupplierCard(supplier, startIndex + index + 1);
        });
    }
    return paginationHTML;
}
// 渲染分页控件
function renderPaginationControls(totalPages) {
    if (totalPages <= 1) return '';
    let paginationHTML = `<nav><ul class="pagination pagination-sm mb-0">`;
    
    if (currentSupplierPage > 1) {
        paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="changeSupplierPage(${currentSupplierPage - 1})">上一页</a></li>`;
    }
    
    for (let i = 1; i <= totalPages; i++) {
        const activeClass = i === currentSupplierPage ? 'active' : '';
        paginationHTML += `<li class="page-item ${activeClass}"><a class="page-link" href="#" onclick="changeSupplierPage(${i})">${i}</a></li>`;
    }
    
    if (currentSupplierPage < totalPages) {
        paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="changeSupplierPage(${currentSupplierPage + 1})">下一页</a></li>`;
    }
    
    paginationHTML += `</ul></nav>`;
    return paginationHTML;
}
// 渲染供应商商品信息
function renderSupplierCommodities(commodities) {
    if (!commodities || commodities.length === 0) {
        return `<div class="text-muted small">暂无商品信息</div>`;
    }
    let commoditiesHTML = `<div class="table-responsive"><table class="table table-sm table-borderless">`;
    commodities.forEach(commodity => {
        commoditiesHTML += `
        <tr>
            <td width="30%">${commodity.name}</td>
            <td width="30%"><small class="text-muted">${commodity.specification || '-'}</small></td>
            <td width="15%" class="text-end">¥${commodity.price}</td>
            <td width="10%" class="text-center">×${commodity.quantity}</td>
            <td width="15%" class="text-end fw-bold">¥${(commodity.price * commodity.quantity).toLocaleString('zh-CN')}</td>
        </tr>`;
    });
    commoditiesHTML += `</table></div>`;
    return commoditiesHTML;
}
// 渲染备注历史
function renderRemarksHistory(remarks) {
    if (!remarks || remarks.length === 0) {
        return '<div class="text-center text-muted py-4">暂无备注记录</div>';
    }
    let remarksHTML = '';
    remarks.forEach(remark => {
        remarksHTML += `
        <div class="card mb-2">
            <div class="card-body py-2">
                <div class="d-flex justify-content-between align-items-start mb-1">
                    <span class="fw-bold text-primary">${remark.created_by}</span>
                    <small class="text-muted">${remark.created_at_display}</small>
                </div>
                <p class="mb-0">${remark.remark_content}</p>
            </div>
        </div>`;
    });
    return remarksHTML;
}
// 初始化标签页
function initTabs() {
    $('#progressTabs button').on('click', function() {
        $('#progressTabs button').removeClass('active');
        $(this).addClass('active');
    });
}

// 渲染采购进度模态框内容
function renderProgressModal(procurementId, data) {
    console.log('接收到的采购数据:', data); // 添加调试日志
    console.log('备注数据详情:', data.remarks_history); // 添加调试日志




    const htmlContent = `
    <div class="modal-header bg-primary text-white sticky-top">
        <h5 class="modal-title">
            <i class="fas fa-tasks me-2"></i>采购进度管理 - ${data.procurement_title || '未知项目'}
            <small class="ms-2 opacity-75">编号: ${data.procurement_number || '-'}</small>
        </h5>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
    </div>
    
    <div class="modal-body p-0" style="max-height: 80vh; overflow-y: auto;">
        <nav>
            <div class="nav nav-tabs bg-light" id="progressTabs" role="tablist">
                <button class="nav-link active" id="overview-tab" data-bs-toggle="tab" data-bs-target="#overview" type="button">
                    <i class="fas fa-chart-bar me-1"></i>概览页面
                </button>
                <button class="nav-link" id="basic-info-tab" data-bs-toggle="tab" data-bs-target="#basic-info" type="button">
                    <i class="fas fa-edit me-1"></i>基本信息管理
                </button>
                <button class="nav-link" id="suppliers-tab" data-bs-toggle="tab" data-bs-target="#suppliers" type="button">
                    <i class="fas fa-truck me-1"></i>供应商管理
                </button>
                <button class="nav-link" id="remarks-tab" data-bs-toggle="tab" data-bs-target="#remarks" type="button">
                    <i class="fas fa-comments me-1"></i>进度备注
                </button>
            </div>
        </nav>
        <div class="tab-content p-4">
            <div class="tab-pane fade show active" id="overview" role="tabpanel">
                ${renderOverviewTab(data)}
            </div>
            <div class="tab-pane fade" id="basic-info" role="tabpanel">
                ${renderBasicInfoTab(data)}
            </div>
            <div class="tab-pane fade" id="suppliers" role="tabpanel">
                ${renderSuppliersTab(data)}
            </div>
            <div class="tab-pane fade" id="remarks" role="tabpanel">
                ${renderRemarksTab(data)}
            </div>
        </div>
    </div>
    
    <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
        <button type="button" class="btn btn-primary" onclick="saveAllData(${procurementId})">
            <i class="fas fa-save me-1"></i>保存所有更改
        </button>
    </div>`;
    $('#progressModalContent').html(htmlContent);
    initTabs();
}

// 渲染概览页面 - 确保数据正确显示
function renderOverviewTab(data) {
    const budget = data.total_budget || 0;
    const biddingStatusMap = {
        'not_started': '未开始',
        'in_progress': '进行中',
        'successful': '竞标成功',
        'failed': '竞标失败',
        'cancelled': '已取消'
    };
    
    return `
    <div class="row">
        <div class="col-md-6">
            <div class="card h-100">
                <div class="card-header bg-light-primary">
                    <h6 class="mb-0"><i class="fas fa-info-circle me-2"></i>基本信息概览</h6>
                </div>
                <div class="card-body">
                    <div class="mb-3">
                        <label class="form-label fw-bold">竞标状态</label>
                        <p class="form-control-plaintext">${biddingStatusMap[data.bidding_status] || data.bidding_status_display || '未知'}</p>
                    </div>
                    
                    <div class="row mb-3">
                        <div class="col-6">
                            <label class="form-label">甲方联系人</label>
                            <p class="form-control-plaintext">${data.client_contact || '未设置'}</p>
                        </div>
                        <div class="col-6">
                            <label class="form-label">甲方联系方式</label>
                            <p class="form-control-plaintext">${data.client_phone || '未设置'}</p>
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label fw-bold">总预算</label>
                        <p class="form-control-plaintext text-success fw-bold">¥${budget.toLocaleString('zh-CN', {minimumFractionDigits: 2})}</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="col-md-6">
            <div class="card h-100">
                <div class="card-header bg-light-success">
                    <h6 class="mb-0"><i class="fas fa-chart-bar me-2"></i>供应商统计</h6>
                </div>
                <div class="card-body">
                    <div class="text-center py-3">
                        <h3 class="text-primary mb-1">${data.suppliers_info?.length || 0}</h3>
                        <small class="text-muted">供应商总数</small>
                    </div>
                    <div class="row text-center">
                        <div class="col-6">
                            <h5 class="text-success mb-1">${(data.suppliers_info?.filter(s => s.is_selected).length || 0)}</h5>
                            <small class="text-muted">已选择</small>
                        </div>
                        <div class="col-6">
                            <h5 class="text-warning mb-1">${(data.suppliers_info?.filter(s => !s.is_selected).length || 0)}</h5>
                            <small class="text-muted">备选</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="mt-4">
        <div class="card">
            <div class="card-header bg-light-warning d-flex justify-content-between align-items-center">
                <h6 class="mb-0"><i class="fas fa-truck me-2"></i>供应商报价概览</h6>
                <span class="badge bg-primary">${data.suppliers_info?.length || 0} 个供应商</span>
            </div>
            <div class="card-body">
                ${renderSuppliersOverview(data.suppliers_info || [], budget)}
            </div>
        </div>
    </div>

    <!-- 在概览页面底部显示备注 -->
    <div class="mt-4">
        <div class="card">
            <div class="card-header bg-light-info d-flex justify-content-between align-items-center">
                <h6 class="mb-0"><i class="fas fa-comments me-2"></i>最新备注</h6>
                <span class="badge bg-primary">${data.remarks_history?.length || 0} 条</span>
            </div>
            <div class="card-body">
                ${renderOverviewRemarks(data.remarks_history || [])}
            </div>
        </div>
    </div>`;
}

// 修复供应商概览表格显示
function renderSuppliersOverview(suppliers, budget) {
    if (!suppliers || suppliers.length === 0) {
        return `<div class="text-center text-muted py-4">暂无供应商信息</div>`;
    }

    let tableHTML = `
    <div class="table-responsive">
        <table class="table table-hover table-sm">
            <thead>
                <tr>
                    <th>供应商名称</th>
                    <th>总报价</th>
                    <th>预计利润</th>
                    <th>利润率</th>
                    <th>状态</th>
                </tr>
            </thead>
            <tbody>`;

    suppliers.forEach(supplier => {
        const totalQuote = supplier.total_quote || 0;
        const profit = supplier.profit || 0;
        const profitRate = budget > 0 ? ((profit / budget) * 100).toFixed(2) : '0.00';
        const profitClass = profit >= 0 ? 'text-success' : 'text-danger';
        const statusBadge = supplier.is_selected ? 
            '<span class="badge bg-success">已选择</span>' : 
            '<span class="badge bg-secondary">备选</span>';

        tableHTML += `
        <tr>
            <td class="fw-bold">${supplier.name || '未知供应商'}</td>
            <td>¥${totalQuote.toLocaleString('zh-CN', {minimumFractionDigits: 2})}</td>
            <td class="${profitClass} fw-bold">¥${profit.toLocaleString('zh-CN', {minimumFractionDigits: 2})}</td>
            <td class="${profitClass}">${profitRate}%</td>
            <td>${statusBadge}</td>
        </tr>`;
    });

    tableHTML += `</tbody></table></div>`;
    return tableHTML;
}


// 渲染基本信息管理页面
function renderBasicInfoTab(data) {
    return `
    <div class="card">
        <div class="card-header bg-light-primary">
            <h6 class="mb-0"><i class="fas fa-edit me-2"></i>编辑基本信息</h6>
        </div>
        <div class="card-body">
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
            
            <div class="mb-3">
                <label class="form-label fw-bold">甲方联系人信息管理</label>
                <div id="clientContactsContainer">
                    ${renderClientContacts(data.client_contacts || [])}
                </div>
                <button type="button" class="btn btn-sm btn-outline-primary mt-2" onclick="addClientContactField()">
                    <i class="fas fa-plus me-1"></i>添加联系人
                </button>
            </div>
        </div>
    </div>`;
}

// 渲染甲方联系人信息
function renderClientContacts(contacts) {
    if (!contacts || contacts.length === 0) {
        return `
        <div class="row mb-2">
            <div class="col-md-6">
                <input type="text" class="form-control" name="client_contact" placeholder="联系人姓名" value="">
            </div>
            <div class="col-md-6">
                <input type="text" class="form-control" name="client_phone" placeholder="联系方式">
            </div>
        </div>`;
    }

    let contactsHTML = '';
    contacts.forEach((contact, index) => {
        contactsHTML += `
        <div class="row mb-2 client-contact-item">
            <div class="col-md-5">
                <input type="text" class="form-control" name="client_contact" placeholder="联系人姓名" value="${contact.name || ''}">
            </div>
            <div class="col-md-5">
                <input type="text" class="form-control" name="client_phone" placeholder="联系方式" value="${contact.phone || ''}">
            </div>
            <div class="col-md-2">
                <button type="button" class="btn btn-sm btn-outline-danger w-100" onclick="removeClientContact(this)">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>`;
    });
    return contactsHTML;
}

// 渲染供应商概览表格 - 修复显示问题
function renderSuppliersOverview(suppliers, budget) {
    if (!suppliers || suppliers.length === 0) {
        return `<div class="text-center text-muted py-4">暂无供应商信息</div>`;
    }

    let tableHTML = `
    <div class="table-responsive">
        <table class="table table-hover table-sm">
            <thead>
                <tr>
                    <th>供应商名称</th>
                    <th>总报价</th>
                    <th>预计利润</th>
                    <th>利润率</th>
                    <th>状态</th>
                </tr>
            </thead>
            <tbody>`;

    suppliers.forEach(supplier => {
        const totalQuote = supplier.total_quote || 0;
        const profit = supplier.profit || 0;
        const profitRate = budget > 0 ? ((profit / budget) * 100).toFixed(2) : '0.00';
        const profitClass = profit >= 0 ? 'text-success' : 'text-danger';
        const statusBadge = supplier.is_selected ? 
            '<span class="badge bg-success">已选择</span>' : 
            '<span class="badge bg-secondary">备选</span>';

        tableHTML += `
        <tr>
            <td class="fw-bold">${supplier.name || '未知供应商'}</td>
            <td>¥${totalQuote.toLocaleString('zh-CN', {minimumFractionDigits: 2})}</td>
            <td class="${profitClass} fw-bold">¥${profit.toLocaleString('zh-CN', {minimumFractionDigits: 2})}</td>
            <td class="${profitClass}">${profitRate}%</td>
            <td>${statusBadge}</td>
        </tr>`;
    });

    tableHTML += `</tbody></table></div>`;
    return tableHTML;
}

// 在概览页面显示最新备注
function renderOverviewRemarks(remarks) {
    if (!remarks || remarks.length === 0) {
        return '<div class="text-center text-muted py-3">暂无备注记录</div>';
    }

    // 只显示最新的3条备注
    const recentRemarks = remarks.slice(0, 3);
    let remarksHTML = '';
    
    recentRemarks.forEach(remark => {
        remarksHTML += `
        <div class="mb-2 p-2 border rounded">
            <div class="d-flex justify-content-between align-items-start mb-1">
                <span class="fw-bold text-primary small">${remark.created_by}</span>
                <small class="text-muted">${remark.created_at_display}</small>
            </div>
            <p class="mb-0 small">${remark.remark_content}</p>
        </div>`;
    });
    
    if (remarks.length > 3) {
        remarksHTML += `<div class="text-center mt-2">
            <small class="text-muted">还有 ${remarks.length - 3} 条备注，请在备注页面查看</small>
        </div>`;
    }
    
    return remarksHTML;
}

// 供应商管理页面保持不变
function renderSuppliersTab(data) {
    return `
    <div class="d-flex justify-content-between align-items-center mb-3">
        <h5 class="mb-0">供应商管理</h5>
        <button type="button" class="btn btn-primary btn-sm" onclick="showAddSupplierModal()">
            <i class="fas fa-plus me-1"></i>添加供应商
        </button>
    </div>
    
    <div id="suppliersContainer">
        ${renderSuppliersPagination(data.suppliers_info || [])}
    </div>`;
}

// 渲染供应商卡片 - 改为只读显示已有信息
function renderSupplierCard(supplier, index) {
    return `
    <div class="card mb-3">
        <div class="card-header d-flex justify-content-between align-items-center">
            <div class="d-flex align-items-center">
                <input type="checkbox" class="form-check-input supplier-selection-checkbox me-2" 
                       data-supplier-id="${supplier.id}" 
                       ${supplier.is_selected ? 'checked' : ''}>
                <h6 class="mb-0">
                    <span class="badge bg-secondary me-2">${index}</span>
                    ${supplier.name || '未知供应商'}
                    ${supplier.is_selected ? '<span class="badge bg-success ms-2">已选择</span>' : ''}
                </h6>
            </div>
            <div>
            <button class="btn btn-sm btn-outline-primary me-1" onclick="editSupplier(${supplier.id})">
                    <i class="fas fa-edit"></i> 编辑
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteSupplier(${supplier.id})">
                    <i class="fas fa-trash"></i> 删除
                </button>
            </div>
        </div>
        <div class="card-body">
            <div class="row">
                <div class="col-md-6">
                    <small class="text-muted">渠道:</small>
                    <p class="mb-2">${supplier.source || '-'}</p>
                    <small class="text-muted">联系方式:</small>
                    <p class="mb-0">${supplier.contact || '-'}</p>
                </div>
                <div class="col-md-6">
                    <small class="text-muted">店铺名称:</small>
                    <p class="mb-2">${supplier.store_name || '-'}</p>
                    <small class="text-muted">总报价:</small>
                    <p class="mb-0 fw-bold text-primary">¥${(supplier.total_quote || 0).toLocaleString('zh-CN', {minimumFractionDigits: 2})}</p>
                </div>
            </div>
            
            <div class="mt-3">
                <h6 class="border-bottom pb-1">商品信息</h6>
                ${renderSupplierCommodities(supplier.commodities || [])}
            </div>
        </div>
    </div>`;
}

// 在渲染备注页面的函数中，确保ID正确
function renderRemarksTab(data) {
    return `
    <div>
        <div class="mb-3">
            <label class="form-label fw-bold">新增备注</label>
            <textarea class="form-control" id="newRemark" rows="3" placeholder="请输入备注内容..."></textarea>
        </div>
        <div class="row mb-3">
            <div class="col-md-6">
                <input type="text" class="form-control" id="remarkCreator" placeholder="创建人" value="系统管理员">
            </div>
            <div class="col-md-6">
                <button type="button" class="btn btn-success w-100" onclick="addNewRemark()">
                    <i class="fas fa-plus me-1"></i>添加备注
                </button>
            </div>
        </div>
        
        <div class="mt-4">
            <h6 class="border-bottom pb-2">备注历史</h6>
            <div id="remarksHistory" style="max-height: 300px; overflow-y: auto;">
                ${renderRemarksHistory(data.remarks_history || [])}
            </div>
        </div>
    </div>`;
}

// 添加新的工具函数到 procurement_progress_utils.js
function addClientContactField() {
    const contactHTML = `
    <div class="row mb-2 client-contact-item">
        <div class="col-md-5">
            <input type="text" class="form-control" name="client_contact" placeholder="联系人姓名">
        </div>
        <div class="col-md-5">
            <input type="text" class="form-control" name="client_phone" placeholder="联系方式">
        </div>
        <div class="col-md-2">
            <button type="button" class="btn btn-sm btn-outline-danger w-100" onclick="removeClientContact(this)">
                <i class="fas fa-times"></i>
            </button>
        </div>
    </div>`;
    $('#clientContactsContainer').append(contactHTML);
}

function removeClientContact(button) {
    $(button).closest('.client-contact-item').remove();
}

// 修改保存函数以支持联系人管理
function saveAllData(procurementId) {
    const formData = {
        bidding_status: $('#progressModal select[name="bidding_status"]').val(),
        client_contact: $('#progressModal input[name="client_contact"]').val() || '',
        client_phone: $('#progressModal input[name="client_phone"]').val() || '',
        supplier_selection: [],
        new_remark: {}
    };
    
    $('.supplier-selection-checkbox').each(function() {
        formData.supplier_selection.push({
            supplier_id: $(this).data('supplier-id'),
            is_selected: $(this).is(':checked')
        });
    });
    
    // 收集新备注（只有在有内容时才提交）
    const remarkContent = $('#newRemark').val().trim();
    const remarkCreator = $('#remarkCreator').val().trim();
    if (remarkContent && remarkCreator) {
        formData.new_remark = {
            remark_content: remarkContent,  // 修改这里：content -> remark_content
            created_by: remarkCreator
        };
    }
    
    // 显示加载状态
    const saveBtn = $('#progressModal').find('.btn-primary');
    const originalText = saveBtn.html();
    saveBtn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-1"></i>保存中...');
    
    $.ajax({
        url: `/emall/purchasing/procurement/${procurementId}/update/`,
        method: 'POST',
        data: JSON.stringify(formData),
        contentType: 'application/json',
        headers: {
            'X-CSRFToken': getCSRFToken()
        },
        success: function(response) {
            showToast('采购信息保存成功', 'success');
            // 清空备注输入框
            $('#newRemark').val('');
            // 刷新数据
            loadProgressData(procurementId);
        },
        error: function(xhr) {
            const errorMsg = xhr.responseJSON?.error || '保存失败，请稍后重试';
            showToast('保存失败: ' + errorMsg, 'error');
        },
        complete: function() {
            saveBtn.prop('disabled', false).html(originalText);
        }
    });
}
