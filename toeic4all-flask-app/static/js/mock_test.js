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

window.addEventListener('load', function() {
    const url = '/api/question_types';
    fetchWithToken(url)
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error('API request failed');
            }
        })
        .then(data => {
            const select = document.getElementById('questionType');

            // 기본 선택 항목 추가
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = '모든 문제 유형';
            defaultOption.selected = true;
            select.appendChild(defaultOption);

            // 다른 옵션들 추가
            data.forEach(item => {
                const option = document.createElement('option');
                option.value = item.Id;
                option.textContent = item.NameKor;
                select.appendChild(option);
            });
        })
        .catch(error => console.error('Error:', error));
});

// 객체 초기화
let timerPerQuestion = {};
let totalTimer;
let questionIndex = 0;  // 현재 표시되는 문제 인덱스
let timers = [];  // 문제별 타이머를 저장하는 배열
let startTimes = []; // 문제 시작 시간을 저장하는 배열

// 타이머 함수
function startTimer() {
    return setInterval(function() {
        totalTimer++;
    }, 1000);
}

function stopTimer(timer) {
    clearInterval(timer);
}

// 문제 채점 함수
function gradeQuestion(questionId, correctAnswer) {
    let userAnswerEl = document.querySelector(`input[name="choice-${questionId}"]:checked`);
    let userAnswer = userAnswerEl ? userAnswerEl.value : null;
    return userAnswer === correctAnswer;
}

// 문제 소요 시간 측정 함수
function measureQuestionTime(questionId) {
    let startTime = Date.now();
    return function() {
        let timeTaken = Math.round((Date.now() - startTime) / 1000);
        timerPerQuestion[questionId] = timeTaken;
    };
}

// 총 시간 측정 및 출력 함수
function getTotalTime() {
    let totalTime = 0;
    for (let questionId in timerPerQuestion) {
        totalTime += timerPerQuestion[questionId];
    }
    return totalTime;
}

// 시간을 분:초 형식으로 변환하는 함수
function convertSecondsToMinutes(timeInSeconds) {
    let minutes = Math.floor(timeInSeconds / 60);
    let seconds = timeInSeconds % 60;
    return `${minutes}분 ${seconds}초`;
}

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function generateTestId() {
    // Date and Time part
    let dt = new Date();
    let dtPart = dt.getFullYear().toString() +
        (dt.getMonth() + 1).toString().padStart(2, '0') + 
        dt.getDate().toString().padStart(2, '0') + 
        dt.getHours().toString().padStart(2, '0') + 
        dt.getMinutes().toString().padStart(2, '0') + 
        dt.getSeconds().toString().padStart(2, '0');

    // UUID part (Here assuming a function 'generateUUID()' which returns a UUID)
    let uuidPart = generateUUID();

    return dtPart + '-' + uuidPart;
}

let totalQuestions = 0;

