// 麻将牌配置
const tileConfig = {
    wan: [
        { char: "🀇", name: "一万" },{ char: "🀈", name: "二万" },{ char: "🀉", name: "三万" },
        { char: "🀊", name: "四万" },{ char: "🀋", name: "五万" },{ char: "🀌", name: "六万" },
        { char: "🀍", name: "七万" },{ char: "🀎", name: "八万" },{ char: "🀏", name: "九万" }
    ],
    tiao: [
        { char: "🀐", name: "一条" },{ char: "🀑", name: "二条" },{ char: "🀒", name: "三条" },
        { char: "🀓", name: "四条" },{ char: "🀔", name: "五条" },{ char: "🀕", name: "六条" },
        { char: "🀖", name: "七条" },{ char: "🀗", name: "八条" },{ char: "🀘", name: "九条" }
    ],
    tong: [
        { char: "🀙", name: "一筒" },{ char: "🀚", name: "二筒" },{ char: "🀛", name: "三筒" },
        { char: "🀜", name: "四筒" },{ char: "🀝", name: "五筒" },{ char: "🀞", name: "六筒" },
        { char: "🀟", name: "七筒" },{ char: "🀠", name: "八筒" },{ char: "🀡", name: "九筒" }
    ],
    zi: [
        { char: "🀀", name: "东" },{ char: "🀁", name: "南" },{ char: "🀂", name: "西" },
        { char: "🀃", name: "北" },{ char: "🀄", name: "中" },{ char: "🀅", name: "发" },{ char: "🀆", name: "白" }
    ]
};

// 默认用户列表
const DEFAULT_USERS = ["怀神", "苏少", "严总", "王总", "P神"];

// 胡数范围配置
const HU_CONFIG = {
    min: 30,
    max: 400,
    step: 10
};