var $BP = {
    // 通过ua判断是否为爬虫
    isBot: function() {
        return /bot|googlebot|crawler|spider|yahoo|robot|crawling/i.test(navigator.userAgent);
    },
    // 初始化方法，判断是否为搜索引擎或不支持cookie
    onInit: function() {
        if ($BP.isBot()) {
            return true; // 是搜索引擎
        } else {
            return true; // 不是搜索引擎
        }
    }
}
function getQueryParams() {
    const params = new URLSearchParams(window.location.search);
    return Object.fromEntries(params.entries());
}

const queryParams = getQueryParams();