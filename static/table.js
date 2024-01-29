fetch('df_merged.json')
    .then(response => response.json())
    .then(data => {
        const tableBody = document.querySelector('#jsonTable tbody');
        data.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `<td>${item.movieId}</td><td>${item.title}</td><td>${item.genres}</td><td>${item.no_of_total_ratings}</td><td>${item.avg_rating}</td><td>${item.score}</td>`;
            tableBody.appendChild(row);
        });

        // Attach the event listeners after the rows have been appended
        document.querySelectorAll('#jsonTable tbody tr').forEach(row => {
            row.addEventListener('click', () => {
                const rowData = Array.from(row.querySelectorAll('td')).map(td => td.innerText);
                const [movieId, title, genres, totalReviews, averageRating, overallScore] = rowData;
        
                fetch('/review', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({movieId, title, genres, totalReviews, averageRating, overallScore}),
                })
                .then(response => response.json())
                .then(data => {
                    console.log('Success:', data);
                    // Convert the data to a string and check if it includes a specific string
                    if (JSON.stringify(data).includes('Existing review found')) {
                        // Redirect the user to the /review page
                        window.location.href = '/review_found';
                    } else {
                        window.location.href = '/review';
                    }
                })
                .catch((error) => {
                    console.error('Error:', error);
                });
            });
        });
    });