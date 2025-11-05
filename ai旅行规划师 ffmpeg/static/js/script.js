
// 检查登录状态
async function checkLoginStatus() {
    try {
        // 尝试访问需要登录的API
        const response = await fetch('/api/itineraries', {
            method: 'GET',
            credentials: 'include'
        });

        if (response.status === 401) {
            // 未登录，跳转到登录页
            window.location.href = 'login.html';
        }
    } catch (error) {
        console.log('检查登录状态失败');
    }
}

// 登出功能
document.getElementById('logoutBtn')?.addEventListener('click', async () => {
    try {
        await fetch('/api/logout', {
            method: 'POST',
            credentials: 'include'
        });
        window.location.href = 'login.html';
    } catch (error) {
        alert('登出失败');
    }
});