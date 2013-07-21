$(document).ready(function() {
    (function set_latest_news(offset, nb) {
	var url = '/news/latest/' + offset + '/' + nb + '/';

	$.get(url, function(data) {
	    console.log(data);
	    $('#latest-news').empty();
	    for (var i = 0; i < data.length; ++i) {
		var lnk = $('<a href="/news/' + data[i].id + '/">' + data[i].title + '</a>');
		$('#latest-news').append($('<li></li>').append(lnk));
	    }
	}, 'json');
    })(0, 5);
});
