/**
 * 供应商管理功能模块
 */
let currentEditingSupplierId = null;
// 编辑供应商 - 修复编辑功能
function editSupplier(supplierId) {
    currentEditingSupplierId = supplierId;
    
    // 获取当前采购数据
    $.ajax({
        url: `/emall/purchasing/procurement/${currentProcurementId}/progress/`,
        type: 'GET',
        success: function(data) {
            const supplier = data.suppliers_info.find(s => s.id === supplierId);
            if (supplier) {
                showEditSupplierModal(supplier);
            } else {
                showToast('找不到供应商信息', 'error');
            }
        },
        error: function(xhr) {
            console.error('获取供应商详情失败:', xhr);
            showToast('获取供应商信息失败', 'error');
        }
    });
}
// 显示编辑供应商模态框
function showEditSupplierModal(supplier) {
    if (!$('#editSupplierModal').length) {
        createEditSupplierModal();
    }
    
    // 填充供应商数据
    $('#editSupplierModal input[name="name"]').val(supplier.name || '');
    $('#editSupplierModal input[name="source"]').val(supplier.source || '');
    $('#editSupplierModal input[name="contact"]').val(supplier.contact || '');
    $('#editSupplierModal input[name="store_name"]').val(supplier.store_name || '');
    $('#editSupplierModal input[name="is_selected"]').prop('checked', supplier.is_selected || false);
    
    // 清空商品容器并重新填充
    $('#editSupplierModal #commoditiesContainer').empty();
    if (supplier.commodities && supplier.commodities.length > 0) {
        supplier.commodities.forEach(commodity => {
            addCommodityFieldToEditModal(commodity);
        });
    } else {
        addCommodityFieldToEditModal();
    }
    
    // 设置z-index和模态框堆栈
    $('#editSupplierModal').css('z-index', '1080');
    modalStack.push('editSupplierModal');
    updateModalZIndexes();
    
    $('#editSupplierModal').modal('show');
    
    $('#editSupplierModal').off('hidden.bs.modal').on('hidden.bs.modal', function() {
        const index = modalStack.indexOf('editSupplierModal');
        if (index > -1) {
            modalStack.splice(index, 1);
        }
        updateModalZIndexes();
        currentEditingSupplierId = null;
    });
}
// 创建编辑供应商模态框
function createEditSupplierModal() {
    const modalHTML = `
    <div class="modal fade" id="editSupplierModal" tabindex="-1" aria-labelledby="editSupplierModalLabel" data-bs-backdrop="static">
        <div class="modal-dialog modal-xl">
            <div class="modal-content">
                <div class="modal-header bg-warning text-dark">
                    <h5 class="modal-title">编辑供应商信息</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body" style="max-height: 70vh; overflow-y: auto;">
                    <form id="editSupplierForm">
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
                                <button type="button" class="btn btn-sm btn-primary" onclick="addCommodityFieldToEditModal()">
                                    <i class="fas fa-plus me-1"></i>添加商品
                                </button>
                            </div>
                            <div class="card-body">
                                <div id="commoditiesContainer">
                                    <!-- 商品表单将动态添加到这里 -->
                                </div>
                                <div class="text-center mt-3">
                                    <button type="button" class="btn btn-outline-primary btn-sm" onclick="addCommodityFieldToEditModal()">
                                        <i class="fas fa-plus me-1"></i>继续添加商品
                                    </button>
                                </div>
                            </div>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                    <button type="button" class="btn btn-warning" onclick="submitEditSupplierForm()">
                        <i class="fas fa-save me-1"></i>更新供应商信息
                    </button>
                </div>
            </div>
        </div>
    </div>`;
    $('body').append(modalHTML);
}
// 为编辑模态框添加商品字段
function addCommodityFieldToEditModal(commodityData = null) {
    const commodityId = commodityData ? commodityData.id || Date.now() : Date.now();
    const commodityHTML = `
    <div class="commodity-item card mb-3" data-id="${commodityId}">
        <div class="card-header bg-light-subtle d-flex justify-content-between align-items-center">
            <h6 class="mb-0">商品信息</h6>
            <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeCommodityFieldFromEditModal(${commodityId})">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="card-body">
            <div class="row">
                <div class="col-md-4">
                    <div class="mb-3">
                        <label class="form-label">商品名称 *</label>
                        <input type="text" class="form-control commodity-name" name="commodities[${commodityId}][name]" 
                               value="${commodityData ? commodityData.name : ''}" required>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="mb-3">
                        <label class="form-label">商品规格</label>
                        <input type="text" class="form-control commodity-specification" name="commodities[${commodityId}][specification]" 
                               value="${commodityData ? commodityData.specification || '' : ''}" placeholder="型号、尺寸、配置等">
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="mb-3">
                        <label class="form-label">产品链接</label>
                        <input type="url" class="form-control commodity-url" name="commodities[${commodityId}][product_url]" 
                               value="${commodityData ? commodityData.product_url || '' : ''}" placeholder="https://...">
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-md-6">
                    <div class="mb-3">
                        <label class="form-label">价格 (元) *</label>
                        <input type="number" class="form-control commodity-price" name="commodities[${commodityId}][price]" 
                               value="${commodityData ? commodityData.price || '' : ''}" step="0.01" min="0" required>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="mb-3">
                        <label class="form-label">数量 *</label>
                        <input type="number" class="form-control commodity-quantity" name="commodities[${commodityId}][quantity]" 
                               value="${commodityData ? commodityData.quantity || '' : ''}" min="1" required>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-12">
                    <div class="mb-0">
                        <label class="form-label">小计</label>
                        <div class="form-control-plaintext commodity-subtotal text-primary fw-bold">
                            ¥${commodityData ? (commodityData.price * commodityData.quantity).toFixed(2) : '0.00'}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>`;
    
    $('#editSupplierModal #commoditiesContainer').append(commodityHTML);
    
    // 绑定价格和数量的计算事件
    $(`#editSupplierModal input[name="commodities[${commodityId}][price]"], #editSupplierModal input[name="commodities[${commodityId}][quantity]"]`).on('input', function() {
        calculateCommoditySubtotalInEditModal(commodityId);
    });
}
// 计算编辑模态框中的商品小计
function calculateCommoditySubtotalInEditModal(commodityId) {
    const price = parseFloat($(`#editSupplierModal input[name="commodities[${commodityId}][price]"]`).val()) || 0;
    const quantity = parseInt($(`#editSupplierModal input[name="commodities[${commodityId}][quantity]"]`).val()) || 0;
    const subtotal = price * quantity;
    
    $(`#editSupplierModal .commodity-item[data-id="${commodityId}"] .commodity-subtotal`).text(`¥${subtotal.toFixed(2)}`);
    updateTotalQuotePreviewInEditModal();
}
// 更新编辑模态框中的总报价预览
function updateTotalQuotePreviewInEditModal() {
    let totalQuote = 0;
    $('#editSupplierModal .commodity-item').each(function() {
        const price = parseFloat($(this).find('.commodity-price').val()) || 0;
        const quantity = parseInt($(this).find('.commodity-quantity').val()) || 0;
        totalQuote += price * quantity;
    });
    
    $('#editSupplierModal #totalQuotePreview').remove();
    if ($('#editSupplierModal .commodity-item').length > 0) {
        $('#editSupplierModal #commoditiesContainer').before(`
            <div class="alert alert-info mb-3" id="totalQuotePreview">
                <i class="fas fa-calculator me-2"></i>
                <strong>当前总报价预览:</strong> ¥${totalQuote.toFixed(2)}
            </div>
        `);
    }
}
// 删除编辑模态框中的商品字段
function removeCommodityFieldFromEditModal(commodityId) {
    $(`#editSupplierModal .commodity-item[data-id="${commodityId}"]`).remove();
    updateTotalQuotePreviewInEditModal();
}
// 提交编辑供应商表单
function submitEditSupplierForm() {
    try {
        const form = document.getElementById('editSupplierForm');
        if (!form) {
            showToast('表单未找到，请刷新页面重试', 'error');
            return;
        }
        const formData = new FormData(form);
        const supplierData = {
            name: formData.get('name')?.trim() || '',
            source: formData.get('source')?.trim() || '',
            contact: formData.get('contact')?.trim() || '',
            store_name: formData.get('store_name')?.trim() || '',
            is_selected: formData.get('is_selected') === 'true',
            commodities: []
        };
    
        // 验证供应商信息
        const validationResult = validateSupplierInfo(supplierData);
        if (!validationResult.isValid) {
            showToast(validationResult.message, 'error');
            return;
        }
        // 收集商品数据
        let hasValidationError = false;
        $('#editSupplierModal .commodity-item').each(function() {
            try {
                const commodityId = $(this).data('id');
                const commodity = {
                    name: $(`#editSupplierModal input[name="commodities[${commodityId}][name]"]`).val()?.trim() || '',
                    specification: $(`#editSupplierModal input[name="commodities[${commodityId}][specification]"]`).val()?.trim() || '',
                    price: parseFloat($(`#editSupplierModal input[name="commodities[${commodityId}][price]"]`).val()) || 0,
                    quantity: parseInt($(`#editSupplierModal input[name="commodities[${commodityId}][quantity]"]`).val()) || 0,
                    product_url: $(`#editSupplierModal input[name="commodities[${commodityId}][product_url]"]`).val()?.trim() || ''
                };
                
                // 验证商品信息
                const commodityValidation = validateCommodityData(commodity);
                if (!commodityValidation.isValid) {
                    showToast(`商品 ${commodityId || ''}: ${commodityValidation.message}`, 'error');
                    hasValidationError = true;
                    return false;
                }
                
                supplierData.commodities.push(commodity);
            } catch (error) {
                console.error('处理商品数据时出错:', error);
                showToast('处理商品数据时发生错误', 'error');
                hasValidationError = true;
                return false;
            }
        });
        
        if (hasValidationError) return;
        
        if (supplierData.commodities.length === 0) {
            showToast('请至少添加一个商品', 'error');
            return;
        }
        
        // 显示加载状态
        const submitBtn = $('#editSupplierModal').find('.btn-warning');
        const originalText = submitBtn.html();
        submitBtn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-1"></i>更新中...');
        
        // 发送更新请求
        $.ajax({
            url: `/emall/purchasing/supplier/${currentEditingSupplierId}/update/`,
            method: 'PUT',
            data: JSON.stringify(supplierData),
            contentType: 'application/json',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            success: function(response) {
                showToast('供应商信息更新成功', 'success');
                $('#editSupplierModal').modal('hide');
                
                // 刷新采购进度数据
                if (typeof loadProgressData === 'function') {
                    loadProgressData(currentProcurementId);
                }
            },
            error: function(xhr) {
                let errorMessage = '更新失败，请稍后重试';
                
                if (xhr.status === 400) {
                    if (xhr.responseJSON?.errors) {
                        const fieldErrors = Object.entries(xhr.responseJSON.errors)
                            .map(([field, error]) => `${getFieldLabel(field)}: ${error}`)
                            .join(', ');
                        errorMessage = fieldErrors;
                    } else if (xhr.responseJSON?.error) {
                        errorMessage = xhr.responseJSON.error;
                    } else {
                        errorMessage = '数据验证失败，请检查输入信息';
                    }
                } else if (xhr.status === 404) {
                    errorMessage = '供应商不存在';
                } else if (xhr.status >= 500) {
                    errorMessage = '服务器错误，请稍后重试';
                }
                
                showToast(errorMessage, 'error');
            },
            complete: function() {
                submitBtn.prop('disabled', false).html(originalText);
            }
        });
        
    } catch (error) {
        console.error('提交供应商编辑表单时发生错误:', error);
        showToast('系统错误，请重试', 'error');
    }
}
// 删除供应商函数保持不变
function deleteSupplier(supplierId) {
    if (!confirm('确定要删除这个供应商吗？此操作不可撤销！')) {
        return;
    }
    
    showToast('正在删除供应商...', 'info');
    
    $.ajax({
        url: `/emall/purchasing/supplier/${supplierId}/delete/`,
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCSRFToken()
        },
        success: function(response) {
            showToast('供应商删除成功', 'success');
            loadProgressData(currentProcurementId);
        },
        error: function(xhr) {
            const errorMsg = xhr.responseJSON?.error || '删除失败，请稍后重试';
            showToast('删除失败: ' + errorMsg, 'error');
        }
    });
}

