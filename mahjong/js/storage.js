// 保存到本地存储
function saveToLocal() {
    localStorage.setItem('mj_u', JSON.stringify(AppState.users));
    localStorage.setItem('mj_r', JSON.stringify(AppState.records));
    localStorage.setItem('mj_s', JSON.stringify(AppState.settleRecords));
    localStorage.setItem('mj_m', JSON.stringify(AppState.military));
}

// 从本地存储加载
function loadLocal() {
    try {
        const u = localStorage.getItem('mj_u');
        if (u) AppState.users = JSON.parse(u);
        
        const r = localStorage.getItem('mj_r');
        if (r) AppState.records = JSON.parse(r);
        
        const s = localStorage.getItem('mj_s');
        if (s) AppState.settleRecords = JSON.parse(s);
        
        const m = localStorage.getItem('mj_m');
        if (m) {
            AppState.military = JSON.parse(m);
            if (AppState.military.active) {
                document.getElementById("btnMilitary").classList.add("active");
            }
        }
    } catch (e) {
        console.error("加载本地数据失败", e);
    }
}