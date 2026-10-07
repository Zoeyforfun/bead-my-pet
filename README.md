# Zoey Pindou Skill

把人物、宠物、玩偶或物品照片转换为**高还原、可实际制作**的拼豆图纸。

本项目不以“把照片直接缩小”为目标，而是先识别外轮廓、五官、关键花纹和主色关系，再根据目标网格做受控简化：优先省略细毛、弱渐变和反光，不用通用卡通模板替代原主体。

## 功能亮点

- 保留脸型、耳尖、五官比例、关键花纹和主色关系；
- 支持单张或多张同一主体的参考图；
- 支持 29×29、38×38、58×58 等任意网格；
- 为不同尺寸分别优化，不机械缩放同一网格；
- 支持普通平面款、钥匙扣款和轻微局部编辑；
- 输出纯图案预览、标准 PNG、单页 PDF、MARD 色号和豆数统计；
- 标准图纸包含四边坐标与 5×5 粗分区，方便实际拼制。

## 工作方式

完整流程分为六步：

1. **锁定身份锚点**：记录主体轮廓、五官位置、关键尖角、花纹路径和主色区域。
2. **提取主体**：清理背景并保留真实形状，不默认动漫化或夸张五官。
3. **生成网格**：针对每个目标尺寸独立归纳色块，生成 `pattern.json` 和 `counts.csv`。
4. **纯图案验收**：先检查不带坐标和色号的预览，确认轮廓与身份特征准确。
5. **标准图纸渲染**：生成带坐标、5×5 分区、MARD 色号和豆数统计的 PNG/PDF。
6. **最终核验**：确认图纸、统计和 PDF 来自同一份网格数据，并检查可制作性。

详细执行规则见 [SKILL.md](SKILL.md)。

## 使用方法

### 方式一：在支持 Skill 的 Agent 中使用

将本目录作为 Skill 加载后，上传清晰照片并用自然语言描述需求即可。

最小输入只需要：

- 一张清晰的 JPG 或 PNG；
- 要保留的主体区域，如“猫头”“人物头像”或“全身”；
- 目标网格尺寸，如 `38×38`。

示例：

```text
提取这张照片里的猫头，保持真实脸型、耳尖、眼睛、鼻嘴和虎斑，
生成 38×38 和 58×58 两套拼豆图纸。
```

```text
把这个人物头像做成 29×29 拼豆，不要卡通化，
控制在 12 色以内，并输出可打印 PDF。
```

```text
基于同一张照片生成 58×58 普通款和钥匙扣款，
挂环放在头顶中间，保留完整发型轮廓。
```

多图输入时，建议明确主参考图：

```text
第一张作为主图，保持它的构图、脸型和五官比例；
第二张只用于补充被遮挡的耳朵与毛色。
```

### 方式二：独立使用渲染脚本

仓库内的两个脚本可脱离 Agent 单独使用。它们不负责照片分析和网格生成，只负责把已经生成的 `pattern.json` 与 `counts.csv` 渲染为预览图和标准图纸。

#### 1. 安装运行依赖

```bash
python3 -m pip install Pillow
```

标准图纸脚本默认使用 Linux DejaVu Sans 字体：

```text
/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf
```

若系统没有这些字体，请安装 DejaVu 字体，或修改 `scripts/render_standard_chart.py` 顶部的字体路径。

#### 2. 准备网格数据

`pattern.json` 至少包含二维 `cells` 数组。每个元素是 MARD 色号或 `null`；所有行必须等宽。

```json
{
  "grid": 4,
  "cells": [
    [null, "H10", "H10", null],
    ["H10", "H6", "H6", "H10"],
    ["H10", "E21", "E21", "H10"],
    [null, "H10", "H10", null]
  ]
}
```

`counts.csv` 必须包含以下列名：

```csv
MARD色号,HEX屏幕参考,颗数
H10,#EEE9EA,8
H6,#2F2B2F,2
E21,#BD9DA1,2
```

其中：

- `MARD色号`：写入网格中的色号；
- `HEX屏幕参考`：预览和图纸使用的屏幕颜色；
- `颗数`：该色号的豆数统计。

