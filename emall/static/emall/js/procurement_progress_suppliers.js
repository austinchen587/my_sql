/**
 * 供应商管理功能模块
 */

// 编辑供应商
function editSupplier(supplierId) {
    showToast(`编辑供应商 ID: ${supplierId}`, 'info');
}

// 删除供应商
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
