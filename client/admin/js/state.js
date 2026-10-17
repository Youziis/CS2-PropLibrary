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
    'molotov': '燃烧弹 (T)',
    'incendiary': '燃烧弹 (CT)',
    'decoy': '诱饵弹'
};

// 类型下拉的展示顺序（与 TYPE_NAMES 对应）
const TYPE_OPTION_ORDER = ['smoke', 'flashbang', 'hegrenade', 'molotov', 'incendiary', 'decoy'];

/**
 * 生成类型下拉的 <option> 列表
 *
 * 若数据库里出现清单之外的类型，会把它原样补进选项，
 * 避免下拉框没有匹配项时静默回落到第一项（烟雾弹）而被改错类型。
 */
function typeOptionsHtml(currentType) {
    const types = TYPE_OPTION_ORDER.slice();
    if (currentType && types.indexOf(currentType) === -1) {
        types.push(currentType);
    }
    return types.map(t =>
        `<option value="${t}"${t === currentType ? ' selected' : ''}>${TYPE_NAMES[t] || t}</option>`
    ).join('');
}