#### 3. 生成纯图案预览

```bash
python3 scripts/render_pattern_preview.py \
  --pattern /absolute/path/to/pattern.json \
  --counts /absolute/path/to/counts.csv \
  --output /absolute/path/to/pure_preview.png
```

可使用 `--cell-size` 调整每格预览像素，默认值为 `20`：

```bash
python3 scripts/render_pattern_preview.py \
  --pattern pattern.json \
  --counts counts.csv \
  --output preview.png \
  --cell-size 24
```

纯预览不显示网格、坐标和色号，适合优先检查：

- 主体外轮廓是否准确；
- 五官和关键部件是否仍可辨认；
- 花纹位置是否正确；
- 是否存在孤立碎色或错误色相。

#### 4. 生成标准 PNG/PDF 图纸

```bash
python3 scripts/render_standard_chart.py \
  --pattern /absolute/path/to/pattern.json \
  --counts /absolute/path/to/counts.csv \
  --out-prefix /absolute/path/to/output_name
```

将生成：

```text
output_name.png
output_name.pdf
```

对于非正方形作品，可使用 `--target-height` 指定裁切空行后的目标高度：

```bash
python3 scripts/render_standard_chart.py \
  --pattern pattern.json \
  --counts counts.csv \
  --out-prefix output/cat_head_38x26 \
  --target-height 26
```

如果实际内容高度超过 `--target-height`，脚本会停止并提示重新生成图案，避免通过拉伸或裁断破坏主体。

## 推荐输入质量

为提高还原效果，建议照片满足：

- 主体清晰，关键轮廓没有被大面积遮挡；
- 光线自然，没有严重偏色或过曝；
- 人物或宠物尽量正面，尤其是小尺寸头像图纸；
- 多张参考图属于同一主体，并明确哪张控制构图；
- 提前说明必须保留的特征，如耳尖、眼睛颜色、额纹、配饰或挂环位置。

## 输出内容

典型交付目录包含：

```text
output/
├── subject_extracted.png
├── subject_38x38_preview.png
├── subject_38x38.png
├── subject_38x38.pdf
├── subject_58x58_preview.png
├── subject_58x58.png
└── subject_58x58.pdf
```

建议同时提供：

- 每个尺寸的使用色数和总豆数；
- 小尺寸中主动省略的次要细节；
- 大尺寸相对小尺寸新增的身份信息；
- 钥匙扣款的连通性和挂环安全检查结果。

## 质量标准

可交付图纸至少满足：

- 一眼可辨为同一主体，而不只是同一物种或同类物品；
- 外轮廓、五官比例、关键花纹与主色关系准确；
- 小尺寸允许简化，但不优先删除眼鼻嘴、耳尖或关键标志；
- 大面积色块连续，没有大量近似色抖动或孤立噪点；
- PNG、PDF、色号和豆数统计相互一致；
- 大尺寸相比小尺寸增加有效身份细节，而不是只增加碎纹。

## 项目结构

```text
zoey-pindou-skill/
├── SKILL.md
├── README.md
├── .skillignore
└── scripts/
    ├── render_pattern_preview.py
    └── render_standard_chart.py
```

## 外部能力与边界

本 Skill 负责照片转拼豆的完整工作流和质量标准，但当前仓库内置脚本只覆盖最终渲染阶段。端到端运行还需要：

- 图像编辑或抠图能力，用于提取主体、清理背景和局部修正；
- 确定性网格转换能力，用于生成 `pattern.json` 与 `counts.csv`；
- 图像对比能力，用于核验原图、提取图和最终图纸。

在 Aime 环境中，`SKILL.md` 声明了对应能力；在其他 Agent 或本地工作流中，可以接入等价工具，只需保持上述输入输出格式与验收标准。

## 贡献建议

欢迎围绕以下方向改进：

- 更多拼豆品牌与色号体系；
- 更便携的跨平台字体处理；
- 网格生成和颜色量化脚本；
- 自动身份锚点提取与误差报告；
- 钥匙扣连通性和结构强度检查；
- 更多真实照片到拼豆图纸的对比示例。
