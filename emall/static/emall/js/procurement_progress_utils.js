/**
 * 工具函数模块
 */

// 保存所有数据
function saveAllData(procurementId) {
    const formData = {
        bidding_status: $('#progressModal select[name="bidding_status"]').val(),
        client_contact: $('#progressModal input[name="client_contact"]').val(),
        client_phone: $('#progressModal input[name="client_phone"]').val(),
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
            remark_content: remarkContent,  // 将 'content' 改为 'remark_content'
            created_by: remarkCreator
        };
    }
    
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

// 添加新备注
function addNewRemark() {
    const content = $('#newRemark').val().trim();
    const creator = $('#remarkCreator').val().trim();
    
    if (!content) {
        showToast('请输入备注内容', 'error');
        return;
    }
    
    if (!creator) {
        showToast('请输入创建人', 'error');
        return;
    }
    
    // 禁用按钮，显示加载状态
    const addBtn = $('#remarks-tab').find('.btn-success');
    const originalText = addBtn.html();
    addBtn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-1"></i>添加中...');
    
    // 注意：这里的字段名应该是 remark_content 而不是 content
    const remarkData = {
        new_remark: {
            remark_content: content,  // 确保这里是 remark_content
            created_by: creator
        }
    };
    
    console.log('准备发送的备注数据:', remarkData);
    
    $.ajax({
        url: `/emall/purchasing/procurement/${currentProcurementId}/update/`,
        method: 'POST',
        data: JSON.stringify(remarkData),
        contentType: 'application/json',
        headers: {
            'X-CSRFToken': getCSRFToken()
        },
        success: function(response) {
            console.log('备注保存成功响应:', response);
            showToast('备注添加成功', 'success');
            
            // 清空输入框
            $('#newRemark').val('');
            
            // 立即刷新备注历史显示
            refreshRemarksHistory();
        },
        error: function(xhr) {
            console.error('备注保存失败:', xhr);
            const errorMsg = xhr.responseJSON?.error || '添加备注失败，请稍后重试';
            showToast('添加备注失败: ' + errorMsg, 'error');
        },
        complete: function() {
            addBtn.prop('disabled', false).html(originalText);
        }
    });
}

