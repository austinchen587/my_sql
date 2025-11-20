// 搜索按钮事件
function bindSearchEvents(table) {
    $('#searchBtn').on('click', function() {
        table.ajax.reload();
    });

    // 重置按钮事件
    $('#resetBtn').on('click', function() {
        $('.filter-input').val('');
        table.ajax.reload();
    });

    // 回车键搜索
    $('.filter-input').on('keypress', function(e) {
        if (e.which === 13) {
            table.ajax.reload();
        }
    });
}
