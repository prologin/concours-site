const applicants = document.getElementsByClassName('applicant-head');

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
document.addEventListener('keypress', (event) => {
    if (event.key === 'Escape')
        for (let i = 0 ; i < applicants.length ; i++)
            applicants[i].parentElement.classList.remove('selected');
});

/**
 * Select next item when pressing `down` arrow
 */
document.addEventListener('keypress', (event) => {
    if (event.key === 'ArrowDown') {
        let last_opened = -1;

        for (let i = 0 ; i < applicants.length ; i++)
            if (applicants[i].parentElement.classList.contains('selected'))
                last_opened = i;

        if (last_opened != -1)
            applicants[last_opened].parentElement.classList.remove('selected');

        applicants[last_opened + 1].parentElement.classList.add('selected');
    }
});

/**
 * Select previous item when pressing `up` arrow
 */
document.addEventListener('keypress', (event) => {
    if (event.key === 'ArrowUp') {
        let last_opened = applicants.length;

        for (let i = applicants.length-1 ; i >= 0 ; i--)
            if (applicants[i].parentElement.classList.contains('selected'))
                last_opened = i;

        if (last_opened != applicants.length)
            applicants[last_opened].parentElement.classList.remove('selected');

        applicants[last_opened - 1].parentElement.classList.add('selected');
    }
});
