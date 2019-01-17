(function($) {
    // ruleform
    var setForm = function(type) {
        var $row = $("fieldset");
        $row.find(".form-row:not(.field-type,.field-weight,.field-menuid,.field-name)").hide();
        switch(type) {
            case "miniprogram":
                $row.find(".form-row.field-appid").show();
                $row.find(".form-row.field-pagepath").show();
            case "view":
                $row.find(".form-row.field-url").show();
                break;
            case "click":
                $row.find(".form-row.field-key").show();
                break;
        }
    };
    $("#id_type").on("change", function() {
        setForm($(this).val());
    });
    setForm($("#id_type").val());
})(django.jQuery);