// 添加商品表单字段
function addCommodityField(commodityData = null) {
    const commodityId = commodityData ? commodityData.id || Date.now() : Date.now();
    const commodityHTML = `
    <div class="commodity-item card mb-3" data-id="${commodityId}">
        <div class="card-header bg-light-subtle d-flex justify-content-between align-items-center">
            <h6 class="mb-0">商品信息</h6>
            <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeCommodityField(${commodityId})">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="card-body">
            <div class="row">
                <div class="col-md-4">
                    <div class="mb-3">
                        <label class="form-label">商品名称 *</label>
                        <input type="text" class="form-control commodity-name" name="commodities[${commodityId}][name]" 
                               value="${commodityData ? commodityData.name : ''}" required>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="mb-3">
                        <label class="form-label">商品规格</label>
                        <input type="text" class="form-control commodity-specification" name="commodities[${commodityId}][specification]" 
                               value="${commodityData ? commodityData.specification || '' : ''}" placeholder="型号、尺寸、配置等">
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="mb-3">
                        <label class="form-label">产品链接</label>
                        <input type="url" class="form-control commodity-url" name="commodities[${commodityId}][product_url]" 
                               value="${commodityData ? commodityData.product_url || '' : ''}" placeholder="https://...">
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-md-6">
                    <div class="mb-3">
                        <label class="form-label">价格 (元) *</label>
                        <input type="number" class="form-control commodity-price" name="commodities[${commodityId}][price]" 
                               value="${commodityData ? commodityData.price || '' : ''}" step="0.01" min="0" required>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="mb-3">
                        <label class="form-label">数量 *</label>
                        <input type="number" class="form-control commodity-quantity" name="commodities[${commodityId}][quantity]" 
                               value="${commodityData ? commodityData.quantity || '' : ''}" min="1" required>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-12">
                    <div class="mb-0">
                        <label class="form-label">小计</label>
                        <div class="form-control-plaintext commodity-subtotal text-primary fw-bold">
                            ¥0.00
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>`;
    
    $('#commoditiesContainer').append(commodityHTML);
    
    $(`input[name="commodities[${commodityId}][price]"], input[name="commodities[${commodityId}][quantity]"]`).on('input', function() {
        calculateCommoditySubtotal(commodityId);
    });
    
    calculateCommoditySubtotal(commodityId);
}

