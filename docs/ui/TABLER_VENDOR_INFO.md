# StarMem Tabler Vendor 信息

## 锁定来源

| 项 | 值 |
| --- | --- |
| Tabler repository | `https://github.com/tabler/tabler.git` |
| Commit SHA | `0776b88863690c9740d7d33988a8b5df66aad6dc` |
| Version | `1.5.1`（`core/package.json` / build banner） |
| Clone time | `2026-09-16 17:24:21 +0800` |
| Local source | `.reference/tabler` |
| Install command | `pnpm install --frozen-lockfile` |
| Build command | `pnpm run build` |
| Preview command | `pnpm --filter @tabler/preview dev` |
| CSS build source | `.reference/tabler/core/dist/css/tabler.css`、`.reference/tabler/core/dist/css/tabler-vendors.css`、`.reference/tabler/core/dist/libs/dropzone/dist/dropzone.css` |
| JS build source | `.reference/tabler/core/dist/js/tabler.esm.js` |
| Theme JS source | `.reference/tabler/core/dist/js/tabler-theme.esm.js` |
| StarMem vendor path | `web/src/vendor/tabler/` |

## Copied files

以下文件均从上述 commit 的官方构建产物或其锁定依赖原样复制，vendor 文件只读，不在 StarMem 中修改：

- `tabler.css` / `tabler.css.map`
- `tabler.min.css` / `tabler.min.css.map`
- `tabler.esm.js` / `tabler.esm.js.map`
- `tabler.esm.min.js` / `tabler.esm.min.js.map`
- `tabler-theme.esm.js` / `tabler-theme.esm.js.map`
- `tabler-theme.esm.min.js` / `tabler-theme.esm.min.js.map`
- `tabler-vendors.css` / `tabler-vendors.css.map`
- `dropzone.css` / `dropzone.css.map`

`tabler-vendors.css` 与 `dropzone.css` 为官方 Dropzone Composition 所需的插件样式；StarMem 保留自己的 API 提交流程，仅复用其官方 DOM/class 与样式。`dropzone.css.map` 来自同一构建锁定的 `dropzone@6.0.0-beta.2` 包。

## SHA-256

```text
2c8ac142f1aa1a8e3b58a6556e48170fcb48f9f0e4fe8728e2ac818d6dd7729d  web/src/vendor/tabler/tabler.css
928ea48183d3807986d5dd3d55a1817525baa865f1608e243b9343fe2277e610  web/src/vendor/tabler/tabler.css.map
4de3d1f47cb4163dfc0b9793d411562f912b951d3b9181e33ba7f0df992fe579  web/src/vendor/tabler/tabler.min.css
2350d06736c58c627be25b45f0146f0c539eaf9ea4016d8ff65245717293ba97  web/src/vendor/tabler/tabler.min.css.map
3c72bdbf791d7531ce7d430ecff64893c0f9fb02f2d020ba971308ea73cf783c  web/src/vendor/tabler/tabler.esm.js
6d0ab77a716bc1012f743c23615b390e7bf95eb5bed04476e0d6dbceb581bc14  web/src/vendor/tabler/tabler.esm.js.map
82ab9aa062a941ea953dda7d6976672fd469de0265f5fa281dfa6f80e356f2da  web/src/vendor/tabler/tabler.esm.min.js
5ec944f9003a6f4825bd4ceb89dba6e17d3d11fb375499541f7602a023abcbed  web/src/vendor/tabler/tabler.esm.min.js.map
5e59d76a9ca355b4fd2bfd827a37d2ee1ec23147e9530cf44de3b93298584d87  web/src/vendor/tabler/tabler-theme.esm.js
1f2a8cd519e907331faf469456d20a420cf87e68eeb8510bde978f04c4d3e20c  web/src/vendor/tabler/tabler-theme.esm.js.map
e86f5e14cd6436a5b4444e15bfeaec4021d95b084e131a0e2acd206a4013f3e6  web/src/vendor/tabler/tabler-theme.esm.min.js
56781c39ab51bdfcb7d7d47f7483da3a1f278e63f236a467d9ae8bb207d89a3f  web/src/vendor/tabler/tabler-theme.esm.min.js.map
55a46a6d53fef2043077c74eb80fb65947370be9170a9399f377d263155edaaa  web/src/vendor/tabler/tabler-vendors.css
102f7450e6bd5f7e64d4c98f9d384b4df324a4b9085762a39e93d660727a5155  web/src/vendor/tabler/tabler-vendors.css.map
3a91e26988c6324e3e1d594231eb20fee96183ba05f731895aaea8cd5c6945a3  web/src/vendor/tabler/dropzone.css
8532731f82456f85d2f8305b2ff9a23248f1272cb56a1eb2f61e492269508ae2  web/src/vendor/tabler/dropzone.css.map
```

升级 Tabler 时必须重新执行官方 install/build，更新 commit/version、复制清单、checksum、source map 和迁移报告。
