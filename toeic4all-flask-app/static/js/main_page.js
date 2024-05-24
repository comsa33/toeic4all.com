window.onload = function() {
    let apiData = null;
    
    const countdownElement = document.createElement('div');
    countdownElement.id = 'countdown';
    countdownElement.style.position = 'absolute';
    countdownElement.style.right = '20px';
    countdownElement.style.top = '20px';
    countdownElement.style.fontSize = '17px';
    countdownElement.style.fontWeight = '200';
    document.getElementById('my-img-container').appendChild(countdownElement);

    function updateCountdown() {
        if (!apiData) {
            fetch('/api/toeic-info')
                .then(response => response.json())
                .then(data => {
                    apiData = data;
                    updateCountdown();  // call this function again to update countdown immediately
                })
                .catch(error => {
                    countdownElement.innerHTML = '토익 시험 정보를 가져오는 데 실패했습니다.';
                });
        } else {
            const now = new Date();
            // Adjust UTC time to Korea Time (UTC +9)
            const nextExam = new Date(apiData.results[0].toeic_test_datetime + 'Z');
            nextExam.setHours(nextExam.getHours() - 9);  // add 9 hours to adjust to Korea Time
            const diff = Math.max((nextExam - now) / 1000, 0);  // remaining time in seconds

            if (diff === 0) {
                apiData = null;  // reset apiData so that the next API call will be made
                return;  // exit this function immediately
            }

            const days = Math.floor(diff / 86400).toString().padStart(2, '0');
            const hours = (Math.floor(diff / 3600) % 24).toString().padStart(2, '0');
            const minutes = (Math.floor(diff / 60) % 60).toString().padStart(2, '0');
            const seconds = (Math.floor(diff % 60)).toString().padStart(2, '0');

            countdownElement.innerHTML = 
                `<p style="font-size:0.7em; margin-bottom: 5px;">다음 토익 시험 (${apiData.results[0].toeic_test_no} 회차) 까지</p>` +
                `<span>${days}일 ${hours}시간 ${minutes}분 ${seconds}초</span>`;
        }
    }
    
    updateCountdown();
    setInterval(updateCountdown, 1000);  // update every second
};
