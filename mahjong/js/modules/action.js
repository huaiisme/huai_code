const personModal = document.getElementById("personModal");

function initActions() {
    document.getElementById("btnJieHu").addEventListener("click", prepareJieHu);
    document.getElementById("btnNiqiu").addEventListener("click", () => actOne("泥鳅"));
    document.getElementById("btnDogLuck").addEventListener("click", openDogLuckModal);
    document.getElementById("btnCaiP").addEventListener("click", openCaiPModal);
    document.getElementById("btnOB").addEventListener("click", prepareOB);
    document.getElementById("btnUndo").addEventListener("click", undo);
    document.getElementById("btnClear").addEventListener("click", clearAll);

    // 菜P按钮事件
    document.querySelectorAll("#caiPModal .caip-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            actCaiP(btn.dataset.action);
        });
    });

    // 狗运按钮事件
    document.querySelectorAll("#dogLuckModal .caip-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            actDogLuck(btn.dataset.action);
        });
    });
}

// 菜P操作
function openCaiPModal() {
    if (!getSelectedSite() || !getSelectedUser()) return;
    openModal(document.getElementById("caiPModal"));
}

function actCaiP(actionName) {
    closeModal(document.getElementById("caiPModal"));
    actOne(actionName);
}

// 狗运操作
function openDogLuckModal() {
    if (!getSelectedSite() || !getSelectedUser()) return;
    openModal(document.getElementById("dogLuckModal"));
}

function actDogLuck(actionName) {
    closeModal(document.getElementById("dogLuckModal"));
    actOne(actionName);
}

// 截胡
function prepareJieHu() {
    const u = getSelectedUser();
    if (!u || !getSelectedSite()) return;
    
    document.getElementById("personModalTitle").innerText = "截胡谁？";
    const list = document.getElementById("personList");
    list.innerHTML = "";
    
    AppState.users.filter(x => x !== u).forEach(t => {
        const b = document.createElement("button");
        b.innerText = t;
        b.onclick = () => {
            closeModal(personModal);
            AppState.records.push({
                t: "jie", from: u, to: t,
                desc: `${u}→截胡→${t}`,
                time: now()
            });
            refresh();
        };
        list.appendChild(b);
    });
    openModal(personModal);
}

// OB
function prepareOB() {
    if (!getSelectedSite()) return;
    
    document.getElementById("personModalTitle").innerText = "谁在边缘OB？";
    const list = document.getElementById("personList");
    list.innerHTML = "";
    
    AppState.users.forEach(t => {
        const b = document.createElement("button");
        b.innerText = t;
        b.onclick = () => {
            closeModal(personModal);
            AppState.records.push({
                t: "ob", obUsers: [t],
                desc: `${t}OB，${AppState.users.filter(x => x !== t).join("、")}+1局`,
                time: now()
            });
            refresh();
        };
        list.appendChild(b);
    });
    openModal(personModal);
}

// 通用单动作
function actOne(a) {
    const u = getSelectedUser();
    if (!u || !getSelectedSite()) return;
    AppState.records.push({
        t: "one", f: u, a: a,
        desc: `${u}｜${a}`,
        time: now()
    });
    refresh();
}

// 撤销
function undo() {
    if (AppState.records.length === 0 && AppState.settleRecords.length === 0) {
        alert("无记录");
        return;
    }
    const rt = AppState.records.length > 0 ? AppState.records[AppState.records.length-1].time : "0";
    const st = AppState.settleRecords.length > 0 ? AppState.settleRecords[AppState.settleRecords.length-1].time : "0";

    if (rt > st) {
        const lastRec = AppState.records[AppState.records.length-1];
        if (lastRec.t === "sys" && lastRec.desc.includes("军师模式")) {
            AppState.military.active = false;
            AppState.military.user = "";
            AppState.military.target = "";
            document.getElementById("btnMilitary").classList.remove("active");
        }
        AppState.records.pop();
    } else {
        AppState.settleRecords.pop();
    }
    refresh();
}

// 清空
function clearAll() {
    if (confirm("清空所有？")) {
        AppState.records = [];
        AppState.settleRecords = [];
        AppState.military.active = false;
        AppState.military.user = "";
        AppState.military.target = "";
        document.getElementById("btnMilitary").classList.remove("active");
        refresh();
    }
}