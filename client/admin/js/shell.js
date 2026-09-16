// 初始化入口 / 侧边栏 / 标签页
// 拆分自 client/admin/script.js，以普通 <script> 加载（函数保持全局作用域）
// 依赖: 其他所有模块

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initTabs();
    initSidebarToggle();
    loadStats();
    loadOverviewStats();
    loadOverviewPendingStats();
    loadDemos();
    loadTypeStats();
    loadPending();
    loadExportStats();
    loadPendingExportUtilities();
});

// 侧边栏收缩展开功能
function initSidebarToggle() {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('sidebar-toggle');
    
    if (!sidebar || !toggleBtn) return;
    
    // 从localStorage读取侧边栏状态
    const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    if (isCollapsed) {
        sidebar.classList.add('collapsed');
    }
    
    // 点击切换按钮
    toggleBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        sidebar.classList.toggle('collapsed');
        
        // 保存状态到localStorage
        const collapsed = sidebar.classList.contains('collapsed');
        localStorage.setItem('sidebarCollapsed', collapsed);
        
        // 添加动画结束后的回调
        if (!collapsed) {
            // 展开时，延迟显示文字
            setTimeout(() => {
                sidebar.style.overflowX = 'hidden';
            }, 300);
        }
    });
    
    // 为导航项添加tooltip属性
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        const text = item.querySelector('.nav-text');
        if (text) {
            item.setAttribute('data-tooltip', text.textContent.trim());
        }
    });
}

// 标签页切换
function initTabs() {
    const navItems = document.querySelectorAll('.nav-item');
    const contents = document.querySelectorAll('.tab-content');
    
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetTab = item.dataset.tab;
            
            // 切换活动导航项
            navItems.forEach(t => t.classList.remove('active'));
            item.classList.add('active');
            
            // 切换内容
            contents.forEach(c => c.classList.remove('active'));
            document.getElementById(`${targetTab}-tab`).classList.add('active');
            
            // 加载对应数据
            if (targetTab === 'demo') {
                loadDemos();
            } else if (targetTab === 'select') {
                loadTypeStats();
            } else if (targetTab === 'review') {
                loadPending();
            } else if (targetTab === 'export') {
                loadExportStats();
                loadPendingExportUtilities();
            } else if (targetTab === 'exported') {
                loadExportedStats();
                loadExportedUtilities();
            } else if (targetTab === 'relations') {
                initRelationsTab();
            } else if (targetTab === 'overview') {
                loadStats();
                loadOverviewStats();
                loadOverviewPendingStats();
            }
        });
    });
}
