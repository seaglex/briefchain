## Brief front-end layout 说明

### layout

左侧边栏（只有普通用户有，临时用户没有）工作导航
- 项目名 "BriefChain"，不要icon
- "+ 创建 Brief"，显著button
- Briefs 列表区
  - "我创建的", created_by = myself
  - "分配给我", assigned_by = myself
  - "待处理", assigned_by = myself and upstream_state = "in_process" and downstream_state != "submitted"
- "Chains"
- "工作看板"
- "设置"

主要工作区
- head 
  - 左边：工作区名字
  - 右边：用户区（登录状态，或者临时用户注册/登录） 
- 工作页面（与具体工作相关）
  - Brief列表
  - 详情页
  - 其他

详情页
- header 信息和操作（如果铺得开就一行，铺不开就三行）
  - 信息区
    - title（最多显示10个字符）
      - 如果有 created_by = myself and unsent_version is not null，增加链接指向这个版本
    - priority
    - 如果未关联，显示: "upstream_state (version.status)"
    - 如果已关联，显示："upstream_state / downstream_state"
  - 如果打开draft版本
    - created_by = myself
      - (draft) -> 显示选项 edit(修改) / review(审核)
      - (reviewed, assigned_to is null) -> 显示选项 edit(修改) / assign(分配用户）
      - (reviewed, assigned_to is not null) -> 显示选项 edit(修改) / update(更新）
    - created_by != myself
      - 没有操作能力
  - downstream 操作区（如果assigned = myself）
    - sent -> 显示选项 accept(接受) / reject(拒绝)
    - in_process / suspended -> 显示选项 opened(待处理) / delegated(已安排) / blocked(遇阻) / submit(提交结果)，去掉当前 downstream_state 状态的选项
    - canceled / done -> 不显示选项
  - upstream 操作区（如果created_by = myself）
    - editing（非draft，version状态应该是sent） -> 显示选项 edit(修改) assign(分配用户)
    - sent -> 显示选项 edit(修改) / cancel(取消) 
    - in_process / 其他 -> 显示选项 edit(修改) / suspend(暂停) / cancel(取消)
    - suspected / 其他 -> 显示选项 edit(修改) / resume(恢复) / cancel(取消)
    - in_process / submitted -> approve(确认完成) / reject_submit(拒绝结果) 
    - suspected / submitted -> approve(确认完成) / reject_submit(拒绝结果)
    - cancelled / done -> 不显示选项
- contents