$(document).ready(function() {
    var nb_news = 10;

    (function set_latest_news(offset, nb) {
	var url = '/news/latest/' + offset + '/' + nb + '/';

	$.get(url, function(data) {
	    console.log(data);
	    $('#latest-news').empty();
	    for (var i = 0; i < data.news.length; ++i) {
		var lnk = $('<a href="' + data.news[i].url + '">' + data.news[i].title + '</a>');
		$('#latest-news').append($('<li></li>').append(lnk));
	    }

	    function append_elem(text, activate, offset) {
		var el = $('<li></li>'), lnk = $('<a></a>').attr('href', '#').html(text);

		if (activate) {
		    lnk.click(function(event) {
			event.preventDefault();
			set_latest_news(offset, nb_news);
		    });
		    el.addClass('active');
		} else {
		    lnk.click(function(event) {
			event.preventDefault();
		    });
		    el.addClass('disabled');
		}

		$('#latest-news-pagination').append(el.append(lnk));
	    }

	    $('#latest-news-pagination').empty();
	    //append_elem('&laquo;', offset > 0, 0);
	    var off = 0;
	    for (var i = 1; off < data.total; off += nb_news) {
		console.log(i, off)
		append_elem(i, offset != off, off);
		i++;
	    }
	    off -= nb_news;
	    //append_elem('&raquo;', offset < off, off);
	}, 'json');
    })(0, nb_news);
});
