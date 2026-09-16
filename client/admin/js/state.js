// 全局状态与常量
// 拆分自 client/admin/script.js，以普通 <script> 加载（函数保持全局作用域）
// 依赖: 无

// 全局变量
let allUtilities = [];
let filteredUtilities = [];
let currentFilterDemo = 'all'; // 当前筛选的 demo
let currentFilterMap = 'all';  // 当前筛选的地图
let currentFilterScreenshot = 'all'; // 当前筛选的截图状态
let currentFilterType = 'all'; // 当前筛选的道具类型

const TYPE_NAMES = {
    'smoke': '烟雾弹',
    'flashbang': '闪光弹',
    'hegrenade': '手雷',
    'incendiary': '燃烧弹',
    'molotov': '燃烧弹'
};
