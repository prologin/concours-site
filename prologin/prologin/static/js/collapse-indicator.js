$(function () {
    var DEFAULT_ICON_COLLAPSED = 'angle-double-right';
    var DEFAULT_ICON_EXPANDED = 'angle-double-down';

    function getIndicator(el) {
        var href = $(el).attr('id');
        return $('[data-indicator="#' + href + '"]');
    }

    function indicatorIcon(el, expanded) {
        return 'fa-' + (expanded
                ? (el.attr('data-icon-expanded') || DEFAULT_ICON_EXPANDED)
                : (el.attr('data-icon-collapsed') || DEFAULT_ICON_COLLAPSED));
    }

    $('.collapse')
        .on('show.bs.collapse', function () {
            var indicator = getIndicator(this);
            indicator
                .removeClass(indicatorIcon(indicator, false))
                .addClass(indicatorIcon(indicator, true));
        })
        .on('hide.bs.collapse', function () {
            var indicator = getIndicator(this);
            indicator
                .removeClass(indicatorIcon(indicator, true))
                .addClass(indicatorIcon(indicator, false));
        })
        .each(function () {
            var expanded = $(this).hasClass('in');
            var indicator = getIndicator(this);
            indicator
                .toggleClass(indicatorIcon(indicator, true), expanded)
                .toggleClass(indicatorIcon(indicator, false), !expanded);
        });
});