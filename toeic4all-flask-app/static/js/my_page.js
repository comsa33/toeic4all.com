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

window.onload = function() {
    fetchWithToken('/api/favourite_questions')
    .then(response => response.json())
    .then(data => {
        let questionArea = document.getElementById('question-area');
        for (let i = 0; i < data.length; i++) {
            let questionDiv = document.createElement('div');
            let vocabList = data[i].Vocabularies || [];
            let vocabText = '';
            for (let j = 0; j < vocabList.length; j++) {
                vocabText += `<p style="margin-bottom: 0;">    · ${vocabList[j].Word} : [${vocabList[j].POS}] ${vocabList[j].Translation} (${vocabList[j].Explanation})<br>&nbsp&nbsp<예문><br>&nbsp&nbsp&nbsp&nbsp${vocabList[j].Example}<br>&nbsp&nbsp&nbsp&nbsp${vocabList[j].ExampleTranslation}</p>`;
            }
            questionDiv.id = 'question-' + data[i].QuestionId;
            questionDiv.className = 'col-12 col-md-6';
            questionDiv.innerHTML = `
                <div class="question-container">
                    <p class="p-question-text"><strong><span class="question-number">${i+1}</span>. ${data[i].QuestionText}</strong></p>
                    <ol id="choices-${data[i].QuestionId}" class="choice-box" type="A"></ol>
                    <p id="result-${data[i].QuestionId}" class="p-result-text"></p>
                    <div id="additional-info-${data[i].QuestionId}" class="additional-info" style="display: none;">
                        <p><strong>'${data[i].QuestionSubType}' 유형 · ${data[i].QuestionLevel}단계</strong></p>
                        <p>[해석] ${data[i].Translation}</p>
                        <p>[해설] ${data[i].Explanation}</p>
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
            let choices = data[i].Choices || [];

            // Randomize the choices
            for (let j = choices.length - 1; j > 0; j--) {
                const k = Math.floor(Math.random() * (j + 1));
                [choices[j], choices[k]] = [choices[k], choices[j]];
            }

            for (let j = 0; j < choices.length; j++) {
                let li = document.createElement('li');
                li.innerHTML = `
                    <input type="radio" name="choice-${data[i].QuestionId}" value="${choices[j]}">
                    <label for="choice-${choices[j]}">${choices[j]}</label>
                `;
                choicesOl.appendChild(li);

                // 이벤트 리스너 추가
                let input = li.querySelector("input");
                input.addEventListener("change", function() {
                    let resultP = document.getElementById("result-" + data[i].QuestionId);
                    let additionalInfoDiv = document.getElementById("additional-info-" + data[i].QuestionId);
                    if (this.value === data[i].CorrectAnswer) {
                        resultP.innerHTML = "정답입니다!";
                        resultP.style.color = "rgb(101, 201, 101)";
                    } else {
                        resultP.innerHTML = "오답입니다! 정답은 " + data[i].CorrectAnswer + "입니다.";
                        resultP.style.color = "rgb(255, 109, 109)";
                    }
                    additionalInfoDiv.style.display = "block";
                });
            }

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

            favouriteBtn.style.color = '#ff4a4a';
            favouriteBtn.addEventListener('click', function() {
                var question_id = this.getAttribute('data-question-id');
                fetchWithToken('/api/favourite/question', {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        question_id: question_id
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
                        alert('즐겨찾기에서 삭제하는 데 실패했습니다: ' + data.error);
                    } else {
                        this.style.color = 'gray';
                        alert('즐겨찾기에서 성공적으로 삭제되었습니다.');
                        var questionElement = document.getElementById('question-' + question_id);
                        questionElement.parentNode.removeChild(questionElement);
                    }
                })
                .catch(error => alert(error));
            });
        }
        return data.map(question => question.QuestionId).join(',');
    })
    .catch(error => alert(error))
};
