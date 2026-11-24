/* 聚合站点搜索结果按项目来源着色 */
document.addEventListener("DOMContentLoaded", function () {
  var container = document.querySelector(".search");
  if (!container) return;

  var observer = new MutationObserver(function () {
    var items = container.querySelectorAll(".search-result");
    items.forEach(function (el) {
      var title = el.querySelector(".search-result-title");
      if (!title) return;
      if (/^\[(BevFusion|FileTree|MultiSensorPostFusion)\]/.test(title.textContent || "")) {
        el.style.borderLeft = "4px solid #2980b9";
        el.style.paddingLeft = "8px";
      }
    });
  });

  observer.observe(container, { childList: true, subtree: true });
});
