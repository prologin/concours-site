const applicants = document.getElementsByClassName('applicant-head');

function goToApplicant(applicant) {
    // Unfold an applicant's description, and scroll down toward its position
    applicant.classList.add('selected');

    // Scroll to get out of the header
    setTimeout(function() {
        applicant.scrollIntoView();
        let scrolledY = window.scrollY;
        window.scroll(0, scrolledY - 10);
    }, 1);
}

/**
 * If there is an anchor to the page, open corresponding applicant and scroll
 * to it.
 */
const url_parts = document.URL.split('#');

if (url_parts.length > 1) {
    const focused_id = url_parts[1];
    const focused_el = document.getElementById(focused_id);
    goToApplicant(focused_el);
}

/**
 * Swap the active status when clicking on an applicant
 */
for (let i = 0 ; i < applicants.length ; i++) {
    applicants[i].addEventListener('click', (event) => {
        const applicant = applicants[i].parentElement;

        if (applicant.classList.contains('selected'))
            applicant.classList.remove('selected');
        else
            applicant.classList.add('selected');
    });
}

/**
 * Close all details when hitting escape
 */
document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape')
        for (let i = 0 ; i < applicants.length ; i++)
            applicants[i].parentElement.classList.remove('selected');
});

/**
 * Select next item when pressing `down` arrow
 */
document.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowDown') {
        event.preventDefault();

        let last_opened = -1;

        for (let i = 0 ; i < applicants.length ; i++)
            if (applicants[i].parentElement.classList.contains('selected'))
                last_opened = i;

        if (last_opened != -1)
            applicants[last_opened].parentElement.classList.remove('selected');
        if (last_opened != applicants.length - 1)
            goToApplicant(applicants[last_opened + 1].parentElement);
    }
});

/**
 * Select previous item when pressing `up` arrow
 */
document.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowUp') {
        event.preventDefault();

        let last_opened = applicants.length;

        for (let i = applicants.length-1 ; i >= 0 ; i--)
            if (applicants[i].parentElement.classList.contains('selected'))
                last_opened = i;

        if (last_opened != applicants.length)
            applicants[last_opened].parentElement.classList.remove('selected');
        if (last_opened != 0)
            goToApplicant(applicants[last_opened - 1].parentElement);
    }
});