// 모의고사 생성 함수
document.getElementById("generate-mocktest-btn").addEventListener("click", function() {
    document.getElementById('pagination-container').style.display = "none";
    document.getElementById('questionType').style.display = "none";
    document.getElementById('difficultyLevel').style.display = "none";
    document.getElementById('questionCount').style.display = "none";
    document.getElementById('questionTypeDescription').style.display = "flex";
    document.getElementById('difficultyLevelDescription').style.display = "flex";
    document.getElementById('questionCountDescription').style.display = "flex";
    document.getElementById('question-area').innerHTML = '';
    
    // Use this function to set test id
    document.getElementById('test-id').textContent = generateTestId();
    
    let questionArea = document.getElementById('question-area');

    // "새로운 모의고사 풀러가기" 버튼 생성
    let newTestBtn = document.createElement('button');
    newTestBtn.id = 'new-test-btn';
    newTestBtn.textContent = '새로운 모의고사 풀러가기';
    newTestBtn.addEventListener('click', function() {
        // 버튼을 클릭하면 원래 화면으로 돌아갑니다.
        location.reload();
    });
    let startTestBtn = document.getElementById('start-test-btn');
    startTestBtn.parentNode.insertBefore(newTestBtn, startTestBtn);
    
    // "모의고사 생성" 버튼을 숨깁니다.
    this.style.display = 'none';
    
    let typeSelect = document.getElementById("questionType");
    let levelSelect = document.getElementById("difficultyLevel");
    let numInput = document.getElementById("questionCount");
    
    let typeId = typeSelect.value;
    let level = levelSelect.value;
    let num = numInput.value;

    if (num < 1 || num > 30) {
        alert("문제 수는 1개에서 30개 사이로 입력해주세요.");
        location.reload();
        return;
    }

    fetchWithToken(`/api/questions?typeId=${typeId}&level=${level}&num_questions=${num}`)
        .then(response => response.json())
        .then(data => {
            totalQuestions = data.length;

            // 페이지네이션 생성
            let paginationContainer = document.getElementById('pagination-container');

            // 이전 버튼 생성
            let prevButton = document.createElement('div');
            prevButton.id = 'prev-button';
            prevButton.className = 'pagination-button';
            prevButton.innerHTML = '<i class="fas fa-chevron-left"></i>';  // 이전 아이콘
            prevButton.addEventListener('click', function() {
                if (questionIndex > 0) {
                    this.style.color = 'darkgray';  // 클릭 시 색상 변경
                    changeQuestion(questionIndex - 1);
                }
            });
            paginationContainer.appendChild(prevButton);

            for (let i = 0; i < totalQuestions; i++) {
                let div = document.createElement('div');
                div.id = 'pagination-' + (i+1);
                div.className = 'pagination-number';
                div.textContent = i + 1;
                div.addEventListener('click', function() {
                    changeQuestion(i);
                });
                paginationContainer.appendChild(div);
            }

            // 다음 버튼 생성
            let nextButton = document.createElement('div');
            nextButton.id = 'next-button';
            nextButton.className = 'pagination-button';
            nextButton.innerHTML = '<i class="fas fa-chevron-right"></i>';  // 다음 아이콘
            nextButton.addEventListener('click', function() {
                if (questionIndex < totalQuestions - 1) {
                    this.style.color = 'darkgray';  // 클릭 시 색상 변경
                    changeQuestion(questionIndex + 1);
                }
            });
            paginationContainer.appendChild(nextButton);

            for (let i = 0; i < totalQuestions; i++) {
                let questionDiv = document.createElement('div');
                questionDiv.style.display = "none";  // 처음에는 문제를 모두 숨깁니다.
                document.getElementById("start-test-btn").style.display = "block";
                
                // 시험 정보 메시지 업데이트
                let testInfoMsg = document.getElementById('test-info-msg');
                testInfoMsg.style.display = "block";
                testInfoMsg.innerHTML = "AI가 당신의 모의고사를 생성했습니다!";

                // 문제 영역 업데이트
                let vocabList = data[i].Vocabulary;
                let vocabText = '';
                for (let j = 0; j < vocabList.length; j++) {
                    vocabText += `<p style="margin-bottom: 0;">    · ${vocabList[j].Word} : [${vocabList[j].POS}] ${vocabList[j].Translation} (${vocabList[j].Explanation})<br>&nbsp&nbsp<예문><br>&nbsp&nbsp&nbsp&nbsp${vocabList[j].Example}<br>&nbsp&nbsp&nbsp&nbsp${vocabList[j].ExampleTranslation}</p>`;
                }
                questionDiv.id = 'question-' + data[i].QuestionId;
                questionDiv.className = 'col-12 col-md-6';
                questionDiv.innerHTML = `
                    <div class="question-container">
                        <div id="question-timer-container">
                            <p id="timer-${i}" class="question-timer">00:00</p>
                            <p id="recommended-time-${i}" class="recommended-time">(권장시간: ${data[i].RecommendedTime}초)</p>
                        </div>
                        <p class="p-question-text"><strong><span class="question-number">${i+1}</span>. ${data[i].QuestionText}</strong></p>
                        <ol id="choices-${data[i].QuestionId}" class="choice-box" type="A"></ol>
                        <p id="result-${data[i].QuestionId}" style="display: none;">${data[i].CorrectAnswer}</p>
                        <div id="additional-info-${data[i].QuestionId}" class="additional-info" style="display: none;">
                            <div class="time-taken" id="time-taken-${data[i].QuestionId}" style="display: none;"></div>
                            <p><strong>'${data[i].QuestionSubType}' 유형 · ${data[i].QuestionLevel}단계</strong></p>
                            <p>[정답] ${data[i].CorrectAnswer}</p>
                            <p>[해석] ${data[i].Translation}</p>
                            <p>[해설]<br>    ${data[i].Explanation}</p>
                            <p style="margin-bottom: 0;">[어휘]</p>
                            ${vocabText}
                        </div>
                        <!-- 즐찾 버튼 -->
                        <button class="favourite-btn" data-question-id="${data[i].QuestionId}" title="내 오답노트에 추가하기"><i class="fas fa-bookmark"></i></button>
                        <!-- 신고 버튼 -->
                        <button class="report-btn" data-question-id="${data[i].QuestionId}" title="문제 리포트 하기"><i class="fas fa-exclamation-triangle"></i></button>
                    </div>
                `;
                questionArea.appendChild(questionDiv);

                let choicesOl = document.getElementById("choices-" + data[i].QuestionId);
                let choices = data[i].Choices;

                // Randomize the choices
                for (let j = choices.length - 1; j > 0; j--) {
                    const k = Math.floor(Math.random() * (j + 1));
                    [choices[j], choices[k]] = [choices[k], choices[j]];
                }

                for (let j = 0; j < choices.length; j++) {
                    let li = document.createElement('li');
                    let radioInput = document.createElement('input');
                    radioInput.type = 'radio';
                    radioInput.name = `choice-${data[i].QuestionId}`;
                    radioInput.value = choices[j];
                
                    // 문제를 푼 경우 페이지네이션의 색상을 변경
                    radioInput.addEventListener('change', function() {
                        if (this.checked) {
                            let paginationItem = document.getElementById('pagination-' + (i + 1));
                            paginationItem.style.backgroundColor = '#fb7f7c';
                            paginationItem.style.color = '#ffffff';
                        }
                    });
                
                    let label = document.createElement('label');
                    label.htmlFor = `choice-${choices[j]}`;
                    label.textContent = choices[j];
                
                    li.appendChild(radioInput);
                    li.appendChild(label);
                    choicesOl.appendChild(li);
                }
                
                // After the questionDiv has been appended to questionArea
                fetchWithToken('/api/get_favourite_status?question_id=' + data[i].QuestionId, {
                    method: 'GET'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'favourite') {
                        favouriteBtn.classList.add('fav');
                        favouriteBtn.style.color = '#ff4a4a';  // Change button color to red
                    }
                });

                // Attach event handlers after creating the buttons
                let reportBtn = questionDiv.querySelector('.report-btn');
                let favouriteBtn = questionDiv.querySelector('.favourite-btn');

                reportBtn.addEventListener('click', function() {
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

                favouriteBtn.addEventListener('click', function() {
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
            }
            document.getElementById('questionTypeDescription').innerHTML = typeSelect.options[typeSelect.selectedIndex].textContent;
            document.getElementById('difficultyLevelDescription').innerHTML = levelSelect.options[levelSelect.selectedIndex].textContent;
            document.getElementById('questionCountDescription').innerHTML = data.length;
        });
});

// 문제별 타이머 시작 함수
function startQuestionTimer(index) {
    let time = timerPerQuestion[index] || 0;  // 이전에 멈춘 시점부터 시작합니다.
    timers[index] = setInterval(function() {
        let minutes = Math.floor(++time / 60);
        let seconds = time % 60;
        document.getElementById('timer-' + index).innerHTML = (minutes < 10 ? "0" : "") + minutes + ":" + (seconds < 10 ? "0" : "") + seconds;
    }, 1000);
}

// 문제 이동 함수
function changeQuestion(index) {
    // 이전 타이머 멈춤
    if (timers[questionIndex]) {
        clearInterval(timers[questionIndex]);
    }
    let elapsedTime = Math.floor((Date.now() - startTimes[questionIndex]) / 1000);  // 밀리초를 초로 변환
    timerPerQuestion[questionIndex] = (timerPerQuestion[questionIndex] || 0) + elapsedTime;  // 각 문제의 총 소요시간을 저장합니다.

    // 이전 문제를 숨기고 새 문제를 표시합니다.
    document.getElementsByClassName('col-12 col-md-6')[questionIndex].style.display = 'none';
    document.getElementsByClassName('col-12 col-md-6')[index].style.display = 'flex';
    document.getElementsByClassName('question-container')[index].style.display = 'flex';

    questionIndex = index;
    
    // 모든 페이지네이션 아이템에서 'pagination-number-active' 클래스를 제거합니다.
    let paginationItems = document.getElementsByClassName('pagination-number');
    for (let i = 0; i < paginationItems.length; i++) {
        paginationItems[i].classList.remove('pagination-number-active');
    }

    // 현재 페이지네이션 아이템에 'pagination-number-active' 클래스를 추가합니다.
    let currentItem = document.getElementById('pagination-' + (index + 1));
    currentItem.classList.add('pagination-number-active');

    // '이전 문제' 버튼의 표시 상태 업데이트
    if (index == 0) {
        document.getElementById('prev-question-btn').style.display = 'none';
    } else {
        document.getElementById('prev-question-btn').style.display = 'flex';
    }

    // '다음 문제' 버튼의 표시 상태 업데이트
    if (index == totalQuestions - 1) {
        document.getElementById('next-question-btn').style.display = 'none';
    } else {
        document.getElementById('next-question-btn').style.display = 'flex';
    }

    // 새 타이머 시작
    startTimes[questionIndex] = Date.now();
    startQuestionTimer(index);
}

window.addEventListener('load', function() {
    // 시험 시작 버튼 클릭 이벤트
    document.getElementById("start-test-btn").addEventListener("click", function() {
        document.getElementById('pagination-container').style.display = "grid";
        document.getElementById('question-area').style.display = "flex";  // 문제 영역을 보임
        document.getElementById('prev-next-button').style.display = "flex";
        document.getElementById('prev-question-btn').style.display = 'none';
        document.getElementById('grade-test-btn').style.display = "flex";  // 채점하기 버튼을 보임
        this.style.display = "none";  // 시험 시작 버튼을 숨김
        
        // 시험 정보 메시지 업데이트
        document.getElementById('test-info-msg').innerHTML = "시험을 시작했습니다!";
        totalTimer = startTimer();  // 총 시간 측정 시작
        
        // 첫 번째 문제를 보이게 함
        let firstQuestion = document.getElementsByClassName('col-12 col-md-6')[0];
        let firstQuestionContainer = firstQuestion.getElementsByClassName('question-container')[0];
        if (firstQuestion) {
            firstQuestion.style.display = 'block';
            if (firstQuestionContainer) {
                firstQuestionContainer.style.display = 'block';
            }
        }
        
        // 첫 번째 페이지네이션 아이템에 색상을 표시합니다.
        let firstPaginationItem = document.getElementById('pagination-1');
        if (firstPaginationItem) {
            firstPaginationItem.classList.add('pagination-number-active');
        }

        // 첫 번째 문제의 시작 시간을 설정합니다.
        startTimes[0] = Date.now();
        startQuestionTimer(0);
    });

    // 이전 문제 이동 버튼 이벤트
    document.getElementById('prev-question-btn').addEventListener('click', function() {
        if (questionIndex > 0) {
            changeQuestion(questionIndex - 1);
        }
    });

    // 다음 문제 이동 버튼 이벤트
    document.getElementById('next-question-btn').addEventListener('click', function() {
        if (questionIndex < totalQuestions - 1) {
            changeQuestion(questionIndex + 1);
        }
    });
});

// 채점 버튼 클릭 이벤트
window.addEventListener('load', function() {
    document.getElementById("grade-test-btn").addEventListener("click", function() {
        // 이전 타이머 멈춤
        if (timers[questionIndex]) {
            clearInterval(timers[questionIndex]);
        }
        let elapsedTime = Math.floor((Date.now() - startTimes[questionIndex]) / 1000);  // 밀리초를 초로 변환
        timerPerQuestion[questionIndex] = (timerPerQuestion[questionIndex] || 0) + elapsedTime;  // 타이머 값을 저장합니다.
        
        // 모든 타이머 종료
        for (let i = 0; i < timers.length; i++) {
            if (timers[i]) {
                clearInterval(timers[i]);
            }
        }
        // 타이머 컨테이너를 안보이게 합니다.
        let timerContainers = document.getElementsByClassName('question-timer');
        for (let i = 0; i < timerContainers.length; i++) {
            timerContainers[i].style.display = 'none';
        }
        
        stopTimer(totalTimer);  // 총 시간 측정 종료
        
        let correctCount = 0;
        let totalQuestions = document.getElementsByClassName('question-container').length;
        let notAnsweredCount = 0;
        let notViewedCount = 0;

        for (let i = 0; i < totalQuestions; i++) {
            let questionId = document.getElementsByClassName('col-12 col-md-6')[i].id.split('-')[1];
            if (!document.querySelector(`input[name="choice-${questionId}"]:checked`)) {
                notAnsweredCount++;
                // 시간이 기록되지 않았다면, 사용자가 문제를 아예 확인하지 않은 것으로 판단합니다.
                if (!timerPerQuestion[i]) {
                    notViewedCount++;
                }
            }
        }
        
        // 확인하지 않은 문제에 대한 경고 메시지를 생성합니다.
        let warningMessage = '';
        let needToConfirm = false;
        
        if (notViewedCount > 0) {
            warningMessage += `아직 ${notViewedCount}개의 문제를 아예 확인하지 않았습니다. `;
            warningMessage += `확인하지 않은 문제는 채점되지 않으며, 데이터가 저장되지 않아 추후 분석이나 오답노트에서 확인하실 수 없습니다. `;
            needToConfirm = true;
        }
        // 선택하지 않은 문제에 대한 경고 메시지를 생성합니다.
        if (notAnsweredCount > notViewedCount) {
            warningMessage += `답을 선택하지 않은 문제가 ${notAnsweredCount - notViewedCount}개 있습니다. `;
            warningMessage += `답을 선택하지 않은 문제는 틀린 것으로 간주되어 채점됩니다. `;
            needToConfirm = true;
        }
        
        if (needToConfirm) {
            warningMessage += `그래도 채점하시겠습니까?`;
        
            if (!confirm(warningMessage)) {
                return;  // 채점하지 않고 종료합니다.
            }
        }

        // 채점 완료 후 API 호출하여 사용자의 시험 정보를 저장합니다.
        let wrongCount = totalQuestions - correctCount;
        let testId = document.getElementById('test-id').textContent;
        let testTypeElement = document.getElementById('questionType');
        let testType = testTypeElement.selectedOptions[0].textContent;
        let testLevelElement = document.getElementById('difficultyLevel');
        let testLevel = testLevelElement.selectedOptions[0].textContent;
        let timeRecord = getTotalTime();  // 전체 소요 시간을 초로 환산합니다.

        let data = {
            test_id: testId,
            test_type: testType,
            test_level: testLevel,
            question_count: totalQuestions - notViewedCount,
            wrong_count: wrongCount,
            time_record: timeRecord
        };

        fetchWithToken('/api/user-test-detail', {
            method: 'POST',
            body: JSON.stringify(data),
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(json => {
            console.log(json);
            let testId = json.test_detail_id;
            
            // 문제를 채점하고 결과를 저장합니다.
            let questionDetailsData = [];

            for (let i = 0; i < totalQuestions; i++) {
                let questionId = document.getElementsByClassName('col-12 col-md-6')[i].id.split('-')[1];
                let correctAnswer = document.getElementById('result-' + questionId).textContent;

                let isCorrect = gradeQuestion(questionId, correctAnswer);
                
                if (isCorrect) {
                    correctCount++;
                    document.getElementById('pagination-' + (i + 1)).style.backgroundColor = 'rgb(101, 201, 101)';
                } else {
                    document.getElementById('pagination-' + (i + 1)).style.backgroundColor = 'rgb(255, 109, 109)';
                }
                
                // 문제별 소요 시간 기록
                let timeTakenDiv = document.getElementById('time-taken-' + questionId);
                let timeTaken = timerPerQuestion[i];
                if (timeTakenDiv && timeTaken) {
                    timeTakenDiv.style.display = 'block';
                    timeTakenDiv.textContent = `${(i + 1)}번 문제 소요시간: ${convertSecondsToMinutes(timeTaken)}`;
                }
                
                // 문제의 추가 정보 표시
                let additionalInfoDiv = document.getElementById('additional-info-' + questionId);
                if (additionalInfoDiv) {
                    additionalInfoDiv.style.display = 'block';
                }

                // 문제를 풀지 않았다면 API 요청에 포함하지 않습니다.
                if (timeTaken) {
                    questionDetailsData.push({
                        test_id: testId,
                        question_id: questionId,
                        is_correct: isCorrect,
                        time_record_per_question: timeTaken
                    });
                }
            }

            // 모든 문제 세부 정보를 한 번의 요청으로 API에 보냅니다.
            fetchWithToken('/api/test-question-detail', {
                method: 'POST',
                body: JSON.stringify({question_details: questionDetailsData}),
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(json => console.log(json))
            .catch(error => console.log('Error:', error));
        })
        .catch(error => console.log('Error:', error));
                
        this.style.display = 'none';  // 채점 버튼 숨김
        document.getElementById('mynote-btn').style.display = "flex";
        document.getElementById('test-result').innerHTML = `점수: ${correctCount}/${totalQuestions} · 시간: ${convertSecondsToMinutes(getTotalTime())}`;
        document.getElementById('test-result').style.display = "flex";  // 채점 결과를 보임
    });
});
