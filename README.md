# DSH 社区插件索引 / DSH Community Index

DeepSeek Harness（dsh）内置「插件 → 发现」标签页可读取的**插件市场索引**，格式严格遵循官方
`@deepseek-ai/dsh-plugin-market-index` 的 **format 1** 契约。

官方明确不提供官方市场（见 `dsh-experimental-plugin-market-bundle` 的已知限制），所以这个索引
从社区侧生成：抓 npm 的 `dsh-plugin` 关键词，按流行度排序，补上分类、作者、仓库和发布时间。

## 索引地址

```
https://gcore.jsdelivr.net/gh/Sher-ryKarl/dsh-market-index@main/market-index.json
```

> dsh 的 `plugin-market` 服务**拒绝重定向**，所以请用上面这个 jsDelivr 直连地址；
> `raw.githubusercontent.com` 在国内不可达，`registry.npmmirror.com/.../files/...` 是 302 跳转，都不能用。

## 在 dsh 里添加

1. 侧栏 → **插件** → **发现** 标签页
2. 粘贴上面的地址 → 添加
3. 之后即可浏览、按分类筛选、一键安装

配置文件方式（等价）：在 profile 的 `cordis.patch.yml` 里

```yaml
- id: plugin-market
  config:
    indexes:
      - https://gcore.jsdelivr.net/gh/Sher-ryKarl/dsh-market-index@main/market-index.json
```

## 索引内容

- 条目数：约 90–120（每次构建按当时流行度截取）
- 分类：模型与运行时 / 科研 / 编码 / 上下文与记忆 / 界面 / 基础设施 / 其他
- 每个条目只列出 `latest` 版本，安装时由 dsh 解析为 `name@version`

## 自动更新

`.github/workflows/refresh.yml` 每日 03:17 UTC 重建一次，内容有变化才提交。
手动触发：Actions → refresh-index → Run workflow。

本地重建：

```bash
python build_index.py 120
```

## 校验

生成物必须能通过官方解析器，否则发现页会以 `plugin-market/invalid-index` 拒绝加载：

```bash
npm i @deepseek-ai/dsh-plugin-market-index
node -e "const{parseMarketIndex}=require('@deepseek-ai/dsh-plugin-market-index');\
const d=JSON.parse(require('fs').readFileSync('market-index.json','utf8'));\
console.log(parseMarketIndex(d,'https://example.com/market-index.json').plugins.length)"
```

## 免责

索引只做发现，不对任何第三方插件的安全性背书。安装前请自行核对来源仓库。