// 计算商品小计
function calculateCommoditySubtotal(commodityId) {
    const price = parseFloat($(`input[name="commodities[${commodityId}][price]"]`).val()) || 0;
    const quantity = parseInt($(`input[name="commodities[${commodityId}][quantity]"]`).val()) || 0;
    const subtotal = price * quantity;
    
    $(`.commodity-item[data-id="${commodityId}"] .commodity-subtotal`).text(`¥${subtotal.toFixed(2)}`);
    updateTotalQuotePreview();
}

// 更新总报价预览
function updateTotalQuotePreview() {
    let totalQuote = 0;
    $('.commodity-item').each(function() {
        const price = parseFloat($(this).find('.commodity-price').val()) || 0;
        const quantity = parseInt($(this).find('.commodity-quantity').val()) || 0;
        totalQuote += price * quantity;
    });
    
    $('#totalQuotePreview').remove();
    if ($('.commodity-item').length > 0) {
        $('#commoditiesContainer').before(`
            <div class="alert alert-info mb-3" id="totalQuotePreview">
                <i class="fas fa-calculator me-2"></i>
                <strong>当前总报价预览:</strong> ¥${totalQuote.toFixed(2)}
            </div>
        `);
    }
}

// 删除商品字段
function removeCommodityField(commodityId) {
    $(`.commodity-item[data-id="${commodityId}"]`).remove();
    updateTotalQuotePreview();
}

// 清空供应商表单
function resetSupplierForm() {
    $('#addSupplierForm')[0].reset();
    $('#commoditiesContainer').empty();
    addCommodityField();
}
