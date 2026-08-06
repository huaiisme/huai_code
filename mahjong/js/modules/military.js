const militaryModal = document.getElementById("militaryModal");
const btnMilitary = document.getElementById("btnMilitary");

function initMilitary() {
    btnMilitary.addEventListener("click", toggleMilitary);
}

function toggleMilitary() {
    if (!getSelectedSite() || !getSelectedUser()) return;

    if (AppState.military.active) {
        // 关闭军师模式
        AppState.military.active = false;
        AppState.military.user = "";
        AppState.military.target = "";
        btnMilitary.classList.remove("active");
        AppState.records.push({
            t: "sys",
            desc: `军师模式关闭`,
            time: now()
        });
        refresh();
    } else {
        // 开启军师模式：先选人
        AppState.military.user = getSelectedUser();
        openMilitaryModal();
    }
}

function openMilitaryModal() {
    const list = document.getElementById("militaryPersonList");
    list.innerHTML = "";
    document.getElementById("militaryModalTitle").innerText = `【${AppState.military.user}】要指点谁？`;

    // 筛选除了自己之外的人
    AppState.users.filter(u => u !== AppState.military.user).forEach(u => {
        const btn = document.createElement("button");
        btn.innerText = u;
        btn.onclick = () => {
            AppState.military.target = u;
            AppState.military.active = true;
            btnMilitary.classList.add("active");
            closeModal(militaryModal);
            AppState.records.push({
                t: "sys",
                desc: `${AppState.military.user} 开启军师模式，指点 ${AppState.military.target}`,
                time: now()
            });
            refresh();
        };
        list.appendChild(btn);
    });

    openModal(militaryModal);
}