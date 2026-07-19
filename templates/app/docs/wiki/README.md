# <应用名> Wiki

> 面向"**快速定位代码**"的导航层:宏观结构与设计理由见 `../architecture.md`,此处只回答"在哪、怎么找、改哪里"。
> 首次由 `prompts/rebuild-wiki.md` 从代码生成;之后每个需求收尾时(finalize-feature)增量维护。

## 使用方式(AI 必读)

改代码前先查 [code-map.md](code-map.md) 定位相关文件与符号,再进对应模块页看"常见修改场景";查不到再全库搜索,并在完成后把结果补进 code-map。

## 模块索引

| 模块 | 职责 | 页面 |
|---|---|---|
| <模块名> | <一句话> | [modules/<模块名>.md](modules/) |
