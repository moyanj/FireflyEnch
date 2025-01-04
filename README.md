# FireflyEnch

FireflyEnch 是一个简单的画廊系统，功能极其少，但是足够简单。满足了我大部分的需求。

## 功能

- 图片浏览
- 图片搜索
- 图片上传
- 图片删除

## 安装

```bash
git clone https://github.com/moyanj/FireflyEnch
cd FireflyEnch
make
docker run -p 8080:8080 -v /path/to/images:/moyan/imgs -v /path/to/config.json:/moyan/config.json fireflyench:2.4.6
```

## 配置

改 `config.json` 文件即可。

## 截图
