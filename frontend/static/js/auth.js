// static/js/auth.js

export async function loadUserStatus(userStatusId = "userStatus") {
    const token = localStorage.getItem("token");
    let user = {};
    const res = await fetch("/api/user", {
        headers: { Authorization: `Bearer ${token}` }
    });
    user = await res.json();

    const userStatus = document.getElementById(userStatusId);
    if (userStatus) {
        userStatus.innerHTML = user.username
            ? `<a href="#">${user.username} 你好！</a> <a href="#" onclick="logout()">登出</a>`
            : `<a href="/login">登入/註冊</a>`;
    }
}
export function logout() {
    localStorage.removeItem("token");
    window.location.href = "/";
}

export function isTokenExpired(token) {
    if (!token) return true;

    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const now = Math.floor(Date.now() / 1000); // 現在時間 (秒)
        return payload.exp < now;
    } catch (e) {
        console.error("Token parsing failed:", e);
        return true;
    }
}