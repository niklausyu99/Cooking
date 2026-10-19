# 家庭专属链接同步 · Supabase Free

状态：所有者已确认执行初始化 SQL，公开配置已填入。正式入口为 https://niklausyu99.github.io/Little-Basket/ 。真实有效家庭链接的双设备读写由家庭设备验收；公开配置不包含家庭权限。

## 一次设置

1. Supabase 项目使用 Free。马来西亚家庭推荐 Singapore 地区。保留 **Enable Data API**、**Enable automatic RLS**，关闭 **Automatically expose new tables**，保持默认 Postgres。
2. 打开 Supabase 左侧 **SQL Editor → New query**。复制 [setup_family.sql](setup_family.sql) 的全部内容，点击 **Run**。它包含建表、限制访问的函数及创建家庭三个步骤；不需要开邮箱认证、创建用户或填写登录密码。
3. 结果会返回 `family_id` 和 `family_connection_code`。**连接码只保留在你自己的设备，不要发到对话、提交 GitHub 或填入公开配置。** 此脚本只在没有家庭时创建一份；重复运行不会覆盖现有家庭，也不会再次显示旧码。已有家庭而遗失链接时，使用下面的换链接方法。
4. [site-config.json](../site-config.json) 已填入你提供的 Project URL 和 Publishable key；这是允许出现在前端的公开配置，不包含家庭权限。环境变量 `SUPABASE_URL`、`SUPABASE_PUBLISHABLE_KEY` 可覆盖它。切勿使用 Secret key、service_role 或数据库密码。
5. 在 GitHub 仓库 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。合并或推送到 `main` 后运行 **Publish Little Basket**。只上传 `dist/` 内两个 HTML、`.nojekyll`、manifest、service worker 和安装图标，不上传设计工具、SQL 或项目文档。GitHub Free 的 Pages 对公开仓库免费；若仓库为私有且当前套餐不支持 Pages，可改用支持私有仓库的免费静态托管，不要为此擅自公开仓库。
6. 也可直接在 App「家庭同步」粘贴初始化时自己保存的连接码，无需手工拼网址。部署成功后，使用 GitHub Pages 实际显示的网站地址，并在末尾加 `#family=你的连接码`。例如 `https://你的站点/#family=64位连接码`；若已有路径，保留路径。第一次用完整链接打开后会自动连接并记住浏览器，验证成功会移除地址栏中的连接码。
7. App 顶部 **家庭同步 → 分享给家人** 会生成完整专属链接。家人点击即进入，没有邮箱、注册和密码步骤。普通网站地址在未连接的设备只提供本机模式，不能读取家庭记录。

手机使用浏览器打开实际 HTTPS 网站，可添加至主屏幕。不要用手机系统的 HTML 文件预览器。应用打开后断网仍可操作，恢复网络会补传；正式构建使用 service worker 缓存公开页面，首次完整联网加载后支持断网重开。缓存不包含 Supabase 请求或家庭密钥。iPhone 用 Safari 分享→添加到主屏幕，保持「作为网页 App 打开」（如有）；Android 用 Chrome 安装。安装后若没有继承浏览器连接，在独立 App 的「家庭同步」粘贴家庭链接或初始连接码一次。安装本身不授予家庭数据访问权。

## 同步与数据保护

- 清单、菜谱修改、库存余量和完整采购历史一起同步；界面导航不写入云端。
- 每次修改约 650ms 后保存，前台每 20 秒检查版本；返回 App 或恢复网络时重试。它不是后台常驻服务。
- 没有个人账户。所有持有家庭链接的人有同等读写权限。256 位随机码只在浏览器中保存，并通过 HTTPS 请求正文传递；数据库只保存 SHA-256 摘要。不得把完整链接放进仓库、公开网页或截图。
- 数据表放在非公开 `private` schema，启用 RLS 并撤销匿名表权限；公开 Data API 只允许执行两个检查连接码的 RPC。关闭默认表暴露不会妨碍这两个显式授权函数。
- `revision` 原子更新防止两台设备相互覆盖。若双方都修改了，暂停同步，请选择保留哪一份；在替换前下载另一份 JSON。当前采用整份厨房记录冲突处理，不提供逐项实时合并。
- 本机模式与每个家庭各自缓存。断开连接只影响此设备，不删除云端、其他家庭或待同步缓存。首次有本机记录时，先确认是否迁入家庭厨房。
- 「开始新的一趟」和每日重置只清空当前选购，余量与采购记录保留；重置会同步给家人。
- JSON 导出不包含连接码；导入会确认替换，连接家庭时也会同步这次替换。备份仍用于误操作恢复、迁移及暂停服务期间的数据保留。

## 换家庭链接

遗失或泄漏链接时，在 SQL Editor 打开 [rotate_family_link.sql](rotate_family_link.sql)，将占位 UUID 改成现有 `family_id` 后执行。数据不变，旧链接立即失去云端访问权限。用新码生成链接，在各设备重新打开。设备上的旧缓存仍可能保留，不会远程擦除。

## Free 配额与暂停

Supabase 官方价格配置（核查于 2026-10-19）：Free 为 $0/月，数据库 500 MB、文件存储 1 GB、出站流量 5 GB，最多两个活跃 Free 项目；约一周无活动的项目可能暂停。详见 [官方价格](https://supabase.com/pricing) 与 [官方价格源配置](https://github.com/supabase/supabase/blob/master/packages/shared-data/plans.ts)。免费规则可能变化，以控制台为准。

500 MB 数据库保存 JSON 格式的菜谱、食材目录、清单、库存余量、购买日期与数据库索引。内联 SVG、页面代码由静态网站提供；本方案不上传食物照片和视频，也不创建前端邮箱账户。家庭文字记录通常远小于配额，但不把历史容量估计当成保证。

只打开静态网页不等于数据库活动；已接通后读取厨房、同步修改才会产生 Supabase 请求。不要求每次都写入数据，但官方价格文字未给出精确的活动判定阈值，不能保证随意打开一次就永不暂停。未设置为了保活而自动刷请求的任务。暂停后所有者可能需要到控制台恢复项目；本机已有记录仍保留。

## 开发验证

```bash
python3 scripts/build_site.py --require-cloud
python3 tests/test_app.py
python3 tests/test_cloud_sync.py
python3 tests/test_build_site.py
python3 tests/test_pwa.py
```

同步测试通过可控 RPC 替身检查双设备、冲突、无效链接、隔离与离线队列；它不替代真实 PostgreSQL 权限测试和上线后双手机验收。真实验收：A 设备加一项，B 打开同一链接收到；B 勾选并调余量，A 返回收到记录；新浏览器只打开普通网址无法读到家庭数据。
