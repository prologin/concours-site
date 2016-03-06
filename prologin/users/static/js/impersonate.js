$(function () {
  var $id = $('#impersonate-user-id'), $username = $('#impersonate-username');
  $username.typeahead({
    classNames: {menu: 'tt-menu tt-impersonate'},
    limit: 5
  }, {
    name: 'impersonate',
    display: 'username',
    source: function (query, syncResults, asyncResults) {
      $.get(IMPERSONATE_URL + '?q=' + query, function (data) {
          asyncResults(data);
        }
      )
      ;
    },
    templates: {
      empty: '<div class="tt-empty">' + IMPERSONATE_EMPTY + '</div>',
      suggestion: function (data) {
        return data.html;
      }
    }
  }).on('typeahead:select', function (e, data) {
    $id.val(data.id).closest('form').submit();
  });
});