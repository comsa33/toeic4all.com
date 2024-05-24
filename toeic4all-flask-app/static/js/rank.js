function fetchWithToken(url, options = {}) {
    const jwtToken = localStorage.getItem('access_token');
    if (jwtToken) {
        let headers = options.headers || {};
        headers['Authorization'] = `Bearer ${jwtToken}`;
        return fetch(url, {...options, headers});
    } else {
        return;
    }
}

window.addEventListener('DOMContentLoaded', (event) => {
    const jwtToken = localStorage.getItem('access_token');
    if (jwtToken) {
        // 로그인된 사용자의 이름을 가져옵니다.
        fetchWithToken('/user/status')
            .then(response => response.json())
            .then(status => {
                if (status.status === 'logged_in') {
                    // 로그인된 사용자의 이름을 전역 변수로 저장합니다.
                    window.loggedInUsername = status.username;
                }
            })
            .catch(error => {
                console.error(error);
            });
    }

    // 문제 유형을 가져와서 선택박스에 추가합니다.
    fetch('/api/question_types')
        .then(response => response.json())
        .then(questionTypes => {
            const selection = document.getElementById('question-type-selection');
            questionTypes.forEach(questionType => {
                const option = document.createElement('option');
                option.value = questionType.Id;
                option.textContent = questionType.NameKor;
                selection.appendChild(option);
            });
        });

    // 선택박스의 선택이 변경될 때마다 랭킹 데이터를 가져옵니다.
    document.getElementById('question-type-selection').addEventListener('change', (event) => {
        const questionTypeId = event.target.value;
        fetch('/api/ranking' + (questionTypeId ? '/' + questionTypeId : ''))
            .then(response => response.json())
            .then(ranking => {
                ranking.forEach((userRanking, index) => {
                    userRanking.rank = index + 1;
                });
                return ranking;
            })
            .then(updateTable);
    });

    // 페이지 로딩 완료 후, 초기 랭킹 데이터를 가져옵니다.
    document.getElementById('question-type-selection').dispatchEvent(new Event('change'));
});

// 랭킹 데이터 프로퍼티와 헤더 텍스트 매핑
const headers = {
    '순위': null,
    '아이디': null,
    '성적': 'accuracy_score',
    '기여도': 'activity_score',
    '난이도': 'difficulty_score',
    '종합점수': 'final_score'
};

let sortOrder = -1; // 초기 정렬 순서를 내림차순으로 설정

// 랭킹 데이터를 테이블에 추가하고 정렬하는 함수
function updateTable(ranking, sortKey = null) {
    const jwtToken = localStorage.getItem('access_token');
    const table = document.getElementById('rank-table');
    table.innerHTML = ''; // 기존의 랭킹 데이터를 비웁니다.

    // 테이블 헤더를 추가합니다.
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    Object.entries(headers).forEach(([headerText, key]) => {
        const th = document.createElement('th');
        th.textContent = headerText;
        if (key) {
            th.classList.add('sortable'); 
            th.addEventListener('click', () => {
                sortOrder *= -1; // 정렬 순서를 토글
                updateTable(ranking, key);
            });
        }
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // 랭킹 데이터를 테이블에 추가합니다.
    const tbody = document.createElement('tbody');
    if (sortKey) {
        ranking = [...ranking].sort((a, b) => sortOrder * (a[sortKey] - b[sortKey]));
    }
    const top30Ranking = ranking.slice(0, 30);
    const currentUserRanking = ranking.find(userRanking => jwtToken && userRanking.username === window.loggedInUsername);

    const addRow = (userRanking, highlight = false) => {
        const tr = document.createElement('tr');

        // 로그인된 사용자의 행이면 색상을 변경합니다.
        if (highlight && jwtToken && userRanking.username === window.loggedInUsername) {
            tr.className = 'highlight';
        }

        [
            userRanking.rank,
            userRanking.username,
            Number(userRanking.accuracy_score).toFixed(2),
            userRanking.activity_score.toFixed(2),
            Number(userRanking.difficulty_score).toFixed(2),
            userRanking.final_score.toFixed(2)
        ].forEach(text => {
            const td = document.createElement('td');
            td.textContent = text;
            tr.appendChild(td);
        });

        tbody.appendChild(tr);
    };

    top30Ranking.forEach((userRanking) => {
        addRow(userRanking, userRanking === currentUserRanking);
    });
    

    // 랭킹이 30위를 넘어가는 경우, 사용자에게 알립니다.
    if (ranking.length > 30) {
        const tr = document.createElement('tr');
        const td = document.createElement('td');
        td.colSpan = 6;
        td.textContent = '...';
        tr.appendChild(td);
        tbody.appendChild(tr);
    }

    // 로그인된 사용자가 30위 밖에 있다면, 그 사용자의 행을 추가합니다.
    if (currentUserRanking && !top30Ranking.includes(currentUserRanking)) {
        addRow(currentUserRanking, true);

        const tr = document.createElement('tr');
        const td = document.createElement('td');
        td.colSpan = 6;
        td.textContent = '...';
        tr.appendChild(td);
        tbody.appendChild(tr);
    }

    table.appendChild(tbody);
}
