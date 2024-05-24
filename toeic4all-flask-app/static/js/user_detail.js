var username; // Global variable to store the username

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

function getDaysSinceJoined(dateString) {
    var joinedDate = new Date(dateString);
    var currentDate = new Date();
    var timeDiff = Math.abs(currentDate.getTime() - joinedDate.getTime());
    var daysDiff = Math.ceil(timeDiff / (1000 * 3600 * 24));
    return daysDiff;
}

async function getUserStatus() {
    try {
        const response = await fetchWithToken('https://toeic4all.com/user/status');
        const data = await response.json();

        if (data.status == 'logged_in') {
            console.log('Logged in');
            username = data.username;

            const userResponse = await fetchWithToken(`user/${username}`);
            const userData = await userResponse.json();

            // Display user detail
            $('#username-text').text(userData.username);
            $('#registered-date-text').text("모두의 토익에 함께한지 " + getDaysSinceJoined(userData.registered_on) + "일이 되었어요!");
            
            // Profile image - use user-selected image if it exists, otherwise use default
            const profilePicture = userData.profile_picture ? userData.profile_picture : "/static/images/profile1.png";
            $('#profile-image').attr("src", profilePicture);
            $('#email').val(userData.email || '');
            $('#phone').val(userData.phone || '');
            $('#job').val(userData.job || '');
            $('#toeic-experience').val(String(userData.toeic_experience) || '');
            $('#toeic-score').val(userData.toeic_score || '');
            $('#toeic-target-score').val(userData.toeic_target_score || '');
            $('#toeic-goal').val(userData.toeic_goal || '');
            $('#toeic-study-period').val(userData.toeic_study_period || '');
            $('#toeic-study-method').val(userData.toeic_study_method || '');
            // Make form fields disabled on page load
            $('#edit-form input, #edit-form select').prop('disabled', true);

            // Check if email is confirmed
            if (!userData.is_email_confirmed) {
                // Change the background color of the email input field to highlight it
                $('#email').css('background-color', '#ffcccc');
                // Add a button to send the verification email
                $('#email').after('<a class="col-12 col-md-12" id="email-verification-link" href="#">내 이메일 인증하기</a>');
            }
        } else {
            console.log('Not logged in');
        }
    } catch (error) {
        console.log('Error: ', error);
    }
}

