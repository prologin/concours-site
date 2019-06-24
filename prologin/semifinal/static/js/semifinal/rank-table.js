// Copyright (C) <2016> Association Prologin <association@prologin.org>
// SPDX-License-Identifier: GPL-3.0+

(function ($) {

  var DURATION = 1200,
      OFFSET = 20;

  $.fn.rankingTableUpdate = function (new_rows, animation_done_callback) {

    var $table = $(this), $tbody = $table.find('tbody');

    var rows_up = [], rows_down = [], rows_change_inplace = [];

    // fill row_* arrays with the right data for next step
    $.each(new_rows, function (row_index, row) {
      var row_id = row.id, new_row_html = row.html;

      var $old_row = $table.find(row_id), old_row_index = $old_row.index();

      var diff = old_row_index - row_index;
      var $destination = $tbody.children().eq(row_index);

      if (diff > 0) {
        // goes up
        rows_up.push([$old_row, new_row_html, $destination]);
      } else if (diff < 0) {
        // goes down
        rows_down.push([$old_row, new_row_html, $destination]);
      } else if ($old_row.text() != $(new_row_html).text()) {
        // rows that don't move but change content
        rows_change_inplace.push([$old_row, new_row_html]);
      }

    });

    // generic function to animate a row
    function move_row(data, offset, move_class) {
      var $old_row = $(data[0]), $new_row = $(data[1]), $new_row_pos = $(data[2]);
      var old_pos = $old_row.position(), new_pos = $new_row_pos.position();

      // fade out mutable columns
      $old_row.find('.sb-update').animate({opacity: 0}, DURATION);

      // build the fake row, that  will move
      var $fake_row = $('<div>').css({
        opacity: 0,
        position: 'absolute',
        display: 'block',
        top: old_pos.top,
        left: old_pos.left,
        width: $old_row.width(),
        height: $old_row.height(),
      });
      // insert it in DOM
      $tbody.append($fake_row);
      // build the fake row columns
      var $old_row_tds = $old_row.children();
      $new_row.children().each(function (tdi) {
        var $td = $(this), $old_td = $old_row_tds.eq(tdi);
        var $fake_td = $('<div>').html($td.html()).attr('class', $td.attr('class')).css({
          position: 'absolute',
          display: 'block',
          top: 0,
          bottom: 0,
          left: $old_td.position().left,
          width: $old_td.width(),
          paddingTop: $old_td.css('paddingTop'),
          paddingRight: $old_td.css('paddingRight'),
          paddingBottom: $old_td.css('paddingBottom'),
          paddingLeft: $old_td.css('paddingLeft')
        });
        $fake_row.append($fake_td);
        // clear out mutable data
        $fake_row.find('.sb-update').html('');
        // build the little up/down arrow icon
        $fake_row.children().eq(1).html('<i class="fa ' + move_class + '"></i>');
      });

      // put the right attributes on the soon-to-be new row
      $new_row.data('id', $new_row.attr('id')).attr('id', '').hide().find('.sb-update').css({opacity: 0});
      // and insert it in DOM
      $new_row_pos.after($new_row);
      // hack: add a hidden <tr> so nth-child stays consistent (fuck you CSS)
      $new_row.after($('<tr>').hide());

      // fade out the whole row
      $old_row.children().animate({opacity: 0}, DURATION);
      // fade in the little icon
      $fake_row.children().eq(1).delay(DURATION * 2 + DURATION / 3 * 2).animate({opacity: 0}, DURATION);
      $fake_row
        .animate({opacity: 1, left: '+=' + offset}, DURATION) // move to the side, horizontally
        .delay(DURATION / 3)
        .animate({top: new_pos.top}, DURATION) // move to new location
        .delay(DURATION / 3)
        .animate({left: '-=' + offset}, DURATION) // come back in place, horizontally
        .queue(function() {
          // stealthily show the new row, as if nothing happened, and restore id attribute
          $new_row.show().attr('id', $new_row.data('id')).next().remove(); // remove the nth-child-hack <tr>
          // drop the obsolete row and the fake, moving row
          $old_row.remove();
          $(this).remove();
        });
    }

    var timeout = DURATION * 3 + DURATION / 3 * 2;
    if (!rows_up.length && !rows_down.length) {
      // nothing to move
    }

    $table.addClass('sb-moving');
    // schedule animations for moving rows
    $.each(rows_up, function(i, data) { move_row(data, OFFSET, 'fa-arrow-circle-up text-success'); });
    $.each(rows_down, function(i, data) { move_row(data, -OFFSET, 'fa-arrow-circle-down text-danger'); });
    // rows that stay in place
    $.each(rows_change_inplace, function (i, data) {
      var $old_row = $(data[0]), $new_row = $(data[1]);
      // fade out mutable columns on old row
      $old_row.find('.sb-update')
        .animate({opacity: 0}, DURATION)
        .queue(function () {
          // when animation is done, replace old row with new row (and actually display it)
          $new_row.find('.sb-update').css({opacity: 0});
          $old_row.replaceWith($new_row);
        });
    });

    setTimeout(function() {
      $table.removeClass('sb-moving');
      $tbody.children().each(function(i, tr) {
        $(tr).find('.sb-update').delay(i * 100).animate({opacity: 1}, DURATION);
      });
      if (animation_done_callback)
        animation_done_callback.apply(this);
    }, timeout);

    return this;
  }

})(jQuery);

