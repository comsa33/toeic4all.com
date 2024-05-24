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

document.addEventListener('DOMContentLoaded', function() {
    fetchVocabs(1);
}, false);

let vocabSection = document.getElementById('vocab-section');
let pagination = document.getElementById('pagination');
let questionSection = document.getElementById('question-section');
let vocabularies;

let wrongOnly = false;

function toggleWrongOnly() {
    wrongOnly = !wrongOnly;
    fetchVocabs(1);
}

function fetchVocabs(page) {
    // Remove all current vocabs and pagination
    while (vocabSection.firstChild) {
        vocabSection.removeChild(vocabSection.firstChild);
    }
    while (pagination.firstChild) {
        pagination.removeChild(pagination.firstChild);
    }

    // Fetch and show vocabs and pagination of the specific page
    fetchWithToken(`/api/user_vocabularies?page=${page}&only_wrong=${wrongOnly}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            vocabularies = data.user_vocabularies;  // Save vocabularies for current page

            // Create and append vocab table
            const table = document.createElement('table');
            table.className = 'table';
            const tbody = document.createElement('tbody');
            vocabularies.forEach(vocab => {
                const tr = document.createElement('tr');
                if (vocab.wrong_count > 0) {
                    tr.className = 'wrong-answer';  // Add 'wrong-answer' class if the user has answered this word incorrectly before
                }
                tr.innerHTML = `<td>${vocab.word}</td><td class="vocab-translation">[${vocab.part_of_speech}] ${vocab.translation}</td><td class="button-column"><button class="vocab-question-button" onclick="showQuestion(${vocab.word_id})">관련 문제</button></td>`;
                tbody.appendChild(tr);
            });
            table.appendChild(tbody);
            vocabSection.appendChild(table);

            // Create and append pagination
            let startPage = Math.floor((page - 1) / 10) * 10 + 1;  // Start page number of the current group
            let endPage = startPage + 10;  // End page number of the current group
            if (endPage > data.total_pages) {
                endPage = data.total_pages + 1;  // If the last group has less than 10 pages
            }

            // Add 'previous group' button if necessary
            if (startPage > 1) {
                const li = document.createElement('li');
                li.className = 'page-item';
                li.innerHTML = `<a class="page-link" href="#" onclick="fetchVocabs(${startPage - 1})"><i class="fas fa-chevron-left"></i></a>`;
                pagination.appendChild(li);
            }

            for (let i = startPage; i < endPage; i++) {
                const li = document.createElement('li');
                li.className = 'page-item';
            
                if(i === page) {
                    li.classList.add('active'); // Add 'active' class to the current page
                }
            
                li.innerHTML = `<a class="page-link" href="#" onclick="fetchVocabs(${i})">${i}</a>`;
                pagination.appendChild(li);
            }

            // Add 'next group' button if necessary
            if (endPage <= data.total_pages) {
                const li = document.createElement('li');
                li.className = 'page-item';
                li.innerHTML = `<a class="page-link" href="#" onclick="fetchVocabs(${endPage})"><i class="fas fa-chevron-right"></i></a>`;
                pagination.appendChild(li);
            }
        })
        .catch(error => {
            console.error('There has been a problem with your fetch operation:', error);
        });
}

function showQuestion(wordId) {
    // Clear question section
    while (questionSection.firstChild) {
        questionSection.removeChild(questionSection.firstChild);
    }

    // Find the vocabulary for the clicked wordId in the vocabularies array
    const vocab = vocabularies.find(v => v.word_id === wordId);
    let question = vocab.question_info;

    // Create question div
    let questionDiv = document.createElement('div');
    let vocabList = question.Vocabularies || [];
    let vocabText = '';
    for (let j = 0; j < vocabList.length; j++) {
        vocabText += `<p style="margin-bottom: 0;">    · ${vocabList[j].Word} : [${vocabList[j].POS}] ${vocabList[j].Translation} (${vocabList[j].Explanation})<br>&nbsp&nbsp<예문><br>&nbsp&nbsp&nbsp&nbsp${vocabList[j].Example}<br>&nbsp&nbsp&nbsp&nbsp${vocabList[j].ExampleTranslation}</p>`;
    }
    questionDiv.id = 'question-' + question.QuestionId;
    questionDiv.className = 'col';
    questionDiv.innerHTML = `
        <div class="question-header">
            <!-- 즐찾 버튼 -->
            <button class="favourite-btn" data-question-id="${question.QuestionId}" title="내 즐겨찾기에 추가하기"><i class="fas fa-bookmark"></i></button>
            <!-- 신고 버튼 -->
            <button class="report-btn" data-question-id="${question.QuestionId}" title="문제 리포트 하기"><i class="fas fa-exclamation-triangle"></i></button>
        </div>
        <div class="question-container">
            <p class="p-question-text"><strong>${question.QuestionText}</strong></p>
            <ol id="choices-${question.QuestionId}" class="choice-box" type="A"></ol>
            <p id="result-${question.QuestionId}" class="p-result-text"></p>
            <div id="additional-info-${question.QuestionId}" class="additional-info" style="display: none;">
                <p><strong>'${question.QuestionSubType}' 유형 · ${question.QuestionLevel}단계</strong></p>
                <p>[해석] ${question.Translation}</p>
                <p>[해설] ${question.Explanation}</p>
                <p style="margin-bottom: 0;">[어휘]</p>
                ${vocabText}
            </div>
        </div>
    `;
    questionSection.appendChild(questionDiv);

    // scroll into view
    questionSection.scrollIntoView({behavior: "smooth"});

    // Create choices list
    let choicesOl = document.getElementById("choices-" + question.QuestionId);
    let choices = question.Choices || [];
    for (let j = 0; j < choices.length; j++) {
        let li = document.createElement('li');
        li.innerHTML = `
            <input type="radio" name="choice-${question.QuestionId}" value="${choices[j]}">
            <label for="choice-${choices[j]}">${choices[j]}</label>
        `;
        choicesOl.appendChild(li);

        // Add event listener to the choice
        let input = li.querySelector("input");
        input.addEventListener("change", function() {
            let resultP = document.getElementById("result-" + question.QuestionId);
            let additionalInfoDiv = document.getElementById("additional-info-" + question.QuestionId);
            if (this.value === question.CorrectAnswer) {
                resultP.innerHTML = "정답입니다!";
                resultP.style.color = "rgb(101, 201, 101)";
            } else {
                resultP.innerHTML = "오답입니다.";
                resultP.style.color = "rgb(255, 84, 84)";
            }
            additionalInfoDiv.style.display = "block";
        });
    }

    // Add event listeners to the favourite and report buttons
    let favouriteBtn = questionDiv.querySelector(".favourite-btn");
    let reportBtn = questionDiv.querySelector(".report-btn");

    // Fetch favourite status and color the button accordingly
    fetchWithToken('/api/get_favourite_status?question_id=' + question.QuestionId, {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'favourite') {
            favouriteBtn.classList.add('fav');
            favouriteBtn.style.color = '#ff4a4a';  // Change button color to red
        }
    });

    favouriteBtn.addEventListener("click", function() {
        var question_id = this.getAttribute('data-question-id');

        // Check if button is already marked as favourite
        var isFavourite = this.classList.contains('fav');

        if (isFavourite) {
            // If the question is already in favourites, remove it
            fetchWithToken('/api/favourite/question', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    question_id: question_id
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('즐겨찾기에서 삭제하는 데 실패했습니다: ' + data.error);
                } else {
                    this.classList.remove('fav');
                    this.style.color = 'gray';  // Change button color to gray
                    alert('즐겨찾기에서 성공적으로 삭제되었습니다.');
                }
            });
        } else {
            // If the question is not in favourites, add it
            fetchWithToken('/api/favourite/question', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    question_id: question_id
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('즐겨찾기에 추가하는 데 실패했습니다: ' + data.error);
                } else {
                    this.classList.add('fav');
                    this.style.color = '#ff4a4a';  // Change button color to red
                    alert('즐겨찾기에 성공적으로 추가되었습니다.');
                }
            });
        }
    });

    reportBtn.addEventListener("click", function() {
        var question_id = this.getAttribute('data-question-id');
        var report_content = prompt('리포트 내용을 입력하세요:');
        if (report_content) {
            fetchWithToken('/api/report/question', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    question_id: question_id,
                    report_content: report_content,
                    report_type: 'question'
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error("API request failed: " + response.status);
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    alert('리포트를 보내는 데 실패했습니다: ' + data.error);
                } else {
                    alert('리포트가 성공적으로 전송되었습니다.');
                }
            })
            .catch(error => alert(error));
        }
    });
    document.getElementById('modal-background').style.display = 'block';
    document.getElementById('modal-close-text').style.display = 'block';
    // 애니메이션을 시작합니다.
    setTimeout(function() {
        $('#question-section').addClass('active');
    }, 50);
}

window.onload = function() {
    positionModalCloseText();
}

window.onresize = function() {
    positionModalCloseText();
}

function positionModalCloseText() {
    var modalContent = document.getElementById('question-section');
    var modalCloseText = document.getElementById('modal-close-text');

    // modalContent나 modalCloseText가 null이 아닌지 확인
    if (!modalContent || !modalCloseText) {
        console.log('question-section or modal-close-text not found');
        return;
    }

    var modalContentHeight = modalContent.offsetHeight;
    var modalCloseTextHeight = modalCloseText.offsetHeight;

    var isMobile = window.innerWidth <= 600;

    if (isMobile) {
        // 모바일 화면에서는 question-section가 화면 하단에 위치
        modalCloseText.style.top = "calc(17% - " + (modalContentHeight / 2 + modalCloseTextHeight + 10) + "px)";
    } else {
        // 피씨 화면에서는 question-section가 중앙에 위치
        modalCloseText.style.top = "calc(28% - " + (modalContentHeight / 2 + modalCloseTextHeight + 10) + "px)";
    }
}

$('#modal-background').click(function(e) {
    // 클릭된 요소가 #modal-background인 경우에만 모달을 닫습니다.
    if (e.target.id === 'modal-background') {
        $('#modal-close-text').css('display', 'none');
        $('#question-section').removeClass('active');
        setTimeout(function() {
            $('#modal-background').css('display', 'none');
        }, 500); // 애니메이션이 끝나는 시간과 일치해야 합니다.
    }
});
