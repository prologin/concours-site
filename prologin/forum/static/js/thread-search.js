(function () {

    let $thread = $('#search-thread-name');

    $thread.typeahead({
        classNames: {menu: 'tt-menu tt-user-search'},
        limit: 5
      }, {
        name: 'search',
        display: 'threadname',
        source: function (query, syncResults, asyncResults) {
          $.get(SEARCH_THREAD_URL + '?q=' + query, function (data) {
              asyncResults(data);
            }
          )
          ;
        },
        templates: {
          empty: '<div class="tt-empty">' + SEARCH_THREAD_EMPTY + '</div>',
          suggestion: function (data) {
            return data.html;
          }
        }
      }).on('typeahead:select', function (e, data) {
        window.location = data.url;
      });

})();