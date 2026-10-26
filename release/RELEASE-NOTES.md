# Coot-1.3.3-backbone-torsion-re.app

Coot 1.3.3 的 Edit Backbone Torsions GTK4 修复预发布版。
基于官方 `0c588c81865cb6028c7ef33b161a35b33fd1b862`，包含本地已测试的完整修复。

- 恢复按钮、atom picking、两个 torsion slider、Accept/Cancel。
- 恢复编辑时实时 Rama 两点反馈，复用原有角度计算、分类和颜色逻辑。
- 修复 Accept 路径中 Python post-manipulation hook 的 GIL 崩溃。
- 独立打包 Python、GTK 和所需动态库，支持 App 改名/移动。

下载 ZIP 后得到 **Coot-1.3.3-backbone-torsion-re.app**。
仅支持 **Apple Silicon / macOS 26+**。这是 ad-hoc 签名包，未做 Apple
Developer ID 签名或公证，系统可能要求用户明确批准打开。请保留正式安装。
附带 Coot 标准字典子集；未包含完整 CCP4、Refmac 或 Phenix。

验证通过：

- 417 个 Mach-O 文件依赖审计；无指向开发目录、Homebrew 或其他 App 的加载依赖。
- 改名并搬到含空格路径后启动；隔离环境中 Python、GTK、NumPy、RDKit、Coot 模块来自包内。
- 实际 GTK button/click-controller 信号进入编辑对话框，Cancel 保持原坐标。
- 两个 slider 连续更新原有两个 phi/psi 点，跨区域分类变化，GPU framebuffer 可见反馈。
- 三轮 Cancel/Accept/Cancel，提交和撤销坐标验证通过，无残留活动状态。
- Real Space Refine 原有 HUD 数据源恢复；bundle 签名校验通过。

未完成：物理鼠标端到端验收、Rotamer/Edit Chi Angles 完整交互回归及全套 Coot
测试。因此标为 **Pre-release**，不建议直接替换正式安装。Refinement 仍可见已有的
macOS OpenGL texture warning。

这不是 fork 当前 main 的直接构建：fork 修复分支使用较新的 upstream 基线，且缺少
本地 GIL 修复。本次使用独立 `release/1.3.3-backbone-torsion-re` 分支和对应 tag，
保留准确的 1.3.3 基线。构建、打包和回归脚本见源码 `release/`。
