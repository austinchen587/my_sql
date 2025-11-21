/**
 * 采购进度管理模块
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
    const modalEl = document.getElementById('progressModal');
    if (!modalEl) {
        createProgressModal();
    }
    
    const modal = new bootstrap.Modal('#progressModal');
    
    // 显示加载状态
    $('#progressModalContent').html(`
        <div class="modal-header bg-warning text-dark">
            <h5 class="modal-title">
                <i class="fas fa-spinner fa-spin me-2"></i>加载中...
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body text-center py-5">
            <div class="spinner-border text-warning mb-3"></div>
            <p>加载采购进度信息...</p>
        </div>
    `);
    
    modal.show();
    
    // 加载采购进度数据
    loadProgressData(procurementId);
}

// 创建采购进度弹窗
function createProgressModal() {
    const modalHTML = `
        <div class="modal fade" id="progressModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content" id="progressModalContent">
                </div>
            </div>
        </div>
    `;
    $('body').append(modalHTML);
}

// 加载采购进度数据
function loadProgressData(procurementId) {
    $.ajax({
        url: `/emall/purchasing/procurements/${procurementId}/progress/`,
        type: 'GET',
        success: function(data) {
            renderProgressForm(procurementId, data);
        },
        error: function(xhr) {
            console.error('加载采购进度失败:', xhr);
            $('#progressModalContent').html(`
                <div class="modal-header bg-danger text-white">
                    <h5 class="modal-title">错误</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="alert alert-danger">
                        <p>无法加载采购进度信息，请稍后重试</p>
                    </div>
                </div>
            `);
        }
    });
}

// 渲染采购进度表单
function renderProgressForm(procurementId, data) {
    const htmlContent = `
        <div class="modal-header bg-warning text-dark">
            <h5 class="modal-title">
                <i class="fas fa-tasks me-2"></i>采购进度管理
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
            <form id="progressForm" data-procurement-id="${procurementId}">
                <div class="row mb-3">
                    <div class="col-md-6">
                        <label for="clientContact" class="form-label">甲方联系人</label>
                        <input type="text" class="form-control" id="clientContact" name="client_contact" 
                               value="${data.client_contact || ''}" placeholder="请输入甲方联系人">
                    </div>
                    <div class="col-md-6">
                        <label for="clientPhone" class="form-label">甲方联系方式</label>
                        <input type="text" class="form-control" id="clientPhone" name="client_phone" 
                               value="${data.client_phone || ''}" placeholder="请输入甲方联系方式">
                    </div>
                </div>
                
                <div class="row mb-3">
                    <div class="col-md-6">
                        <label for="supplierSource" class="form-label">供应商获取渠道</label>
                        <select class="form-select" id="supplierSource" name="supplier_source">
                            <option value="">请选择渠道</option>
                            <option value="平台推荐" ${data.supplier_source === '平台推荐' ? 'selected' : ''}>平台推荐</option>
                            <option value="自主开发" ${data.supplier_source === '自主开发' ? 'selected' : ''}>自主开发</option>
                            <option value="客户推荐" ${data.supplier_source === '客户推荐' ? 'selected' : ''}>客户推荐</option>
                            <option value="其他" ${data.supplier_source === '其他' ? 'selected' : ''}>其他</option>
                        </select>
                    </div>
                    <div class="col-md-6">
                        <label for="supplierStore" class="form-label">供应商店铺名称</label>
                        <input type="text" class="form-control" id="supplierStore" name="supplier_store" 
                               value="${data.supplier_store || ''}" placeholder="请输入供应商店铺名称">
                    </div>
                </div>
                
                <div class="row mb-3">
                    <div class="col-md-6">
                        <label for="supplierContact" class="form-label">供应商联系方式</label>
                        <input type="text" class="form-control" id="supplierContact" name="supplier_contact" 
                               value="${data.supplier_contact || ''}" placeholder="请输入供应商联系方式">
                    </div>
                    <div class="col-md-6">
                        <label for="cost" class="form-label">成本（元）</label>
                        <input type="number" class="form-control" id="cost" name="cost" 
                               value="${data.cost || ''}" placeholder="请输入成本金额" step="0.01" min="0">
                    </div>
                </div>
                
                <div class="alert alert-info">
                    <small>
                        <i class="fas fa-info-circle me-1"></i>
                        采购项目：${data.procurement_title || '未知项目'}
                    </small>
                </div>
            </form>
        </div>
        <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
            <button type="button" class="btn btn-primary" id="saveProgress">保存进度</button>
        </div>
    `;
    
    $('#progressModalContent').html(htmlContent);
    bindProgressFormEvents(procurementId);
}

// 绑定进度表单事件
function bindProgressFormEvents(procurementId) {
    $('#saveProgress').on('click', function() {
        saveProgressData(procurementId);
    });
}

// 保存采购进度数据
function saveProgressData(procurementId) {
    const formData = {
        client_contact: $('#clientContact').val(),
        client_phone: $('#clientPhone').val(),
        supplier_source: $('#supplierSource').val(),
        supplier_store: $('#supplierStore').val(),
        supplier_contact: $('#supplierContact').val(),
        cost: $('#cost').val()
    };
    
    $.ajax({
        url: `/emall/purchasing/procurements/${procurementId}/progress/`,
        type: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        data: formData,
        beforeSend: function() {
            $('#saveProgress').prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-1"></i>保存中...');
        },
        success: function(response) {
            if (response.success) {
                showToast('采购进度保存成功', 'success');
                $('#progressModal').modal('hide');
            } else {
                showToast(response.errors || '保存失败', 'error');
            }
        },
        error: function(xhr) {
            showToast('网络错误，请重试', 'error');
        },
        complete: function() {
            $('#saveProgress').prop('disabled', false).html('保存进度');
        }
    });
}
