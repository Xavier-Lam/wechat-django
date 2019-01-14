(function($) {
    // ruleform
    var typeChanged = function(e) {
        setForm($(this).closest(".dynamic-rules"), $(this).val());
    }, setForm = function($row, type) {
        $row.find(".form-row:not(.field-type,.field-weight)").hide();
        switch(type) {
            case "all":
                break;
            case "msg_type":
                $row.find(".form-row.field-msg_type").show();
                break;
            case "eventkey":
                $row.find(".form-row.field-content").show();
            case "event":
                $row.find(".form-row.field-event").show();
                break;
            case "contain":
            case "equal":
            case "regex":
                $row.find(".form-row.field-content").show();
                break;
        }
    };

    $(document).ready(function() {
        $(".dynamic-rules").each(function() {
            var $row = $(this);
            var id = $row.attr("id");
            var type = $row.find('[name=' + id + '-type]').on("change", typeChanged)
                .val();
            setForm($row, type);
        });
    })

    $(document).on('formset:added', function(event, $row, formsetName) {
        if(formsetName == "rules") {
            var id = $row.attr("id");
            $row.find('[name=' + id + '-type]').on("change", typeChanged);
            setForm($row);
        }
    });

    // $(document).on('formset:removed', function(event, $row, formsetName) {
    // });
})(django.jQuery);

(function($) {
    // replyform
    var typeChanged = function(e) {
        setForm($(this).closest(".dynamic-replies"), $(this).val());
    }, setForm = function($row, type) {
        $row.find(".form-row:not(.field-msg_type)").hide();
        switch(type) {
            case "custom":
                $row.find(".form-row.field-program").show();
                break;
            case "forward":
                $row.find(".form-row.field-url").show();
                break;
            case "news":
                break;
            case "video":
                ;
            case "music":
            case "image":
            case "voice":
            case "text":
                $row.find(".form-row.field-content").show();
                break;
        }
    };

    $(document).ready(function() {
        $(".dynamic-replies").each(function() {
            var $row = $(this);
            var id = $row.attr("id");
            var type = $row.find('[name=' + id + '-msg_type]').on("change", typeChanged)
                .val();
            setForm($row, type);
        });
    })

    $(document).on('formset:added', function(event, $row, formsetName) {
        if(formsetName == "replies") {
            var id = $row.attr("id");
            $row.find('[name=' + id + '-msg_type]').on("change", typeChanged);
            setForm($row);
        }
    });
})(django.jQuery);