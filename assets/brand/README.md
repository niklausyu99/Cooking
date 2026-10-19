# 菜篮子品牌图形

2026-10-19 按用户选定的方案一生成：柔和手绘 2D 藤编菜篮与叶菜，名称仍为「菜篮子 · Little Basket」，与现有食物插画保持一致。

- `source.png`：保留完整透明母图，由当前 image generation 工具生成。原生成文件：`/workspace/generated_images/exec-46dbe17b-deea-472d-923e-d557afa29e23.png`。不依赖该临时路径重建。
- `header.webp`：128 × 128 透明画布，约 8 KB，质量 92；只在 HTML 内嵌一次。
- `../../pwa/icons/`：192、512、Apple touch 180 和 favicon 32 px，不透明米白底，留出 maskable 安全区，无预裁圆角。

`python3 scripts/prepare_brand_assets.py` 使用 Pillow、numpy、scipy 从保留母图清理零散透明边缘、裁切完整轮廓并缩放，不重新绘画。普通部署不需要这些制图依赖，也不会上传母图：构建仅复制安装图标与公开页面。
