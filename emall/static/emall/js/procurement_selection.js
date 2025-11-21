/**
 * 采购选择功能模块
 */

// 初始化选择功能
function initSelectionModule(table) {
    bindSelectionEvents(table);
    bindProgressEvents();
}

// 绑定选择事件
function bindSelectionEvents(table) {
    // 全选/全不选
    $('#selectAll').on('click', function() {
        const isChecked = $(this).prop('checked');
        $('.select-checkbox').prop('checked', isChecked).trigger('change');
    });
    
    // 单个选择框事件
    $('#procurementTable').on('change', '.select-checkbox', function() {
        const procurementId = $(this).data('id');
        const isSelected = $(this).prop('checked');
        togglePurchaseSelection(procurementId, isSelected, $(this), table);
    });
}

// 切换采购选择状态
function togglePurchaseSelection(procurementId, isSelected, checkbox, table) {
    $.ajax({
        url: `/emall/purchasing/procurements/${procurementId}/select/`,
        type: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        beforeSend: function() {
            checkbox.prop('disabled', true);
        },
        success: function(response) {
            if (response.success) {
                // 更新行样式
                updateRowStyle(procurementId, response.is_selected, table);
                
                // 显示成功提示
                showToast('选择状态更新成功', 'success');
            } else {
                showToast(response.error || '操作失败', 'error');
                checkbox.prop('checked', !isSelected);
            }
        },
        error: function(xhr) {
            showToast('网络错误，请重试', 'error');
            checkbox.prop('checked', !isSelected);
        },
        complete: function() {
            checkbox.prop('disabled', false);
        }
    });
}

// 更新行样式
function updateRowStyle(procurementId, isSelected, table) {
    const row = $(`tr:has(.select-checkbox[data-id="${procurementId}"])`);
    
    if (isSelected) {
        row.addClass('selected-row text-danger');
        // 添加采购进度按钮
        if (!row.find('.btn-progress').length) {
            row.find('.btn-detail').after(
                `<button class="btn btn-sm btn-warning btn-progress me-1" data-id="${procurementId}">
                    <i class="fas fa-tasks me-1"></i>采购进度
                </button>`
            );
        }
    } else {
        row.removeClass('selected-row text-danger');
        // 移除采购进度按钮
        row.find('.btn-progress').remove();
    }
    
    // 重新绑定事件
    bindProgressEvents();
}

// 获取CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// 显示Toast提示
function showToast(message, type = 'info') {
    const toast = $(`
        <div class="toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `);
    
    $('#toastContainer').append(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.on('hidden.bs.toast', function() {
        $(this).remove();
    });
}
