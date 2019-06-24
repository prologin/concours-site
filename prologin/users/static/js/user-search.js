// Copyright (C) <2016> Association Prologin <association@prologin.org>
// SPDX-License-Identifier: GPL-3.0+

$(function () {
  let $username = $('#search-user-name');
  $username.typeahead({
    classNames: {menu: 'tt-menu tt-user-search'},
    limit: 5
  }, {
    name: 'search',
    display: 'username',
    source: function (query, syncResults, asyncResults) {
      $.get(SEARCH_USER_URL + '?q=' + query, function (data) {
          asyncResults(data);
        }
      )
      ;
    },
    templates: {
      empty: '<div class="tt-empty">' + SEARCH_USER_EMPTY + '</div>',
      suggestion: function (data) {
        return data.html;
      }
    }
  }).on('typeahead:select', function (e, data) {
    window.location = data.url;
  });
});