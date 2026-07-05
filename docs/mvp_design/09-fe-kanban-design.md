## 新入口
- 在 task 下，可以 create sub-task
- 在 assign 给自己的 brief 下，可以 create 子 brief / task
- 在 task / sub-task / bug 下，都可以 comment

## layout
左侧边栏增加并分为一组
- 创建 task
- 个人 kanban

内容区

## 重要单个页面
Task 详情页
- 所有关键信息、状态可以修改，创建者可以删除
- 可以选择弹窗方式或者弹层方式
- 查看详情时用普通页面方式

个人 kanban - 不存在
- 如果看板不存在：创建默认template，并打开

个人 kanban - 存在
- 右上角有配置 kanban button，点击进入配置页
- 分列展示
  - 列 head 显示 `task数` `新建` button，head 颜色取决与 column 配置
  - 属于这一列的 task cards
  - 如果 column is_hidden 为 true，折叠，列宽变为常规20%
- Task Card
  - title
  - 优先级
  - assignee_name
  - 完成时间（如果超时卡片 highlight ）
  - 查看详情（打开 Task 详情页）
- 折叠中的task card
  - 仅显示优先级
  - 如果超时卡片变标红

kanban 配置页
- 选择模板（默认用 default 模板），私人的模板用`private`表示
- 设置 泳道、done显示多少天以内
- 各列 list
  - 修改列名、颜色（自动变成 simple 模式）
- 如果 columns 被改变了，增加选项 [] 是否保存为公开模板，选中后增加 template_name 输入
- 下方有 `保存`按键
