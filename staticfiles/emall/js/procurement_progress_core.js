/**
 * 采购进度管理核心模块
 */

let currentProcurementId = null;
let currentSupplierPage = 1;
let suppliersPerPage = 5;
let modalStack = [];

// 绑定进度事件
function bindProgressEvents() {
    $('#procurementTable').off('click', '.btn-progress').on('click', '.btn-progress', function() {
        const procurementId = $(this).data('id');
        showProgressModal(procurementId);
    });
}

// 显示采购进度弹窗
function showProgressModal(procurementId) {
    currentProcurementId = procurementId;
    currentSupplierPage = 1;
    
    if (!$('#progressModal').length) {
        createProgressModal();
    }
    
    $('#progressModal').css('z-index', '1060');
    const modal = new bootstrap.Modal('#progressModal');
    
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
    
    modalStack.push('progressModal');
    updateModalZIndexes();
    modal.show();
    loadProgressData(procurementId);
    
    $('#progressModal').off('hidden.bs.modal').on('hidden.bs.modal', function() {
        const index = modalStack.indexOf('progressModal');
        if (index > -1) {
            modalStack.splice(index, 1);
        }
        updateModalZIndexes();
    });
}

// 加载采购进度数据
function loadProgressData(procurementId) {
    $.ajax({
        url: `/emall/purchasing/procurement/${procurementId}/progress/`,
        type: 'GET',
        success: function(data) {
            renderProgressModal(procurementId, data);
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
                        <h6><i class="fas fa-exclamation-triangle me-2"></i>加载失败</h6>
                        <p class="mb-0">无法加载采购进度信息，请检查网络连接或稍后重试。</p>
                    </div>
                    <div class="text-center">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                    </div>
                </div>
            `);
        }
    });
}

// 分页功能
function changeSupplierPage(page) {
    currentSupplierPage = page;
    loadProgressData(currentProcurementId);
    $('#suppliers-tab').tab('show');
}