$(document).ready(function() {
    
    getUserStatus();
    positionModalCloseText();
    
    $('#edit-button').click(function(event) {
        $('#edit-form input, #edit-form select, #save-button').prop('disabled', false);
        event.target.disabled = true;
    });

    $('#toeic-experience').on('change', function() {
        if (this.value === 'true') {
            $('#toeic-score').prop('disabled', false);
        } else {
            $('#toeic-score').prop('disabled', true);
        }
    });
    
    $('#edit-form').submit(function(event) {
        event.preventDefault();
        if (username) {
            const postData = {
                'email': $('#email').val(),
                'phone': $('#phone').val(),
                'job': $('#job').val(),
                'toeic_experience': $('#toeic-experience').val() === "true",
                'toeic_score': Number($('#toeic-score').val()),
                'toeic_target_score': Number($('#toeic-target-score').val()),
                'toeic_goal': $('#toeic-goal').val(),
                'toeic_study_period': $('#toeic-study-period').val(),
                'toeic_study_method': $('#toeic-study-method').val(),
            };
    
            fetchWithToken(`/user/${username}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(postData)
            })
            .then(response => {
                if (!response.ok) {
                    throw response;
                }
                return response.json();
            })
            .then(data => {
                console.log(data);
                if (data.success) {
                    alert('성공적으로 저장되었습니다!');
                    window.location.href = "https://toeic4all.com/user-detail";
                } else {
                    alert('오류가 발생했습니다. 다시 시도해주세요.');
                }
            })
            .catch(response => {
                // Try to extract the error message from the server and display it
                response.json().then(data => alert(data.message));
            });
        }
    });    
});

$(document).on('click', '#email-verification-link', function() {
    // Send the verification email
    $.ajax({
        url: '/user/email-verification',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({'email': $('#email').val()}),
        success: function(data) {
            if (data.success) {
                alert('인증 이메일이 발송되었습니다. 이메일을 확인해 주세요.');
            } else {
                alert(data.message);
            }
        },
        error: function(jqXHR, textStatus, errorThrown) {
            var response = JSON.parse(jqXHR.responseText);
            alert(response.message);
        }
    });
});

$('#profile-image-change-text').click(function() {
    // 모달을 표시합니다.
    $('#modal-background').css('display', 'block');
    
    // 모달 안의 이미지 그리드를 초기화합니다.
    $('#image-grid').empty();
    
    // 각 이미지를 모달 안의 이미지 그리드에 추가합니다.
    for (let i = 1; i <= 42; i++) {
        const imageContainer = $('<div>').addClass('image-container');
        const image = $('<img>')
            .attr('data-src', '/static/images/profile' + i + '.png') // src를 data-src로 변경합니다.
            .attr('width', '50')
            .attr('height', '50')
            .css('cursor', 'pointer')
            .on('error', function() { // 이미지 로드에 실패할 경우 다시 시도합니다.
                $(this).attr('src', $(this).attr('data-src'));
            })
            .appendTo(imageContainer);

        imageContainer.click(async function() {
            // 이미지를 클릭했을 때, 프로필 이미지를 변경하고 모달을 닫습니다.
            const clickedImage = $(this).find('img');
            $('#profile-image').attr('src', clickedImage.attr('src'));
            $('#modal-background').css('display', 'none');
                    
            // 변경된 이미지 정보를 서버에 업데이트합니다.
            const imageName = 'profile' + i + '.png';
            const response = await fetchWithToken('/user/set_profile_image', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ image_name: imageName })
            });

            const data = await response.json();
            if (data.status === 'success') {
                console.log('Profile image updated successfully');
                window.location.reload();
            } else {
                console.error('Error updating profile image:', data.message);
            }
        });
            
        $('#image-grid').append(imageContainer);
    }

    // 애니메이션을 시작합니다.
    setTimeout(function() {
        $('#image-modal').addClass('active');

        // 모달이 완전히 열린 후에 이미지를 로드합니다.
        $('#image-grid img').each(function() {
            $(this).attr('src', $(this).data('src'));
        });
    }, 50); // 50밀리초의 딜레이를 줍니다. 이는 CSS 애니메이션이 제대로 작동하기 위한 임시 조치입니다.
});

// 모달의 닫기 버튼을 눌렀을 때
$('#close-modal-button').click(function() {
    // 애니메이션을 종료하고 모달을 닫습니다.
    $('#image-modal').removeClass('active');
    setTimeout(function() {
        $('#modal-background').css('display', 'none');
    }, 500); // 애니메이션이 끝나는 시간과 일치해야 합니다.
});

$('#modal-background').click(function(e) {
    // 클릭된 요소가 #modal-background인 경우에만 모달을 닫습니다.
    if (e.target.id === 'modal-background') {
        $('#image-modal').removeClass('active');
        setTimeout(function() {
            $('#modal-background').css('display', 'none');
        }, 500); // 애니메이션이 끝나는 시간과 일치해야 합니다.
    }
});

window.onresize = function() {
    positionModalCloseText();
}

function positionModalCloseText() {
    var modalContent = document.getElementById('image-modal');
    var modalCloseText = document.getElementById('modal-close-text');

    // modalContent나 modalCloseText가 null이 아닌지 확인
    if (!modalContent || !modalCloseText) {
        console.log('image-modal or modal-close-text not found');
        return;
    }

    var modalContentHeight = modalContent.offsetHeight;
    var modalCloseTextHeight = modalCloseText.offsetHeight;

    var isMobile = window.innerWidth <= 600;

    if (isMobile) {
        // 모바일 화면에서는 question-modal가 화면 하단에 위치
        modalCloseText.style.top = "calc(47% - " + (modalContentHeight / 2 + modalCloseTextHeight + 10) + "px)";
    } else {
        // 피씨 화면에서는 question-modal가 중앙에 위치
        modalCloseText.style.top = "calc(17% - " + (modalContentHeight / 2 + modalCloseTextHeight + 10) + "px)";
    }
}

document.getElementById('image-modal').addEventListener('scroll', function() {
    var top  = this.scrollTop;
    var modalContentTop = document.getElementById('modal-content-top');
    
    // 스크롤 위치에 따라 배경색 변경
    if(top > 50){ // 50은 스크롤이 얼마나 이동했는지를 나타내는 값입니다. 이 값은 필요에 따라 조정하십시오.
      modalContentTop.style.backgroundColor = "#f0ebeb"; // 배경색을 옅은 회색으로 변경
    }else{
      modalContentTop.style.backgroundColor = "#ffffff"; // 배경색을 원래대로 변경
    }
});
  