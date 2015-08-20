(function ($) {
    $.fn.bootstrapSelect = function (options) {
        var settings = $.extend({
            icon: null,
            callback: function (e) {
            },
            renderItem: function ($opt, $el) {
                $el.text($opt.text());
            },
            renderSelect: function ($opt, $el) {
                $el.text($opt.text());
            }
        }, options);

        return this.each(function () {
            var $select = $(this);
            // hide original <select>
            $select.hide();
            // build the dropdown
            var $dropdown = $('<div class="btn-group">');
            var $button = $('<button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false"/>');
            var $value = $('<span class="value"/>');
            var $listing = $('<ul class="dropdown-menu"/>');
            if (settings.icon)
                $button.append(settings.icon);
            $button.append($value).append(' ').append($('<span class="caret"/>'));
            $dropdown.append($button).append($listing);
            var selected_items = $select.find('> option:selected'), $selected_link;
            $select.find('> option').each(function (i, item) {
                var $item = $(item);
                var $li = $('<li/>');
                var $link = $('<a/>');
                settings.renderItem.call(this, $item, $link);
                $link.click(function (e) {
                    e.preventDefault();
                    settings.renderSelect.call(this, $item, $value);
                    settings.callback.call(this, item);
                    $select.val($item.attr('value')).change();
                });
                if ($.inArray(item, selected_items) > -1)
                    $selected_link = $link; // we do not support 'multiple' <select>
                $li.append($link);
                $listing.append($li);
            });
            // insert it where <select> was
            $select.after($dropdown);
            // trigger a click for the current selected option
            if ($selected_link)
                $selected_link.click();
        });
    };

    $(function () {
        // hide basic textarea
        $('textarea[name="code"]').hide();
        // ACE code editor
        var editor = ace.edit("code-editor");
        editor.setTheme("ace/theme/monokai");
        editor.setOptions({
            minLines: 30,
            maxLines: 30,
            showLineNumbers: true,
            highlightActiveLine: true,
            showPrintMargin: false,
            autoScrollEditorIntoView: true
        });
        var theme_list = ace.require("ace/ext/themelist").themesByName;

        $('#editor-form select[name="language"]').bootstrapSelect({
            renderSelect: function ($opt, $el) {
                $el.text($opt.text()).prepend(' ').prepend($('<i class="fa fa-code"/>'));
            },
            callback: function (item) {
                var mode = $(item).attr('data-mode');
                editor.getSession().setMode("ace/mode/" + mode);
            }
        });

        // Build the themes select
        var $editor_themes = $('#editor-form select#code-editor-theme');
        $.each(theme_list, function(i, theme) {
            $editor_themes.append(
                $('<option/>')
                    .attr('value', theme.name)
                    .attr('data-dark', theme.isDark)
                    .text(theme.caption));
        });
        $editor_themes.bootstrapSelect({
            renderSelect: function ($opt, $el) {
                $el.text($opt.text()).prepend(' ').prepend($('<i class="fa fa-paint-brush"/>'));
            },
            renderItem: function($item, $el) {
                $el.text($item.text()).prepend(' ').prepend($('<i/>').addClass('fa').addClass($item.attr('data-dark') === 'true' ? 'fa-circle' : 'fa-circle-thin'));
            },
            callback: function (item) {
                var name = $(item).attr('value');
                editor.setTheme("ace/theme/" + name);
            }
        });

        $('#editor-form select#code-editor-font-size').bootstrapSelect({
            renderSelect: function ($opt, $el) {
                $el.text($opt.text()).prepend(' ').prepend($('<i class="fa fa-font"/>'));
            },
            callback: function (item) {
                var size = parseInt($(item).attr('value'));
                editor.setFontSize(size);
            }
        });

    });
}(jQuery));