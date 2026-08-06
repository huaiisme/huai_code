const titleModal = document.getElementById("titleModal");

function initTitle() {
    document.getElementById("btnTitle").addEventListener("click", openTitleModal);
    document.getElementById("btnCloseTitle").addEventListener("click", () => closeModal(titleModal));
}

// 计算所有称号
function calcTitles() {
    const base = calcBaseStats();
    const titleData = [];

    // 找最大值（支持平局）
    const findMax = (keyFn) => {
        let maxVal = -1;
        let maxUsers = [];
        AppState.users.forEach(u => {
            const val = keyFn(base[u] || {});
            if (val > maxVal) {
                maxVal = val;
                maxUsers = [u];
            } else if (val === maxVal && val > 0) {
                maxUsers.push(u);
            }
        });
        return { users: maxUsers, count: maxVal };
    };

    // 找最小值（支持平局）
    const findMin = (keyFn) => {
        let minVal = Infinity;
        let minUsers = [];
        AppState.users.forEach(u => {
            const val = keyFn(base[u] || {});
            if (val > 0) {
                if (val < minVal) {
                    minVal = val;
                    minUsers = [u];
                } else if (val === minVal) {
                    minUsers.push(u);
                }
            }
        });
        return { users: minUsers, count: minVal };
    };

    // 1. 放炮王
    const pao = findMax(d => d.p);
    if (pao.users.length > 0)
        titleData.push(["放炮王", pao.users.join("、"), pao.count, "放炮最多的称为放炮王"]);

    // 2. 他是真的想赢
    const win = findMax(d => d.w);
    if (win.users.length > 0)
        titleData.push(["他是真的想赢", win.users.join("、"), win.count, "获胜最多的叫做“他是真的想赢”"]);

    // 3. 我靠我自己！
    const zimo = findMax(d => d.z);
    if (zimo.users.length > 0)
        titleData.push(["我靠我自己！", zimo.users.join("、"), zimo.count, "自摸次数最多的称为“我靠我自己！”"]);

    // 4. 真的不当人
    const jie = findMax(d => d.j);
    if (jie.users.length > 0)
        titleData.push(["真的不当人", jie.users.join("、"), jie.count, "截胡最多的叫做“真的不当人”"]);

    // 5. 谁还比我惨
    const beiJie = findMax(d => d.bj);
    if (beiJie.users.length > 0)
        titleData.push(["谁还比我惨", beiJie.users.join("、"), beiJie.count, "被截胡数最多的叫做“谁还比我惨”"]);

    // 6. 泥鳅王
    const niqiu = findMax(d => d.n);
    if (niqiu.users.length > 0)
        titleData.push(["泥鳅王", niqiu.users.join("、"), niqiu.count, "泥鳅最多的称为泥鳅王"]);

    // 7. 狗运真的好！
    const luck = findMax(d => (d.c3 || 0) + (d.b4 || 0) + (d.tdh || 0));
    if (luck.users.length > 0)
        titleData.push(["狗运真的好！", luck.users.join("、"), luck.count, "3财神、4白板、天&地胡三者计数和最高的称为“狗运真的好！”"]);

    // 8. 操作拉跨王
    const caip = findMax(d => (d.bg || 0) + (d.ll || 0) + (d.zh || 0));
    if (caip.users.length > 0)
        titleData.push(["操作拉跨王", caip.users.join("、"), caip.count, "第一张被跟、姥姥、诈胡三者计数和最高的称为“操作拉跨王”"]);

    // 9. 灵犀一指狗头军师
    const milMax = findMax(d => d.militaryP);
    if (milMax.users.length > 0)
        titleData.push(["灵犀一指狗头军师", milMax.users.join("、"), milMax.count, "作为军师时累计分锅（放炮）最多的人"]);

    // 10. 神机妙算诸葛孔明
    const milMin = findMin(d => d.militaryP);
    if (milMin.users.length > 0)
        titleData.push(["神机妙算诸葛孔明", milMin.users.join("、"), milMin.count, "作为军师时累计分锅（放炮）最少的人"]);

    // 11. 屁胡王！
    const hu30_40 = findMax(d => d.hu30_40);
    if (hu30_40.users.length > 0)
        titleData.push(["屁胡王！", hu30_40.users.join("、"), hu30_40.count, "30胡和40胡计数最多的称为“屁胡王！”"]);

    // 12. 不贪王
    const hu50_80 = findMax(d => d.hu50_80);
    if (hu50_80.users.length > 0)
        titleData.push(["不贪王", hu50_80.users.join("、"), hu50_80.count, "50-80胡计数最多的称为“不贪王”"]);

    // 13. 饭没吃饱就请你们吃辣子！
    const hu400 = findMax(d => d.hu400);
    if (hu400.users.length > 0)
        titleData.push(["饭没吃饱就请你们吃辣子！", hu400.users.join("、"), hu400.count, "400胡计数最多的称为“饭没吃饱就请你们吃辣子！”"]);

    // 14. 哥们胡很大但也没那么大
    const hu210_390 = findMax(d => d.hu210_390);
    if (hu210_390.users.length > 0)
        titleData.push(["哥们胡很大但也没那么大", hu210_390.users.join("、"), hu210_390.count, "210-390胡计数最高的称为“哥们胡很大但也没那么大”"]);

    return titleData;
}

// 打开称号弹窗
function openTitleModal() {
    if (!getSelectedSite()) return;
    if (AppState.records.length === 0) {
        alert("暂无数据，无法鉴定！");
        return;
    }

    const titleResult = calcTitles();

    // 填充规则
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
        "作为军师时累计分锅（放炮）最多的称为“灵犀一指狗头军师”",
        "作为军师时累计分锅（放炮）最少的称为“神机妙算诸葛孔明”"
    ];
    document.getElementById("titleRules").innerHTML = rules.map(r =>
        `<div class="title-rule-item">• ${r}</div>`
    ).join("");

    // 填充结果
    if (titleResult.length === 0) {
        document.getElementById("titleResults").innerHTML = '<div class="empty-tip">暂无封神数据</div>';
    } else {
        document.getElementById("titleResults").innerHTML = titleResult.map(row => `
            <div class="title-result-item">
                <div>
                    <span class="title-name">${row[0]}</span>
                    <span style="color:#999;font-size:12px;margin-left:5px;">(${row[3]})</span>
                </div>
                <div>
                    <span class="title-owner">${row[1]}</span>
                    <span class="title-count">(${Number.isInteger(row[2]) ? row[2] : row[2].toFixed(1)}次)</span>
                </div>
            </div>
        `).join("");
    }

    openModal(titleModal);
}