window.addEventListener('load', function () {
    console.log('========== 三档宝箱排序脚本启动 ==========');

    const containers = document.querySelectorAll('div.chest-list');
    console.log(`找到 ${containers.length} 个宝箱容器`);

    if (containers.length === 0) {
        console.error('❌ 未找到 .chest-list 容器，检查 div 类名和渲染');
        return;
    }

    containers.forEach((container, idx) => {
        try {
            const ul = container.querySelector('ul');
            if (!ul) {
                console.warn(`第${idx+1}个容器内无 ul 列表，检查 div 和列表间是否空行`);
                return;
            }

            const items = Array.from(ul.querySelectorAll('li'));
            const purple = [];   // 紫色宝箱（最高优先级）
            const gold = [];     // 金色宝箱（次优先级）
            const silver = [];   // 银色宝箱（最低优先级）
            const others = [];   // 未匹配条目（保留在底部）

            items.forEach((li, i) => {
                const rawText = li.textContent.trim();
                const cleanText = rawText.replace(/\s+/g, '');
                const checkbox = li.querySelector('input[type="checkbox"]');

                console.log(`第${i+1}项：「${rawText}」`);

                // 1. 匹配紫色宝箱（最高级）
                if (cleanText.includes('紫色宝箱')) {
                    li.classList.add('chest-purple');
                    if (!li.querySelector('.chest-icon')) {
                        const icon = document.createElement('span');
                        icon.className = 'chest-icon';
                        icon.textContent = '🔮 ';
                        try {
                            if (checkbox && checkbox.parentNode) {
                                checkbox.parentNode.insertBefore(icon, checkbox.nextSibling);
                            } else {
                                li.insertBefore(icon, li.firstChild);
                            }
                        } catch(e) {
                            li.prepend(icon);
                        }
                    }
                    purple.push(li);
                    console.log('  → 归为：紫色宝箱');
                }
                // 2. 匹配金色宝箱（次高级）
                else if (cleanText.includes('金色宝箱')) {
                    li.classList.add('chest-gold');
                    if (!li.querySelector('.chest-icon')) {
                        const icon = document.createElement('span');
                        icon.className = 'chest-icon';
                        icon.textContent = '👑 ';
                        try {
                            if (checkbox && checkbox.parentNode) {
                                checkbox.parentNode.insertBefore(icon, checkbox.nextSibling);
                            } else {
                                li.insertBefore(icon, li.firstChild);
                            }
                        } catch(e) {
                            li.prepend(icon);
                        }
                    }
                    gold.push(li);
                    console.log('  → 归为：金色宝箱');
                }
                // 3. 匹配银色宝箱（普通级）
                else if (cleanText.includes('银色宝箱')) {
                    li.classList.add('chest-silver');
                    if (!li.querySelector('.chest-icon')) {
                        const icon = document.createElement('span');
                        icon.className = 'chest-icon';
                        icon.textContent = '🥈 ';
                        try {
                            if (checkbox && checkbox.parentNode) {
                                checkbox.parentNode.insertBefore(icon, checkbox.nextSibling);
                            } else {
                                li.insertBefore(icon, li.firstChild);
                            }
                        } catch(e) {
                            li.prepend(icon);
                        }
                    }
                    silver.push(li);
                    console.log('  → 归为：银色宝箱');
                }
                // 4. 未匹配条目保留
                else {
                    others.push(li);
                    console.log('  → 未匹配，保留在底部');
                }
            });

            console.log(`\n第${idx+1}个列表统计：紫色${purple.length} | 金色${gold.length} | 银色${silver.length} | 其他${others.length}`);

            // 按优先级重排：紫色 → 金色 → 银色 → 其他
            ul.innerHTML = '';
            purple.forEach(li => ul.appendChild(li));
            gold.forEach(li => ul.appendChild(li));
            silver.forEach(li => ul.appendChild(li));
            others.forEach(li => ul.appendChild(li));
            console.log(`第${idx+1}个列表重排完成`);

        } catch (e) {
            console.error(`❌ 第${idx+1}个容器处理出错：`, e);
        }
    });

    console.log('========== 脚本执行完毕 ==========');
});