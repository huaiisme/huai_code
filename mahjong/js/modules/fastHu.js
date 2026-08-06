const fastHuModal = document.getElementById("fastHuModal");

function initFastHu() {
    document.getElementById("btnFastHu").addEventListener("click", openFastHuModal);
    document.getElementById("fastBtnPao").addEventListener("click", () => setFastType("pao"));
    document.getElementById("fastBtnZimo").addEventListener("click", () => setFastType("zimo"));
    document.getElementById("fastConfirmBtn").addEventListener("click", confirmFastHu);
}

// 打开极速胡牌弹窗
function openFastHuModal() {
    if (!getSelectedSite() || !getSelectedUser()) return;

    // 重置状态
    AppState.fastState = {
        huUser: getSelectedUser(),
        huScore: 0,
        type: "",
        paoUser: "",
        tile: { char: "", name: "" }
    };

    document.getElementById("fastHuTitle").innerText = `🎲 【${AppState.fastState.huUser}】 极速胡牌`;
    
    // 渲染胡数
    const huGrid = document.getElementById("fastHuGrid");
    huGrid.innerHTML = "";
    for (let i = HU_CONFIG.min; i <= HU_CONFIG.max; i += HU_CONFIG.step) {
        const btn = document.createElement("button");
        btn.className = "hu-btn";
        btn.innerText = i;
        btn.onclick = () => selectFastHuScore(i, btn);
        huGrid.appendChild(btn);
    }

    // 渲染放炮者列表
    const paoList = document.getElementById("fastPaoPersonList");
    paoList.innerHTML = "";
    AppState.users.filter(u => u !== AppState.fastState.huUser).forEach(u => {
        const btn = document.createElement("button");
        btn.innerText = u;
        btn.onclick = () => selectFastPaoUser(u, btn);
        paoList.appendChild(btn);
    });

    // 渲染牌
    renderFastTiles();

    // 重置UI状态
    document.getElementById("fastBtnPao").classList.remove("active");
    document.getElementById("fastBtnZimo").classList.remove("active");
    document.getElementById("fastPaoArea").classList.remove("show");
    document.getElementById("fastConfirmBtn").disabled = true;

    openModal(fastHuModal);
}

// 渲染麻将牌
function renderFastTiles() {
    const container = document.getElementById("fastTileContainer");
    container.innerHTML = "";
    const types = [
        { key: 'wan', name: '万子' },
        { key: 'tiao', name: '条子' },
        { key: 'tong', name: '筒子' },
        { key: 'zi', name: '字牌' }
    ];

    types.forEach(t => {
        const title = document.createElement("div");
        title.className = "tile-type-title";
        title.innerText = t.name;
        container.appendChild(title);

        const grid = document.createElement("div");
        grid.className = "fast-tile-grid";
        
        tileConfig[t.key].forEach(tile => {
            const btn = document.createElement("button");
            btn.className = "fast-tile-btn";
            btn.innerText = tile.char;
            btn.onclick = () => selectFastTile(tile, btn, grid);
            grid.appendChild(btn);
        });
        container.appendChild(grid);
    });
}

// 选择胡数
function selectFastHuScore(score, btn) {
    document.querySelectorAll("#fastHuGrid .hu-btn").forEach(b => b.classList.remove("selected"));
    btn.classList.add("selected");
    AppState.fastState.huScore = score;
    checkFastReady();
}

// 设置胡牌类型
function setFastType(type) {
    AppState.fastState.type = type;
    const btnPao = document.getElementById("fastBtnPao");
    const btnZimo = document.getElementById("fastBtnZimo");
    const paoArea = document.getElementById("fastPaoArea");

    btnPao.classList.remove("active");
    btnZimo.classList.remove("active");

    if (type === "pao") {
        btnPao.classList.add("active");
        paoArea.classList.add("show");
        AppState.fastState.paoUser = "";
        document.querySelectorAll("#fastPaoPersonList button").forEach(b => b.classList.remove("selected"));
    } else {
        btnZimo.classList.add("active");
        paoArea.classList.remove("show");
        AppState.fastState.paoUser = "";
    }
    checkFastReady();
}

// 选择放炮者
function selectFastPaoUser(user, btn) {
    document.querySelectorAll("#fastPaoPersonList button").forEach(b => b.classList.remove("selected"));
    btn.classList.add("selected");
    AppState.fastState.paoUser = user;
    checkFastReady();
}

// 选择牌
function selectFastTile(tile, btn, grid) {
    grid.querySelectorAll(".fast-tile-btn").forEach(b => b.classList.remove("selected"));
    btn.classList.add("selected");
    AppState.fastState.tile = tile;
    checkFastReady();
}

// 检查是否可以确认
function checkFastReady() {
    const s = AppState.fastState;
    const isReady = s.huScore > 0 && s.type !== "" && s.tile.name !== ""
        && (s.type === "zimo" || (s.type === "pao" && s.paoUser !== ""));
    document.getElementById("fastConfirmBtn").disabled = !isReady;
    return isReady;
}

// 确认胡牌记录
function confirmFastHu() {
    if (!checkFastReady()) return;
    const s = AppState.fastState;
    let descExtra = "";
    let militaryData = { active: false, user: "", target: "" };
    let desc = "";

    if (s.type === "pao") {
        if (AppState.military.active && AppState.military.target === s.paoUser) {
            descExtra = ` (军师${AppState.military.user}分锅)`;
            militaryData = {
                active: true,
                user: AppState.military.user,
                target: s.paoUser
            };
        }
        desc = `${s.huUser}【${s.huScore}胡】｜${s.paoUser}放炮【${s.tile.name}】${descExtra}`;
        AppState.records.push({
            t: "pao",
            from: s.paoUser,
            to: s.huUser,
            huScore: s.huScore,
            tile: s.tile.char,
            tileName: s.tile.name,
            desc: desc,
            time: now(),
            military: militaryData
        });
    } else {
        desc = `${s.huUser}【${s.huScore}胡】｜自摸【${s.tile.name}】`;
        AppState.records.push({
            t: "zimo",
            from: s.huUser,
            huScore: s.huScore,
            tile: s.tile.char,
            tileName: s.tile.name,
            desc: desc,
            time: now()
        });
    }

    closeModal(fastHuModal);
    refresh();
}