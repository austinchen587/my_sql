/**
 * 模态框管理模块
 */

// 创建采购进度弹窗
function createProgressModal() {
    const modalHTML = `
    <div class="modal fade" id="progressModal" tabindex="-1" aria-labelledby="progressModalLabel" aria-hidden="true" data-bs-backdrop="static">
        <div class="modal-dialog modal-xxl" style="max-width: 1400px;">
            <div class="modal-content" id="progressModalContent">
                <!-- 内容将由JavaScript动态加载 -->
            </div>
        </div>
    </div>`;
    $('body').append(modalHTML);
}

// 更新所有模态框的 z-index
function updateModalZIndexes() {
    const baseZIndex = 1050;
    $('.modal').each(function(index) {
        const modalId = $(this).attr('id');
        const stackIndex = modalStack.indexOf(modalId);
        if (stackIndex > -1) {
            $(this).css('z-index', baseZIndex + (stackIndex + 1) * 10);
        }
    });
}

// 创建添加供应商模态框
function createAddSupplierModal() {
    if (!$('#addSupplierModal').length) {
        const modalHTML = `
        <div class="modal fade" id="addSupplierModal" tabindex="-1" aria-labelledby="addSupplierModalLabel" data-bs-backdrop="static">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title">添加供应商</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body" style="max-height: 70vh; overflow-y: auto;">
                        <form id="addSupplierForm">
                            <div class="card mb-4">
                                <div class="card-header bg-light">
                                    <h6 class="mb-0"><i class="fas fa-building me-2"></i>供应商基本信息</h6>
                                </div>
                                <div class="card-body">
                                    <div class="row">
                                        <div class="col-md-6">
                                            <div class="mb-3">
                                                <label class="form-label">供应商名称 *</label>
                                                <input type="text" class="form-control" name="name" required>
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="mb-3">
                                                <label class="form-label">获取渠道</label>
                                                <input type="text" class="form-control" name="source" placeholder="如：淘宝、京东、线下等">
                                            </div>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-6">
                                            <div class="mb-3">
                                                <label class="form-label">联系方式</label>
                                                <input type="text" class="form-control" name="contact" placeholder="电话/微信/QQ">
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="mb-3">
                                                <label class="form-label">店铺名称</label>
                                                <input type="text" class="form-control" name="store_name" placeholder="线上店铺或公司名称">
                                            </div>
                                        </div>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">是否选择该供应商</label>
                                        <div class="form-check">
                                            <input type="checkbox" class="form-check-input" name="is_selected" value="true">
                                            <label class="form-check-label">选择此供应商作为主要供应商</label>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="card">
                                <div class="card-header bg-light d-flex justify-content-between align-items-center">
                                    <h6 class="mb-0"><i class="fas fa-boxes me-2"></i>商品信息</h6>
                                    <button type="button" class="btn btn-sm btn-primary" onclick="addCommodityField()">
                                        <i class="fas fa-plus me-1"></i>添加商品
                                    </button>
                                </div>
                                <div class="card-body">
                                    <div id="commoditiesContainer">
                                        <!-- 商品表单将动态添加到这里 -->
                                    </div>
                                    <div class="text-center mt-3">
                                        <button type="button" class="btn btn-outline-primary btn-sm" onclick="addCommodityField()">
                                            <i class="fas fa-plus me-1"></i>继续添加商品
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" onclick="submitSupplierForm()">
                            <i class="fas fa-save me-1"></i>保存供应商信息
                        </button>
                    </div>
                </div>
            </div>
        </div>`;
        $('body').append(modalHTML);
        addCommodityField();
    }
}

// 显示添加供应商模态框
function showAddSupplierModal() {
    if (!$('#addSupplierModal').length) {
        createAddSupplierModal();
    } else {
        resetSupplierForm();
    }
    
    $('#addSupplierModal').css('z-index', '1070');
    modalStack.push('addSupplierModal');
    updateModalZIndexes();
    $('#addSupplierModal').modal('show');
    
    $('#addSupplierModal').off('hidden.bs.modal').on('hidden.bs.modal', function() {
        const index = modalStack.indexOf('addSupplierModal');
        if (index > -1) {
            modalStack.splice(index, 1);
        }
        updateModalZIndexes();
    });
}
