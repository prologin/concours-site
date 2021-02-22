(function () {

    let $thread = $('#search-thread-name');

    function relocate(event, query) {
      var NEW_URL = SEARCH_THREAD_URL + "?q=" + query
      document.location.replace(NEW_URL)
    }

    thread.onkeypress = function(event) {
      if(event.key == "Enter") {
        var value = thread.value;
        relocate(event, value)
      }
    }

})();