// 页面加载完成后初始化所有模块
document.addEventListener("DOMContentLoaded", () => {
    // 1. 加载本地数据
    loadLocal();

    // 2. 初始化各业务模块
    initUserManage();
    initFastHu();
    initActions();
    initSettle();
    initTitle();
    initMilitary();
    initExport();
    initKeyboard(); // 键盘快捷键模块

    // 3. 首次渲染界面
    refreshAllUI();
});