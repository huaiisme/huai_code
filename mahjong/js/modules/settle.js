const settleModal = document.getElementById("settleModal");

function initSettle() {
    document.getElementById("btnSettle").addEventListener("click", openSettleModal);
    document.getElementById("btnSaveSettle").addEventListener("click", saveSettle);
    document.getElementById("btnCancelSettle").addEventListener("click", () => closeModal(settleModal));
}

function openSettleModal() {
    if (!getSelectedSite()) return;
    
    const inputs = document.getElementById("settleInputs");
    inputs.innerHTML = "";
    
    AppState.users.forEach(u => {
        const div = document.createElement("div");
        div.className = "settle-input-group";
        div.innerHTML = `<div class="settle-input-label">${u}</div><input type="number" class="settle-input" id="settle_${u}" placeholder="赢正输负" value="0">`;
        inputs.appendChild(div);
    });

    updateGoldRankOptions();
    openModal(settleModal);
}

function saveSettle() {
    const goldRank = parseInt(document.getElementById("goldRankSelect").value);
    const amounts = [];
    
    AppState.users.forEach(u => {
        const input = document.getElementById(`settle_${u}`);
        const val = parseFloat(input.value) || 0;
        amounts.push({ user: u, amount: val });
    });

    const ranked = [...amounts].sort((a, b) => b.amount - a.amount);
    if (goldRank > ranked.length) {
        alert("名次无效！");
        return;
    }

    const goldUser = ranked[goldRank - 1];
    const resultText = `本次指定第${goldRank}名为财神爷👑：${goldUser.user} 负责付钱！`;

    AppState.settleRecords.push({
        time: now(),
        goldRank: goldRank,
        goldUser: goldUser.user,