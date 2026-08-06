function initExport() {
    document.getElementById("btnExport").addEventListener("click", exportExcel);
}

function exportExcel() {
    const site = getSelectedSite();
    if (!site) return;
    if (AppState.records.length === 0 && AppState.settleRecords.length === 0) {
        alert("暂无记录");
        return;
    }

    const baseStats = calcBaseStats();
    const paoStats = calcTileStats("pao");
    const zimoStats = calcTileStats("zimo");

    // Sheet1 实时战报
    const sheet1 = [
        ["时间", "描述", "胡数", "放炮", "获胜", "自摸", "截胡", "被截", "泥鳅",
         "3财神", "4白板", "天&地胡", "杠上开花", "被跟", "诈胡", "姥姥", "放炮牌", "自摸牌"]
    ];
    AppState.records.forEach(r => {
        const row = ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""];
        row[0] = r.time;
        row[1] = r.desc;
        if (r.huScore) row[2] = r.huScore;
        if (r.t === "pao") {
            row[3] = r.from;
            row[4] = r.to;
            row[16] = `${r.tileName}${r.tile}`;
        }
        if (r.t === "zimo") {
            row[4] = r.from;
            row[5] = 1;
            row[17] = `${r.tileName}${r.tile}`;
        }
        if (r.t === "jie") {
            row[6] = r.from;
            row[7] = r.to;
        }
        if (r.t === "one") {
            const idx = {
                "泥鳅": 8, "3财神": 9, "4白板": 10, "天&地胡": 11,
                "杠上开花": 12, "第一张被跟": 13, "诈胡": 14, "姥姥": 15
            }[r.a];
            if (idx !== undefined) row[idx] = r.f;
        }
        sheet1.push(row);
    });

    // Sheet2 基础计数
    const sheet2 = [
        ["玩家", "放炮", "获胜", "自摸", "截胡", "被截", "泥鳅", "3财神", "4白板",
         "天&地胡", "杠上开花", "被跟", "诈胡", "姥姥", "牌局数", "军师分锅数",
         "30/40胡", "50-80胡", "90-200胡", "210-390胡", "400胡"]
    ];
    AppState.users.forEach(u => {
        const d = baseStats[u] || {
            p: 0, w: 0, z: 0, j: 0, bj: 0, n: 0, c3: 0, b4: 0, tdh: 0, gs: 0,
            bg: 0, zh: 0, ll: 0, game: 0, militaryP: 0,
            hu30_40: 0, hu50_80: 0, hu90_200: 0, hu210_390: 0, hu400: 0
        };
        sheet2.push([
            u, d.p, d.w, d.z, d.j, d.bj, d.n, d.c3, d.b4, d.tdh, d.gs,
            d.bg, d.zh, d.ll, d.game, d.militaryP,
            d.hu30_40, d.hu50_80, d.hu90_200, d.hu210_390, d.hu400
        ]);
    });

    // Sheet3 胡牌统计
    const sheet3 = [
        ["【放炮牌】全局排行", "", ""],
        ["牌名", "字符", "放炮次数"]
    ];
    paoStats.sortedGlobal.forEach(i =>
        sheet3.push([i.tile.slice(0, -2), i.tile.slice(-2), i.count])
    );
    sheet3.push([]);
    sheet3.push(["【放炮牌】个人明细", "", ""]);
    sheet3.push(["玩家", "牌名", "次数"]);
    AppState.users.forEach(u => {
        Object.entries(paoStats.personCount[u] || {})
            .sort((a, b) => b[1] - a[1])
            .forEach(i => sheet3.push([u, i[0], i[1]]));
    });

    sheet3.push([]);
    sheet3.push(["【自摸牌】全局排行", "", ""], ["牌名", "字符", "自摸次数"]);
    zimoStats.sortedGlobal.forEach(i =>
        sheet3.push([i.tile.slice(0, -2), i.tile.slice(-2), i.count])
    );
    sheet3.push([]);
    sheet3.push(["【自摸牌】个人明细", "", ""]);
    sheet3.push(["玩家", "牌名", "次数"]);
    AppState.users.forEach(u => {
        Object.entries(zimoStats.personCount[u] || {})
            .sort((a, b) => b[1] - a[1])
            .forEach(i => sheet3.push([u, i[0], i[1]]));
    });

    sheet3.push([]);
    sheet3.push(["牌局参与", ""]);
    sheet3.push(["玩家", "局数"]);
    AppState.users.forEach(u =>
        sheet3.push([u, (baseStats[u] || {}).game || 0])
    );

    // Sheet4 输赢结算
    const sheet4 = [["👑 输赢结算&财神记录"]];
    sheet4.push(["结算时间", "排名", "玩家", "输赢金额", "是否财神爺", "规则"]);
    AppState.settleRecords.forEach(rec => {
        const rule = `指定第${rec.goldRank}名`;
        rec.ranked.forEach((item, idx) => {
            const r = idx + 1;
            sheet4.push([
                idx === 0 ? rec.time : "",
                `第${r}名`,
                item.user,
                item.amount,
                r === rec.goldRank ? "是👑" : "否",
                idx === 0 ? rule : ""
            ]);
        });
        sheet4.push([]);
    });

    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(sheet1), "实时战报");
    XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(sheet2), "计数统计");
    XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(sheet3), "胡牌统计");
    if (AppState.settleRecords.length > 0)
        XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(sheet4), "输赢结算");

    // Sheet5 称号鉴定
    const titleResult = calcTitles();
    if (titleResult.length > 0) {
        const sheet5 = [];
        sheet5.push(["🏆 称号说明"]);
        const rules = [
            "放炮最多的称为放炮王",
            "获胜最多的叫做“他是真的想赢”",
            "自摸次数最多的称为“我靠我自己！”",
            "截胡最多的叫做“真的不当人”",
            "被截胡数最多的叫做“谁还比我惨”",
            "泥鳅最多的称为泥鳅王",
            "3财神、4白板、天&地胡三者计数和最高的称为“狗运真的好！”",
            "第一张被跟、姥姥、诈胡三者计数和最高的称为“操作拉跨王”",
            "30胡和40胡计数最多的称为“屁胡王！”",
            "50-80胡计数最多的称为“不贪王”",
            "210-390胡计数最高的称为“哥们胡很大但也没那么大”",
            "400胡计数最多的称为“饭没吃饱就请你们吃辣子！”",
            "作为军师时放炮最多的称为“灵犀一指狗头军师”",
            "作为军师时放炮最少的称为“神机妙算诸葛孔明”"
        ];
        rules.forEach(r => sheet5.push([r]));
        sheet5.push([]);
        sheet5.push(["=================="]);
        sheet5.push(["🎖️ 封神榜"]);
        sheet5.push(["称号", "得主", "次数/统计"]);
        titleResult.forEach(row => sheet5.push([row[0], row[1], row[2]]));
        XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(sheet5), "称号鉴定");
    }

    XLSX.writeFile(wb, `${site}_${getDateStr()}_麻将战报.xlsx`);
}