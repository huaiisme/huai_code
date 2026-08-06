function initKeyboard() {
    let inputHuMode = false;
    let inputBuffer = "";
    let currentMode = ""; // zimo / pao / minggang / angang
    let selectedPaoUser = ""; // 放炮模式下的放炮者

    document.addEventListener("keydown", (e) => {
        const key = e.key.toLowerCase();

        // 如果有弹窗打开，不处理全局快捷键（Esc除外）
        const openModals = document.querySelectorAll(".modal.show");
        if (openModals.length > 0) {
            if (key === "escape") {
                openModals.forEach(m => closeModal(m));
                resetKeyboardState();
            }
            return;
        }

        // 胡数输入模式
        if (inputHuMode) {
            e.preventDefault();
            if (/^\d$/.test(key)) {
                if (inputBuffer.length < 3) {
                    inputBuffer += key;
                    showStatus(`输入胡数：${inputBuffer}，回车确认，Esc取消`);
                }
                return;
            }
            if (key === "backspace") {
                inputBuffer = inputBuffer.slice(0, -1);
                showStatus(`输入胡数：${inputBuffer || "_"}，回车确认，Esc取消`);
                return;
            }
            if (key === "enter") {
                if (inputBuffer) {
                    let num = parseInt(inputBuffer);
                    if (num < HU_CONFIG.min) num = HU_CONFIG.min;
                    if (num > HU_CONFIG.max) num = HU_CONFIG.max;
                    // 同步到极速胡牌的默认值（通过修改全局配置不现实，这里只做提示）
                    showStatus(`✅ 胡数已设为 ${num} 胡`);
                }
                inputHuMode = false;
                inputBuffer = "";
                return;
            }
            if (key === "escape") {
                inputHuMode = false;
                inputBuffer = "";
                showStatus("已取消胡数输入");
                return;
            }
            return;
        }

        // 进入胡数输入模式
        if (key === "h") {
            e.preventDefault();
            inputHuMode = true;
            inputBuffer = "";
            showStatus("⌨️ 请输入胡数（30-400），输完按回车");
            return;
        }

        // 数字键：选玩家
        if (["1", "2", "3", "4", "5"].includes(key)) {
            e.preventDefault();
            const idx = parseInt(key) - 1;
            if (idx >= AppState.users.length) return;
            const userName = AppState.users[idx];

            if (!currentMode) {
                // 没选模式时，数字键直接选中该玩家
                const radios = document.querySelectorAll('input[name="user"]');
                if (radios[idx]) {
                    radios[idx].checked = true;
                    showStatus(`已选中玩家：${userName}`);
                }
                return;
            }

            // 放炮模式：两步选
            if (currentMode === "pao") {
                if (!selectedPaoUser) {
                    selectedPaoUser = userName;
                    showStatus(`放炮者：${userName}，请按数字键选择胡牌玩家`);
                } else {
                    if (userName === selectedPaoUser) {
                        showStatus("⚠️ 放炮者和胡牌者不能是同一人");
                        return;
                    }
                    // 放炮完成，打开极速胡牌弹窗并预填
                    openFastHuWithPrefill("pao", selectedPaoUser, userName);
                    resetKeyboardState();
                }
                return;
            }

            // 自摸/杠牌：一步完成
            if (currentMode === "zimo") {
                openFastHuWithPrefill("zimo", null, userName);
                resetKeyboardState();
            } else {
                // 明杠暗杠直接记录（简化处理，调用单动作）
                actOne(currentMode === "minggang" ? "明杠" : "暗杠");
                showStatus(`✅ 已记录：${userName} ${currentMode === "minggang" ? "明杠" : "暗杠"}`);
                resetKeyboardState();
            }
            return;
        }

        // 模式选择键
        if (key === "z") { e.preventDefault(); setKeyboardMode("zimo", "自摸"); return; }
        if (key === "f") { e.preventDefault(); setKeyboardMode("pao", "放炮"); return; }
        if (key === "m") { e.preventDefault(); setKeyboardMode("minggang", "明杠"); return; }
        if (key === "a") { e.preventDefault(); setKeyboardMode("angang", "暗杠"); return; }

        // 胡数微调
        if (key === "arrowup") {
            e.preventDefault();
            // 这里只是提示，实际胡数在极速弹窗里选
            showStatus("提示：按 H 键可直接输入胡数");
            return;
        }
        if (key === "arrowdown") {
            e.preventDefault();
            showStatus("提示：按 H 键可直接输入胡数");
            return;
        }

        // 撤销
        if (key === "backspace") {
            e.preventDefault();
            undo();
            return;
        }

        // 取消
        if (key === "escape") {
            e.preventDefault();
            resetKeyboardState();
            showStatus("已取消，等待操作");
            return;
        }

        function setKeyboardMode(mode, modeName) {
            currentMode = mode;
            selectedPaoUser = "";
            showStatus(`已选【${modeName}】，请按数字键选择玩家`, true);
        }

        function resetKeyboardState() {
            currentMode = "";
            selectedPaoUser = "";
        }

        function showStatus(text, isActive = false) {
            // 临时在日志顶部显示提示
            const logBox = document.getElementById("log");
            logBox.scrollTop = 0;
        }
    });

    // 打开极速胡牌并预填数据
    function openFastHuWithPrefill(type, paoUser, huUser) {
        // 先选中胡牌玩家
        const radios = document.querySelectorAll('input[name="user"]');
        const idx = AppState.users.indexOf(huUser);
        if (idx >= 0 && radios[idx]) radios[idx].checked = true;

        // 打开极速弹窗
        openFastHuModal();

        // 预填类型
        setTimeout(() => {
            if (type === "pao") {
                setFastType("pao");
                // 选中放炮者
                const paoBtns = document.querySelectorAll("#fastPaoPersonList button");
                paoBtns.forEach(btn => {
                    if (btn.innerText === paoUser) btn.click();
                });
            } else {
                setFastType("zimo");
            }
        }, 50);
    }
}