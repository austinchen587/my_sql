// 加载指示器
$(document).ajaxStart(function() {
    $("#loading").show();
}).ajaxStop(function() {
    $("#loading").hide();
});

// 主初始化函数
$(function() {
    // 初始化DataTable
    const table = initializeDataTable();
    
    // 绑定事件
    bindSearchEvents(table);
    bindDetailEvents(table);
});
