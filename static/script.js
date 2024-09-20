document.addEventListener('DOMContentLoaded', function () {
    const searchForm = document.getElementById('searchForm');
    const messageList = document.getElementById('messageList');
    const prevPageButtonTop = document.getElementById('prevPageButtonTop');
    const nextPageButtonTop = document.getElementById('nextPageButtonTop');
    const firstPageButtonTop = document.getElementById('firstPageButtonTop');
    const lastPageButtonTop = document.getElementById('lastPageButtonTop');
    const prevPageButtonBottom = document.getElementById('prevPageButtonBottom');
    const nextPageButtonBottom = document.getElementById('nextPageButtonBottom');
    const firstPageButtonBottom = document.getElementById('firstPageButtonBottom');
    const lastPageButtonBottom = document.getElementById('lastPageButtonBottom');
    const translationInfo = document.getElementById('translationInfo');

    let currentPage = 1;
    let totalPages = 1;
    let currentSearchQuery = '';
    let currentLanguages = [];
    let translations = [];

    function updateDisplayedResults(results) {
        let listItemsHTML = '';
        for (const result of results) {
            const senderStyle = result.sender_color ? `style="color: #${result.sender_color}"` : '';
            listItemsHTML += `
                <li>
                    <p><strong>Message ID:</strong> ${result.message_id}</p>
                    <p><strong>Date:</strong> ${result.date}</p>
                    <p><strong>Sender:</strong> <span ${senderStyle}>${result.sender}</span> (${result.sender_type})</p>
                    <p><strong>Content:</strong> ${result.content}</p>
                    ${result.post_url ? `<p><a href="${result.post_url}" target="_blank">View Original Post</a></p>` : ''}
                </li>
            `;
        }
        messageList.innerHTML = listItemsHTML || '<li>No results found.</li>';
    }
    
    function updatePagination() {
        const pageNumbersTop = document.getElementById('pageNumbersTop');
        const pageNumbersBottom = document.getElementById('pageNumbersBottom');
        pageNumbersTop.innerHTML = '';
        pageNumbersBottom.innerHTML = '';

        const maxVisiblePages = 5; // Max number of page buttons visible
        let range = [];

        if (totalPages <= maxVisiblePages) {
            range = createRange(1, totalPages);
        } else {
            if (currentPage <= Math.floor(maxVisiblePages / 2)) {
                range = createRange(1, maxVisiblePages - 1);
                range.push('...');
                range.push(totalPages);
            } else if (currentPage >= totalPages - Math.floor(maxVisiblePages / 2)) {
                range.push(1);
                range.push('...');
                range = range.concat(createRange(totalPages - (maxVisiblePages - 2), totalPages));
            } else {
                range.push(1);
                range.push('...');
                range = range.concat(createRange(currentPage - 1, currentPage + 1));
                range.push('...');
                range.push(totalPages);
            }
        }

        range.forEach(item => {
            if (item === '...') {
                pageNumbersTop.appendChild(createEllipsis());
                pageNumbersBottom.appendChild(createEllipsis());
            } else {
                addPageNumber(item, pageNumbersTop);
                addPageNumber(item, pageNumbersBottom);
            }
        });

        firstPageButtonTop.disabled = currentPage === 1;
        prevPageButtonTop.disabled = currentPage === 1;
        nextPageButtonTop.disabled = currentPage === totalPages;
        lastPageButtonTop.disabled = currentPage === totalPages;

        firstPageButtonBottom.disabled = currentPage === 1;
        prevPageButtonBottom.disabled = currentPage === 1;
        nextPageButtonBottom.disabled = currentPage === totalPages;
        lastPageButtonBottom.disabled = currentPage === totalPages;
    }

    function createRange(start, end) {
        return Array.from({ length: end - start + 1 }, (_, i) => start + i);
    }

    function addPageNumber(pageNum, container) {
        const pageNumber = document.createElement('button');
        pageNumber.classList.add('page-number');
        if (pageNum === currentPage) {
            pageNumber.classList.add('active');
        }
        pageNumber.textContent = pageNum;
        pageNumber.addEventListener('click', () => goToPage(pageNum));
        container.appendChild(pageNumber);
    }

    function createEllipsis() {
        const ellipsis = document.createElement('span');
        ellipsis.classList.add('ellipsis');
        ellipsis.textContent = '...';
        return ellipsis;
    }

    function goToPage(page) {
        if (page >= 1 && page <= totalPages && page !== currentPage) {
            currentPage = page;
            performSearch(currentSearchQuery, currentLanguages, currentPage);
        }
    }

    async function performSearch(searchQuery, languages, page = 1) {
        try {
            const response = await fetch('/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    q: searchQuery,
                    languages: languages,
                    page: page
                })
            });

            if (!response.ok) {
                throw new Error('Failed to fetch search results.');
            }

            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }

            updateDisplayedResults(data.results);
            totalPages = data.total_pages;
            currentPage = data.page;
            updatePagination();

            // Update the translation info display
            let translationDisplay = `Input: ${searchQuery}`;
            translations.forEach(translation => {
                translationDisplay += `   -   ${translation.lang}: ${translation.translated}`;
            });
            translationInfo.textContent = translationDisplay;

        } catch (error) {
            console.error('Error fetching search results:', error);
            messageList.innerHTML = `<li>Error fetching search results: ${error.message}</li>`;
        }
    }

    searchForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const searchQuery = document.getElementById('searchQuery').value.trim();
        const selectedLanguages = Array.from(document.querySelectorAll('#languageOptions input:checked'))
            .map(checkbox => checkbox.value);

        if (searchQuery === '') {
            return;
        }

        currentSearchQuery = searchQuery;
        currentLanguages = selectedLanguages;
        currentPage = 1;

        // Fetch translations for each selected language
        translations = await Promise.all(
            selectedLanguages.map(async lang => {
                const translated = await translateSearchQuery(searchQuery, lang);
                return { lang: lang, translated: translated };
            })
        );

        await performSearch(searchQuery, selectedLanguages);
    });

    async function translateSearchQuery(query, targetLang) {
        try {
            const response = await fetch('/translate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: query,
                    target_lang: targetLang
                })
            });

            if (!response.ok) {
                throw new Error(`Failed to translate query to ${targetLang}.`);
            }

            const data = await response.json();
            return data.translated_text;
        } catch (error) {
            console.error(`Error translating query: ${error.message}`);
            return query; // Fallback to original query
        }
    }

    prevPageButtonTop.addEventListener('click', () => goToPage(currentPage - 1));
    nextPageButtonTop.addEventListener('click', () => goToPage(currentPage + 1));
    firstPageButtonTop.addEventListener('click', () => goToPage(1));
    lastPageButtonTop.addEventListener('click', () => goToPage(totalPages));

    prevPageButtonBottom.addEventListener('click', () => goToPage(currentPage - 1));
    nextPageButtonBottom.addEventListener('click', () => goToPage(currentPage + 1));
    firstPageButtonBottom.addEventListener('click', () => goToPage(1));
    lastPageButtonBottom.addEventListener('click', () => goToPage(totalPages));
});