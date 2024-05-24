const mobileUserBtn = document.getElementById('mobile-user-btn');
const sideNav = document.getElementById('side-nav');
const closeSidebarButton = document.getElementById('close-sidebar-button');

function toggleNav() {
    if (sideNav.classList.contains('hidden')) {
        sideNav.classList.remove('hidden');
        sideNav.classList.add('visible');
    } else {
        sideNav.classList.remove('visible');
        sideNav.classList.add('hidden');
    }
}

mobileUserBtn.addEventListener('click', toggleNav);
closeSidebarButton.addEventListener('click', toggleNav);

document.addEventListener('click', function(event) {
    var isClickInside = sideNav.contains(event.target);
    var isMobileUserBtnClicked = mobileUserBtn.contains(event.target);
    var isCloseButtonClicked = closeSidebarButton.contains(event.target);

    if (!isClickInside && !isMobileUserBtnClicked && !isCloseButtonClicked) {
        sideNav.classList.remove('visible');
        sideNav.classList.add('hidden');
    }
});

function makeRequest(method, url, headers = {}, callback, errorCallback) {
    var xhr = new XMLHttpRequest();
    xhr.open(method, url);
    Object.keys(headers).forEach(function(key) {
        xhr.setRequestHeader(key, headers[key]);
    });
    xhr.onload = function() {
        if (xhr.status === 200) {
            callback(JSON.parse(xhr.responseText));
        } else if (errorCallback) {
            errorCallback();
        }
    };
    xhr.send();
}

function updateUI(isLoggedIn, username, profile_picture) {
    $('#nav-logout, #mobile-nav-logout').toggle(isLoggedIn);
    $('#nav-login, #mobile-nav-login').toggle(!isLoggedIn);

    if (isLoggedIn) {
        profile_picture = profile_picture || '/static/images/profile1.png';  // 프로필 사진이 없으면 기본 이미지를 사용합니다.

        const userPCMenuHtml = `
            <a href="/user-detail"><img src="${profile_picture}" width="20" height="20" class="profile-img" style="margin-right: 10px;">${username} 님</a>
            <ul id="nav-user-dropdown">
                <li><a href="/user-detail">내 정보</a></li>
                <li><a href="/mypage">찜한 문제</a></li>
                <li><a href="/mynote">내 오답노트</a></li>
                <li><a href="/myvoca">내 단어장</a></li>
                <li><a href="/my-learning-analysis">내 학습 분석</a></li>
            </ul>
        `;
        const userMobileMenuHtml = `
            <ul id="mobile-user-dropdown">
                <li><i class="fas fa-user"></i> <a href="/user-detail">&nbsp;&nbsp;내 정보</a></li>
                <li><i class="fas fa-star"></i> <a href="/mypage">&nbsp;&nbsp;찜한 문제</a></li>
                <li><i class="fas fa-eraser"></i> <a href="/mynote">&nbsp;&nbsp;내 오답노트</a></li>
                <li><i class="fas fa-language"></i> <a href="/myvoca">&nbsp;&nbsp;내 단어장</a></li>
                <li><i class="fas fa-chart-line"></i> <a href="/my-learning-analysis">&nbsp;&nbsp;내 학습 분석</a></li>
            </ul>
        `;
        const userProfileBtnHtml = `
        <div id="login-area">
        <img src="${profile_picture}" width="30" height="30" class="profile-img" id="mobile-user-icon">
        </div>
        `;

        $('#nav-user').html(userPCMenuHtml).show();
        $('#mobile-user-btn').html(userProfileBtnHtml).show();
        $('#mobile-nav-user').html(userMobileMenuHtml).show();
    } else {
        $('#nav-user, #mobile-nav-user').hide();
    }
}

$(document).ready(function() {
    var token = localStorage.getItem('access_token');
    if (token) {
        makeRequest(
            'GET',
            'https://toeic4all.com/user/status',
            { 'Authorization': `Bearer ${token}` },
            function(data) {
                console.log(data);
                if (data.status == 'logged_in') {
                    console.log('Logged in');
                    updateUI(true, data.username, data.profile_picture);
                }
            },
            function() {
                console.log('Not logged in');
                updateUI(false);
            }
        );
    } else {
        console.log('Not logged in');
        updateUI(false);
    }

    $('#nav-logout, #mobile-nav-logout').click(function() {
        localStorage.removeItem('access_token');
        location.reload();
    });

    // Code for nav-user dropdown
    $('#nav-user').hover(function() {
        // Mouse enter
        $('#nav-user-dropdown').show();
    }, function() {
        // Mouse leave
        $('#nav-user-dropdown').hide();
    });
});

window.addEventListener('scroll', scrollFunction);

function scrollFunction() {
    let navbar = document.getElementById("mobile-nav");
    let title = document.getElementById("mobile-title");
    let titleLink = document.querySelector("#mobile-title a")
    let titleLogo = document.querySelector("#mobile-title a img")
    let mobileUserIcon = document.getElementById("mobile-user-icon");
    let loginArea = document.getElementById("login-area");

    if (document.body.scrollTop > 50 || document.documentElement.scrollTop > 50) {
        navbar.style.height = "10px";
        navbar.style.backgroundColor = '#eae8e8';
        title.style.fontSize = "10px";
        title.style.fontWeight = "500";
        titleLink.style.color = '#343333';
        titleLogo.style.width = '13px';
        titleLogo.style.height = '13px';
        titleLogo.style.marginBottom = '1px';
        mobileUserIcon.style.color = '#343333';
        loginArea.style.scale = '0.5';
        loginArea.style.border = '1px solid #bdb9b9';
    } else {
        navbar.style.height = "50px";
        navbar.style.backgroundColor = '#343333';
        title.style.fontSize = "1.5rem";
        title.style.fontWeight = "700";
        titleLink.style.color = '#fff';
        titleLogo.style.width = '25px';
        titleLogo.style.height = '25px';
        titleLogo.style.marginBottom = '5px';
        mobileUserIcon.style.color = '#fff';
        loginArea.style.scale = '1';
        loginArea.style.border = '1px solid #fff';
    }
}

let scrollPosition = 0;
let lastScroll = 0;
let hideTimer = null;

const navbar = document.getElementById("mobile-navbar-bottom");

window.addEventListener('scroll', function() {
    let currentScroll = window.scrollY;

    clearTimeout(hideTimer);
    hideTimer = setTimeout(function() {
        navbar.style.bottom = "-70px"; // 2초 동안 아무 스크롤도 없으면 네비게이션 바를 숨깁니다.
    }, 3000);
  
    if (currentScroll > scrollPosition && currentScroll > 100) {
        // 스크롤이 아래로 가고, 적어도 100px 아래로 내려갔을 때
        navbar.style.bottom = "-70px";
    } else if (currentScroll < scrollPosition && (scrollPosition - currentScroll) > 5) {
        // 스크롤이 위로 올라가고, 적어도 5px 이상 올라갔을 때
        navbar.style.bottom = "0px";
    }

    lastScroll = scrollPosition;
    scrollPosition = currentScroll;
});

document.addEventListener("DOMContentLoaded", function() {
    var currentPath = window.location.pathname;
    var navItems = document.querySelectorAll(".nav-item a");

    navItems.forEach(function(navItem) {
        if (navItem.getAttribute("href") === currentPath) {
            navItem.parentElement.classList.add("active");
        }
    });
});
