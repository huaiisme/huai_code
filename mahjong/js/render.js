// 计算基础统计数据
function calcBaseStats() {
    const st = {};
    AppState.users.forEach(u => {
        st[u] = {
            p:0, w:0, z:0, j:0, bj:0, n:0, c3:0, b4:0, tdh:0, gs:0,
            bg:0, zh:0, ll:0, game:0, militaryP:0,
            hu30_40:0, hu50_80:0, hu90_200:0, hu210_390:0, hu400:0
        };
    });

    AppState.records.forEach(r => {
        if (r.t === "pao" && st[r.from]) {
            if (r.military && r.military.active) {
                st[r.from].p += 0.5;
                if (st[r.military.user]) {
                    st[r.military.user].p += 0.5;
                    st[r.military.user].militaryP += 0.5;
                }
            } else {
                st[r.from].p++;
            }
            if (st[r.to]) st[r.to].w++;
        }

        if (r.t === "zimo" && st[r.from]) {
            st[r.from].w++;
            st[r.from].z++;
        }

        if (r.t === "jie" && st[r.from]) {
            st[r.from].j++;
            if (st[r.to]) st[r.to].bj++;
        }

        if (r.t === "ob") {
            AppState.users.forEach(u => {
                if (!r.obUsers.includes(u) && st[u]) st[u].game++;
            });
        }

        if (r.t === "one" && st[r.f]) {
            const a = r.a;
            if (a === "泥鳅") st[r.f].n++;
            if (a === "3财神") st[r.f].c3++;
            if (a === "4白板") st[r.f].b4++;
            if (a === "天&地胡") st[r.f].tdh++;
            if (a === "杠上开花") st[r.f].gs++;
            if (a === "第一张被跟") st[r.f].bg++;
            if (a === "诈胡") st[r.f].zh++;
            if (a === "姥姥") st[r.f].ll++;
        }

        // 胡数分段统计
        if ((r.t === "pao" || r.t === "zimo") && r.huScore) {
            const hu = r.huScore;
            const user = r.t === "pao" ? r.to : r.from;
            if (!st[user]) return;
            if (hu === 30 || hu === 40) st[user].hu30_40++;
            else if (hu >= 50 && hu <= 80) st[user].hu50_80++;
            else if (hu >= 90 && hu <= 200) st[user].hu90_200++;
            else if (hu >= 210 && hu <= 390) st[user].hu210_390++;
            else if (hu === 400) st[user].hu400++;
        }
    });

    return st;
}

// 计算牌面统计
function calcTileStats(type) {
    const globalCount = {};
    const personCount = {};
    AppState.users.forEach(u => personCount[u] = {});

    AppState.records.filter(r => r.t === type).forEach(r => {
        const k = `${r.tileName}${r.tile}`;
        globalCount[k] = (globalCount[k] || 0) + 1;
        personCount[r.from][k] = (personCount[r.from][k] || 0) + 1;
    });

    return {
        sortedGlobal: Object.entries(globalCount)
            .sort((a, b) => b[1] - a[1])
            .map(i => ({ tile: i[0], count: i[1] })),
        personCount
    };
}

// 渲染玩家选择组
function renderPersonGroup() {
    const container = document.getElementById("personGroupContainer");
    container.innerHTML = "";
    AppState.users.forEach((u, i) => {
        const id = `u_${i}`;
        const input = document.createElement("input");
        input.type = "radio";
        input.name = "user";
        input.id = id;
        input.value = u;
        if (i === 0) input.checked = true;
        const label = document.createElement("label");
        label.htmlFor = id;
        label.innerText = u;
        container.appendChild(input);
        container.appendChild(label);
    });
}

// 渲染删除下拉
function renderDelSelect() {
    const sel = document.getElementById("delUserSelect");
    sel.innerHTML = '<option value="">选择删除</option>';
    AppState.users.forEach(u => {
        const o = document.createElement("option");
        o.value = u;
        o.innerText = u;
        sel.appendChild(o);
    });
}

// 更新财神名次选项
function updateGoldRankOptions() {
    const sel = document.getElementById("goldRankSelect");
    sel.innerHTML = "";
    for (let i = 1; i <= AppState.users.length; i++) {
        const opt = document.createElement("option");
        opt.value = i;
        if (i === AppState.users.length) {
            opt.selected = true;
            opt.innerText = `第${i}名（默认输最多）`;
        } else {
            opt.innerText = `第${i}名`;
        }
        sel.appendChild(opt);
    }
}