// 提交供应商表单
function submitSupplierForm() {
    try {
        const form = document.getElementById('addSupplierForm');
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
    
        const validationResult = validateSupplierInfo(supplierData);
        if (!validationResult.isValid) {
            showToast(validationResult.message, 'error');
            return;
        }

        let hasValidationError = false;
        $('.commodity-item').each(function() {
            try {
                const commodityId = $(this).data('id');
                const commodity = {
                    name: $(`input[name="commodities[${commodityId}][name]"]`).val()?.trim() || '',
                    specification: $(`input[name="commodities[${commodityId}][specification]"]`).val()?.trim() || '',
                    price: parseFloat($(`input[name="commodities[${commodityId}][price]"]`).val()) || 0,
                    quantity: parseInt($(`input[name="commodities[${commodityId}][quantity]"]`).val()) || 0,
                    product_url: $(`input[name="commodities[${commodityId}][product_url]"]`).val()?.trim() || ''
                };
                
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
        
        const submitBtn = $('#addSupplierModal').find('.btn-primary');
        const originalText = submitBtn.html();
        submitBtn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-1"></i>保存中...');
        
        $.ajax({
            url: `/emall/purchasing/procurement/${currentProcurementId}/add-supplier/`,
            method: 'POST',
            data: JSON.stringify(supplierData),
            contentType: 'application/json',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            success: function(response) {
                showToast('供应商添加成功', 'success');
                $('#addSupplierModal').modal('hide');
                form.reset();
                
                if (typeof loadProgressData === 'function') {
                    loadProgressData(currentProcurementId);
                }
                
                $(document).trigger('supplier:added', [response.data || supplierData]);
            },
            error: function(xhr) {
                let errorMessage = '添加失败，请稍后重试';
                
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
                } else if (xhr.status === 403) {
                    errorMessage = '权限不足，无法添加供应商';
                } else if (xhr.status === 409) {
                    errorMessage = '该供应商已存在';
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
        console.error('提交供应商表单时发生错误:', error);
        showToast('系统错误，请重试', 'error');
    }
}

// 供应商信息验证函数
function validateSupplierInfo(data) {
    if (!data.name) {
        return {
            isValid: false,
            message: '供应商名称为必填项'
        };
    }
    
    if (data.name.length < 2 || data.name.length > 100) {
        return {
            isValid: false,
            message: '供应商名称长度应在2-100个字符之间'
        };
    }
    
    if (data.contact) {
        const phoneRegex = /^1[3-9]\d{9}$/;
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        
        if (!phoneRegex.test(data.contact) && !emailRegex.test(data.contact)) {
            return {
                isValid: false,
                message: '请输入有效的手机号码或邮箱地址'
            };
        }
    }
    
    if (data.store_name && data.store_name.length > 100) {
        return {
            isValid: false,
            message: '店铺名称不能超过100个字符'
        };
    }
    
    if (data.source && data.source.length > 50) {
        return {
            isValid: false,
            message: '获取渠道不能超过50个字符'
        };
    }
    
    return {
        isValid: true,
        message: '验证通过'
    };
}

// 商品数据验证函数
function validateCommodityData(commodity) {
    if (!commodity.name) {
        return {
            isValid: false,
            message: '商品名称为必填项'
        };
    }
    
    if (commodity.name.length > 200) {
        return {
            isValid: false,
            message: '商品名称不能超过200个字符'
        };
    }
    
    if (!commodity.price || commodity.price <= 0) {
        return {
            isValid: false,
            message: '商品价格必须大于0'
        };
    }
    
    if (commodity.price > 999999999) {
        return {
            isValid: false,
            message: '商品价格超出合理范围'
        };
    }
    
    if (!commodity.quantity || commodity.quantity <= 0) {
        return {
            isValid: false,
            message: '商品数量必须大于0'
        };
    }
    
    if (commodity.quantity > 999999) {
        return {
            isValid: false,
            message: '商品数量超出合理范围'
        };
    }
    
    if (commodity.specification && commodity.specification.length > 500) {
        return {
            isValid: false,
            message: '商品规格不能超过500个字符'
        };
    }
    
    if (commodity.product_url) {
        try {
            new URL(commodity.product_url);
        } catch (error) {
            return {
                isValid: false,
                message: '请输入有效的商品链接'
            };
        }
    }
    
    return {
        isValid: true,
        message: '验证通过'
    };
}

// 获取字段标签
function getFieldLabel(field) {
    const labels = {
        'name': '供应商名称',
        'source': '获取渠道',
        'contact': '联系方式',
        'store_name': '店铺名称',
        'is_selected': '选择状态'
    };
    return labels[field] || field;
}

// 获取CSRF Token
function getCSRFToken() {
    return $('meta[name="csrf-token"]').attr('content') || 
           $('input[name="csrfmiddlewaretoken"]').val() ||
           document.cookie.match(/csrftoken=([^;]+)/)?.[1];
}

// Toast提示函数
function showToast(message, type = 'info') {
    $('.toast').remove();
    
    const iconMap = {
        'success': 'fa-check-circle',
        'error': 'fa-exclamation-circle',
        'warning': 'fa-exclamation-triangle',
        'info': 'fa-info-circle'
    };
    
    const toastHTML = `
    <div class="toast align-items-center text-white bg-${getToastClass(type)} border-0 position-fixed" 
         style="z-index: 9999; top: 20px; right: 20px;" role="alert">
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas ${iconMap[type] || 'fa-info-circle'} me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    </div>`;
    
    $('body').append(toastHTML);
    $('.toast').toast({ delay: 4000 }).toast('show');
}

function getToastClass(type) {
    const classes = {
        'success': 'success',
        'error': 'danger',
        'warning': 'warning',
        'info': 'info'
    };
    return classes[type] || 'info';
}



// 刷新备注历史
function refreshRemarksHistory() {
    console.log('开始刷新备注历史'); // 添加调试日志
    
    $.ajax({
        url: `/emall/purchasing/procurement/${currentProcurementId}/progress/`,
        type: 'GET',
        success: function(data) {
            console.log('刷新备注历史获取到的数据:', data); // 添加调试日志
            
            // 更新备注页面的备注历史
            $('#remarksHistory').html(renderRemarksHistory(data.remarks_history || []));
            
            // 更新概览页面的备注显示
            const overviewRemarksHTML = renderOverviewRemarks(data.remarks_history || []);
            $('#overview .card:last-child .card-body').html(overviewRemarksHTML);
        },
        error: function(xhr) {
            console.error('刷新备注失败:', xhr);
            showToast('刷新备注失败', 'error');
        }
    });
}