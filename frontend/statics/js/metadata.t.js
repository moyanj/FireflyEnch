const VERSION = '{{ version }}';
const BUILD_TYPE = '{{ type }}';
const base_url = '{{ base_url }}';
const BUILD_TIME = {{ build_timestamp }};

$(document).ready(function() {
    var maxAttempts = 5; // 设置最大尝试次数

    // 为所有img元素绑定load和error事件
    $('img').on('load', function() {
        // 图片加载成功时执行的操作
        $(this).data('attempts', 0); // 重置尝试次数
    }).on('error', function() {
        var currentAttempts = $(this).data('attempts') || 0;

        // 图片加载失败时执行的操作
        if (currentAttempts < maxAttempts) {
            // 增加尝试次数
            $(this).data('attempts', currentAttempts + 1);

            // 尝试重新加载图片
            var src = $(this).attr('src');
            var newSrc = src + (src.indexOf('?') === -1 ? '?' : '&') + 'retry=' + new Date().getTime();
            $(this).attr('src', newSrc);
        } else {
            // 如果达到最大尝试次数，显示占位符图片
            $(this).attr('src', '/statics/img/error.webp');
        }
    });
});