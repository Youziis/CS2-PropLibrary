// 通用工具函数
// 拆分自 client/admin/script.js，以普通 <script> 加载（函数保持全局作用域）
// 依赖: 无

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1024 / 1024).toFixed(1) + ' MB';
}

function showImage(src) {
    event.stopPropagation();
    document.getElementById('modal-image').src = src;
    document.getElementById('image-modal').classList.add('active');
}

function closeModal() {
    document.getElementById('image-modal').classList.remove('active');
}


// 显示屏幕中央提示消息
function showCenterMessage(message, type) {
    // 创建或获取提示元素
    let messageEl = document.getElementById('center-message');
    if (!messageEl) {
        messageEl = document.createElement('div');
        messageEl.id = 'center-message';
        document.body.appendChild(messageEl);
    }
    
    // 设置样式和内容
    messageEl.className = `center-message ${type}`;
    messageEl.textContent = message;
    messageEl.classList.add('show');
    
    // 2秒后自动隐藏
    setTimeout(() => {
        messageEl.classList.remove('show');
    }, 2000);
}

// ========== 工具函数 ==========

// 复制文本到剪贴板
function copyToClipboard(text, button) {
    // 创建临时文本域
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    
    // 选择并复制
    textarea.select();
    textarea.setSelectionRange(0, 99999); // 兼容移动设备
    
    try {
        document.execCommand('copy');
        
        // 更新按钮状态
        const originalText = button.textContent;
        button.textContent = '已复制';
        button.style.background = '#00d4aa';
        
        // 2秒后恢复
        setTimeout(() => {
            button.textContent = originalText;
            button.style.background = '';
        }, 2000);
    } catch (err) {
        console.error('复制失败:', err);
        alert('复制失败，请手动选择并复制');
    } finally {
        document.body.removeChild(textarea);
    }
}

// 获取道具类型图标
function getUtilityTypeIcon(type) {
    const icons = {
        'smoke': '💨',
        'flashbang': '💡',
        'hegrenade': '💣',
        'molotov': '🔥',
        'incendiary': '🔥'
    };
    return icons[type] || '❓';
}
