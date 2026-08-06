// 时间格式化
function now() {
    const d = new Date();
    const pad = n => n.toString().padStart(2, "0");
    return `${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function getDateStr() {
    const d = new Date();
    const pad = n => n.toString().padStart(2, "0");
    return `${String(d.getFullYear()).slice(2)}${pad(d.getMonth()+1)}${pad(d.getDate())}`;
}

// 获取选中场地
function getSelectedSite() {
    const r = document.querySelector('input[name="site"]:checked');
    if (!r) {
        alert("请先选择场地！");
        return null;
    }
    return r.value;
}

// 获取选中用户
function getSelectedUser() {
    const r = document.querySelector('input[name="user"]:checked');
    if (!r) {
        alert("请先选择操作人！");
        return null;
    }
    return r.value;
}

// 弹窗控制
function openModal(modalEl) {
    modalEl.classList.add("show");
}

function closeModal(modalEl) {
    modalEl.classList.remove("show");
}