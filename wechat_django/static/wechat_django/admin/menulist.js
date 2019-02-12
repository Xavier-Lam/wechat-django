(function($) {
    var $tr = $("#result_list tbody tr"),
        root = "-";
    $("#result_list th.column-id, #result_list th.column-parent_id, #result_list td.field-id, #result_list td.field-parent_id").hide();
    $(".action-checkbox-column, .action-checkbox").remove();
    $("th.sortable a").attr("href", "javascript:;");

    // 对菜单进行重新排序
    var trs = {};
    trs[root] = [];
    $tr.removeClass("row1 row2").each(function() {
        var parentId = $(this).find("td.field-parent_id").text(),
            id = $(this).find("td.field-id").text();
        if(!trs[parentId]) trs[parentId] = [];
        trs[parentId].push([id, this]);
    })

    var $newTable = $("<tbody>");
    for(var i=0; i < trs[root].length; i++) {
        var obj = trs[root][i],
            subs = trs[obj[0]] || [];
        $newTable.append(obj[1]);
        for(var j=0; j < subs.length; j++) {
            $newTable.append(subs[j][1]);
        }
    }

    $("#result_list tbody").replaceWith($newTable);
    $("#result_list tr:odd").addClass("row1");
    $("#result_list tr:even").addClass("row2");
})(django.jQuery);