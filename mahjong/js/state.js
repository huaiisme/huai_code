// 全局状态管理
const AppState = {
    users: [...DEFAULT_USERS],
    records: [],
    settleRecords: [],
    
    // 极速胡牌状态机
    fastState: {
        huUser: "",
        huScore: 0,
        type: "", // "pao" or "zimo"
        paoUser: "",
        tile: { char: "", name: "" }
    },

    // 军师系统状态
    military: {
        active: false,
        user: "",
        target: ""
    }
};