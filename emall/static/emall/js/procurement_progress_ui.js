/**
 * 采购进度UI渲染模块
 */

// 渲染采购进度模态框内容
function renderProgressModal(procurementId, data) {
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

// 渲染概览页面
function renderOverviewTab(data) {
    const budget = data.total_budget || 0;
    
    return `
    <div class="row">
        <div class="col-md-6">
            <div class="card h-100">
                <div class="card-header bg-light-primary">
                    <h6 class="mb-0"><i class="fas fa-info-circle me-2"></i>基本信息</h6>
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
                    
                    <div class="row mb-3">
                        <div class="col-6">
                            <label class="form-label">甲方联系人</label>
                            <input type="text" class="form-control" name="client_contact" value="${data.client_contact || ''}">
                        </div>
                        <div class="col-6">
                            <label class="form-label">甲方联系方式</label>
                            <input type="text" class="form-control" name="client_phone" value="${data.client_phone || ''}">
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="col-md-6">
            <div class="card h-100">
                <div class="card-header bg-light-success">
                    <h6 class="mb-0"><i class="fas fa-money-bill-wave me-2"></i>预算信息</h6>
                </div>
                <div class="card-body">
                    <div class="text-center py-3">
                        <h3 class="text-success mb-1">¥${budget.toLocaleString('zh-CN', {minimumFractionDigits: 2})}</h3>
                        <small class="text-muted">项目总预算</small>
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
    </div>`;
}

// 渲染供应商概览表格
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
        const profit = supplier.profit || 0;
        const profitRate = budget > 0 ? ((profit / budget) * 100).toFixed(2) : 0;
        const profitClass = profit >= 0 ? 'text-success' : 'text-danger';
        const statusBadge = supplier.is_selected ? 
            '<span class="badge bg-success">已选择</span>' : 
            '<span class="badge bg-secondary">备选</span>';

        tableHTML += `
        <tr>
            <td class="fw-bold">${supplier.name}</td>
            <td>¥${supplier.total_quote?.toLocaleString('zh-CN') || '0'}</td>
            <td class="${profitClass} fw-bold">¥${profit.toLocaleString('zh-CN')}</td>
            <td class="${profitClass}">${profitRate}%</td>
            <td>${statusBadge}</td>
        </tr>`;
    });

    tableHTML += `</tbody></table></div>`;
    return tableHTML;
}

// 渲染供应商管理页面
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

// 渲染供应商分页
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

// 渲染供应商卡片
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
                    ${supplier.name}
                    ${supplier.is_selected ? '<span class="badge bg-success ms-2">已选择</span>' : ''}
                </h6>
            </div>
            <div>
                <button class="btn btn-sm btn-outline-primary me-1" onclick="editSupplier(${supplier.id})">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteSupplier(${supplier.id})">
                    <i class="fas fa-trash"></i>
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
                    <p class="mb-0 fw-bold text-primary">¥${supplier.total_quote?.toLocaleString('zh-CN') || '0'}</p>
                </div>
            </div>
            
            <div class="mt-3">
                <h6 class="border-bottom pb-1">商品信息</h6>
                ${renderSupplierCommodities(supplier.commodities || [])}
            </div>
        </div>
    </div>`;
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

// 渲染备注页面
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
