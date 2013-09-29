$(document).ready(function() {
    $('.menu-collapsed > .sub-menu').hide();
    $('.menu-main-elem').click(function() {
	console.log('click !');
	$(this).parent().find('.sub-menu').slideToggle();
    });
});
