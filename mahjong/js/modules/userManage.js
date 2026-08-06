function initUserManage() {
    document.getElementById("btnAddUser").addEventListener("click", addUser);
    document.getElementById("btnDelUser").addEventListener("click", deleteUser);
}

function addUser() {
    const input = document.getElementById("newUserInput");
    const n = input.value.trim();
    if (!n || AppState.users.includes(n)) {
        alert("无效或已存在");
        return;
    }
    AppState.users.push(n);
    input.value = "";
    refreshAllUI();
    saveToLocal();
}

function deleteUser() {
    const n = document.getElementById("delUserSelect").value;
    if (!n) return;
    
    const hasRecord = AppState.records.some(r =>
        r.from === n || r.to === n || r.f === n || r.obUsers?.includes(n)
    );
    const hasSettle = AppState.settleRecords.some(s =>
        s.ranked.some(i => i.user === n)
    );
    
    if (hasRecord || hasSettle) {
        alert("无法删除，有记录");
        return;
    }
    
    if (confirm(`删除${n}？`)) {
        AppState.users = AppState.users.filter(x => x !== n);
        document.getElementById("delUserSelect").value = "";
        refreshAllUI();
        saveToLocal();
    }
}