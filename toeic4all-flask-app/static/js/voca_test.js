function isTokenExpired(token) {
    if (!token) {
        return true;
    }
    const jwtToken = JSON.parse(atob(token.split('.')[1]));
    // Checking if the token is expired.
    if (!jwtToken.exp || Date.now() >= jwtToken.exp * 1000) {
        return true;
    }
    return false;
}

function fetchWithToken(url, options = {}) {
    const jwtToken = localStorage.getItem('access_token');
    if (jwtToken) {
        if (isTokenExpired(jwtToken)) {
            localStorage.removeItem('access_token');
            alert('세션이 만료되었습니다. 다시 로그인해 주세요.');
            window.location.href = "/user/login";
            return;
        }

        let headers = options.headers || {};
        headers['Authorization'] = `Bearer ${jwtToken}`;
        return fetch(url, {...options, headers});
    } else {
        alert('세션이 만료되었습니다. 다시 로그인해 주세요.');
        window.location.href = "/user/login";
        return;
    }
}

// 페이지 초기화
let vocabularies = [];
let currentVocabulary = 0;
let answerChecked = false;

// 페이지 번호 업데이트
let page = 1;
function loadVocabularies() {
    fetchWithToken(`/api/vocabularies?page=${page}`)
        .then(response => response.json())
        .then(data => {
            vocabularies = data.vocabularies;
            currentVocabulary = 0;
            displayVocabulary();
        });
}

function displayVocabulary() {
    let vocaContainer = document.getElementById('voca-test-container');
    let vocabulary = vocabularies[currentVocabulary];

    // 초기화
    vocaContainer.innerHTML = '';

    // 단어와 선택지를 묶는 컨테이너 생성
    let vocaQuestionContainer = document.createElement('div');
    vocaQuestionContainer.className = 'voca-container';

    let wordElement = document.createElement('h2');
    wordElement.textContent = vocabulary.word;
    vocaQuestionContainer.appendChild(wordElement);

    // 임의의 순서로 답안 배치
    let answers = [...vocabulary.wrong_translations, vocabulary.translation];
    answers.sort(() => Math.random() - 0.5);

    answers.forEach(answer => {
        let answerElement = document.createElement('button');
        answerElement.textContent = answer;
        answerElement.classList.add('answer-button');
        answerElement.addEventListener('click', function() {
            checkAnswer(answer);
            this.disabled = true;
        });
        vocaQuestionContainer.appendChild(answerElement);
    });

    let passElement = document.createElement('button');
    passElement.textContent = "모르겠음";
    passElement.classList.add('answer-button');
    passElement.addEventListener('click', function() {
        checkAnswer(null);
        this.disabled = true;
    });
    vocaQuestionContainer.appendChild(passElement);

    // 컨테이너를 vocaContainer에 추가
    vocaContainer.appendChild(vocaQuestionContainer);

    let nextElement = document.createElement('button');
    nextElement.textContent = "다음 단어";
    nextElement.addEventListener('click', function() {
        if (answerChecked) {
            nextVocabulary();
        } else {
            alert("답을 체크해주세요.");
        }
    });
    vocaContainer.appendChild(nextElement);
}

function checkAnswer(answer) {
    let correct = (answer === vocabularies[currentVocabulary].translation);
    let messageElement = document.createElement('h3');
    messageElement.innerHTML = correct ? "<i class='fas fa-check' style='color:green;'></i>&nbsp;&nbsp;정답입니다" : "<i class='fas fa-times' style='color:red;'></i>&nbsp;&nbsp;오답입니다";
    document.getElementById('voca-test-container').appendChild(messageElement);

    let answerElements = document.querySelectorAll('.answer-button');  // 클래스를 기반으로 선택
    answerElements.forEach(answerElement => {
        if (answerElement.textContent === vocabularies[currentVocabulary].translation) {
            answerElement.style.color = 'green';
        }
        answerElement.disabled = true;
    });

    fetchWithToken('/api/user_vocabularies', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            word_id: vocabularies[currentVocabulary].id,
            wrong_count: correct ? 0 : 1
        })
    });
    answerChecked = true;
}

function nextVocabulary() {
    if (currentVocabulary < vocabularies.length - 1) {
        currentVocabulary += 1;
        displayVocabulary();
    } else {
        page += 1;
        loadVocabularies();
    }
    answerChecked = false;
}

loadVocabularies();
