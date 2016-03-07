(function ($) {
  /**
   * Standard affix.
   * @param options: parent: optional, the selector string to the affix's parent for scrollspy
   *                 offset: top offset; default: 20
   *                 footer: selector string to the page footer element; default: 'footer'
   */
  $.fn.standardAffix = function (options) {
    var settings = $.extend({
      offset: 20,
      footer: 'footer'
    }, options);

    return this.each(function () {
      var $that = $(this);

      if (settings.parent) {
        $(document.body).scrollspy({
          target: settings.parent,
          offset: settings.offset
        });
      }

      $that.affix({
        offset: {
          top: function () {
            var c = $that.offset().top - settings.offset;
            return this.top = c;
          },
          bottom: function () {
            return this.bottom = $(settings.footer).outerHeight(true);
          }
        }
      });
    });
  };

  /**
   * Listen to input changes and update corresponding label(s) accordingly.
   * @param options: checkedClass: the class that will be added when `prop` is true; default: 'checked'
   *                 prop: the property that is read with prop(); default: 'checked'
   */
  $.fn.inputToLabels = function (options) {
    var settings = $.extend({
      checkedClass: 'checked',
      prop: 'checked'
    }, options);
    return this.each(function () {
      var that = $(this);
      var labels = that.find('label');
      labels.each(function () {
        var label = $(this);
        var input = $(label.find('input'));
        input.change(function (e) {
          if ($(this).prop(settings.prop)) {
            labels.removeClass(settings.checkedClass);
            label.addClass(settings.checkedClass);
          }
        });
        if (input.prop(settings.prop))
          label.addClass(settings.checkedClass);
      });
    });
  };

})(jQuery);