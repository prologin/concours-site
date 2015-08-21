(function ($) {
    // some constants for localStorages
    var THEME_STORAGE_KEY = 'prologin.code-editor.theme', THEME_DEFAULT = 'monokai';
    var FONT_SIZE_STORAGE_KEY = 'prologin.code-editor.font-size', FONT_SIZE_DEFAULT = '11';

    // select-to-bootstrap-dropdown jQuery plugin (for graceful degradation)
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
        var $code_textarea = $('textarea[name="code"]').hide();
        // ACE code editor
        var editor = ace.edit("code-editor");
        editor.setOptions({
            minLines: 30,
            maxLines: 30,
            showLineNumbers: true,
            highlightActiveLine: true,
            showPrintMargin: false,
            autoScrollEditorIntoView: true
        });

        var $current_language_label = $('#editor-current-lang');
        $('#editor-form select[name="language"]').bootstrapSelect({
            renderSelect: function ($opt, $el) {
                $el.text($opt.text()).prepend(' ').prepend($('<i class="fa fa-code"/>'));
            },
            callback: function (item) {
                var $item = $(item);
                var mode = $item.attr('data-mode');
                editor.getSession().setMode("ace/mode/" + mode);
                $current_language_label.text($item.text());
            }
        });

        // Build the themes select
        var theme_list = ace.require("ace/ext/themelist").themesByName;
        var $editor_themes = $('#editor-form select#code-editor-theme');
        $.each(theme_list, function(i, theme) {
            $editor_themes.append(
                $('<option/>')
                    .attr('value', theme.name)
                    .attr('data-dark', theme.isDark)
                    .text(theme.caption));
        });
        var preferred_theme = localStorage.getItem(THEME_STORAGE_KEY) || THEME_DEFAULT;
        $editor_themes.val(preferred_theme).change();
        $editor_themes.bootstrapSelect({
            renderSelect: function ($opt, $el) {
                $el.text($opt.text()).prepend(' ').prepend($('<i class="fa fa-paint-brush"/>'));
            },
            renderItem: function($item, $el) {
                $el.text($item.text()).prepend(' ').prepend($('<i/>').addClass('fa').addClass($item.attr('data-dark') === 'true' ? 'fa-circle' : 'fa-circle-thin'));
            },
            callback: function (item) {
                var name = $(item).attr('value');
                localStorage.setItem(THEME_STORAGE_KEY, name);
                editor.setTheme("ace/theme/" + name);
            }
        });

        var $editor_font_sizes = $('#editor-form select#code-editor-font-size');
        var preferred_font_size = localStorage.getItem(FONT_SIZE_STORAGE_KEY) || FONT_SIZE_DEFAULT;
        $editor_font_sizes.val(preferred_font_size).change();
        $editor_font_sizes.bootstrapSelect({
            renderSelect: function ($opt, $el) {
                $el.text($opt.text()).prepend(' ').prepend($('<i class="fa fa-font"/>'));
            },
            callback: function (item) {
                var size = $(item).attr('value');
                localStorage.setItem(FONT_SIZE_STORAGE_KEY, size);
                editor.setFontSize(parseInt(size));
            }
        });

        // store solution in textarea on submit
        $('#editor-form').submit(function(e) {
            e.preventDefault();
            $code_textarea.val(editor.getSession().getDocument().getValue());
            this.submit();
        });

    });
}(jQuery));