// 渲染结算历史UI
function refreshSettleUI() {
    const box = document.getElementById("settleBox");
    const history = document.getElementById("settleHistory");
    
    if (AppState.settleRecords.length === 0) {
        box.style.display = "none";
        return;
    }
    box.style.display = "block";

    let html = "";
    [...AppState.settleRecords].reverse().forEach(rec => {
        html += `<div class="settle-history-item"><div class="settle-history-time">${rec.time}</div>`;
        rec.ranked.forEach((item, idx) => {
            const rank = idx + 1;
            const isGold = rank === rec.goldRank;
            const c = item.amount > 0 ? "color:#2d882d" : (item.amount < 0 ? "color:#d92c2c" : "");
            let cls = "settle-rank-row";
            if (isGold) cls += " rank-gold";
            else if (rank === 1) cls += " rank-1";
            else if (rank === rec.ranked.length) cls += " rank-last";
            html += `<div class="${cls}"><span>第${rank}名：${item.user} ${isGold?"👑":""}</span><span style="${c};font-weight:bold">${item.amount>0?"+":""}${item.amount.toFixed(2)}元</span></div>`;
        });
        html += `<div class="settle-result-text">${rec.resultText}</div></div>`;
    });
    history.innerHTML = html;
}

// 全局刷新入口
function refresh() {
    const base = calcBaseStats();
    const pao = calcTileStats("pao");
    const zimo = calcTileStats("zimo");

    // 统计面板
    document.getElementById("stats").innerHTML = AppState.users.map(u => {
        const d = base[u] || { p:0, w:0, z:0, j:0, bj:0, n:0, c3:0, b4:0, tdh:0, gs:0, bg:0, zh:0, ll:0, game:0, militaryP:0, hu30_40:0, hu50_80:0, hu90_200:0, hu210_390:0, hu400:0 };
        const displayP = Number.isInteger(d.p) ? d.p : d.p.toFixed(1);
        return `<div class="stats-row">
            <div class="stats-name">${u}</div>
            <div class="stats-item">${displayP}</div>
            <div class="stats-item">${d.w}</div>
            <div class="stats-item">${d.z}</div>
            <div class="stats-item">${d.j}</div>
            <div class="stats-item">${d.bj}</div>
            <div class="stats-item">${d.n}</div>
            <div class="stats-item">${d.c3}</div>
            <div class="stats-item">${d.b4}</div>
            <div class="stats-item">${d.tdh}</div>
            <div class="stats-item">${d.gs}</div>
            <div class="stats-item">${d.bg}</div>
            <div class="stats-item">${d.zh}</div>
            <div class="stats-item">${d.ll}</div>
            <div class="stats-item" style="color:#8e44ad">${d.game}</div>
            <div class="stats-item">${d.hu30_40}</div>
            <div class="stats-item">${d.hu50_80}</div>
            <div class="stats-item">${d.hu90_200}</div>
            <div class="stats-item">${d.hu210_390}</div>
            <div class="stats-item">${d.hu400}</div>
        </div>`;
    }).join("");

    // 牌统计渲染
    const renderTileStats = (stats, globalId, personId) => {
        document.getElementById(globalId).innerHTML = stats.sortedGlobal.length
            ? stats.sortedGlobal.map(i => `<div class="tile-rank-item"><span class="tile-rank-char">${i.tile.slice(-2)}</span><span>${i.tile.slice(0,-2)}×${i.count}</span></div>`).join("")
            : '<div class="empty-tip">暂无记录</div>';
        
        document.getElementById(personId).innerHTML = AppState.users.map(u => {
            const t = Object.entries(stats.personCount[u] || {}).sort((a, b) => b[1] - a[1]);
            return `<div class="person-tile-card"><div class="person-tile-name">${u}</div>
                <div class="person-tile-list">${t.length ? t.map(i => `<span>${i[0].slice(-2)}×${i[1]}</span>`).join("") : '<span style="color:#999">暂无</span>'}</div></div>`;
        }).join("");
    };

    renderTileStats(pao, "globalPaoTileRank", "personPaoTileDetail");
    renderTileStats(zimo, "globalZimoTileRank", "personZimoTileDetail");

    // 牌局统计
    document.getElementById("gameCountDetail").innerHTML = AppState.users.map(u =>
        `<div class="person-tile-card"><div class="person-tile-name">${u}</div>
        <div style="font-size:24px;color:#8e44ad;text-align:center">${(base[u] || {}).game || 0}局</div></div>`
    ).join("");

    // 日志
    document.getElementById("log").innerText = AppState.records.map(r => `[${r.time}] ${r.desc}`).join("\n");
    
    refreshSettleUI();
    saveToLocal();
}

// 刷新所有UI
function refreshAllUI() {
    renderPersonGroup();
    renderDelSelect();
    updateGoldRankOptions();
    refresh();
}